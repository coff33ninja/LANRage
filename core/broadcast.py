"""Broadcast emulation - Make LAN games work over the internet"""

import asyncio
import hashlib
import logging
import socket
import struct
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from .config import Config
from .exceptions import SocketError

logger = logging.getLogger(__name__)


@dataclass
class BroadcastPacket:
    """A captured broadcast packet"""

    data: bytes
    source_ip: str
    source_port: int
    dest_port: int
    protocol: str  # "udp" or "tcp"


@dataclass
class BroadcastDeduplicator:
    """Prevents duplicate broadcast forwarding using hash tracking

    Maintains a time-windowed set of packet hashes to prevent:
    - Same packet forwarded multiple times (deduplication)
    - Network loops from exponential packet duplication
    - Wasteful bandwidth usage

    Uses SHA256 hash of packet contents with 5-second expiry window.
    """

    window_seconds: float = 5.0
    cleanup_interval: float = 2.0
    enabled: bool = True

    # Tracking
    _packet_hashes: dict[str, float] = field(default_factory=dict)
    _cleanup_task: asyncio.Task | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # Metrics
    total_packets: int = 0
    forwarded_packets: int = 0
    deduplicated_packets: int = 0

    async def should_forward(
        self, packet: BroadcastPacket, source_peer: str | None = None
    ) -> bool:
        """Check if packet should be forwarded (not a duplicate)

        Args:
            packet: The broadcast packet to check
            source_peer: Optional peer ID that sourced this packet (to prevent back-forwarding)

        Returns:
            True if packet should be forwarded, False if duplicate
        """
        if not self.enabled:
            return True

        async with self._lock:
            self.total_packets += 1

            # Don't forward back to the source peer
            if source_peer and packet.source_ip == source_peer:
                self.deduplicated_packets += 1
                return False

            # Hash the packet contents
            packet_hash = self._hash_packet(packet)

            # Check if we've seen this packet recently
            if packet_hash in self._packet_hashes:
                logger.debug(
                    f"Dropping duplicate broadcast packet {packet_hash[:8]}... "
                    f"from {packet.source_ip}:{packet.source_port} on port {packet.dest_port}"
                )
                self.deduplicated_packets += 1
                return False

            # New packet - record it and schedule cleanup
            self._packet_hashes[packet_hash] = time.time()
            self.forwarded_packets += 1

            # Start cleanup task if needed
            if not self._cleanup_task or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_hashes())

            return True

    def _hash_packet(self, packet: BroadcastPacket) -> str:
        """Generate hash of packet for deduplication

        Uses SHA256 of packet data, source, and destination port.
        This uniquely identifies a specific broadcast packet.

        Args:
            packet: Broadcast packet to hash

        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()
        hasher.update(packet.data)
        hasher.update(packet.source_ip.encode())
        hasher.update(str(packet.dest_port).encode())
        return hasher.hexdigest()

    async def _cleanup_expired_hashes(self) -> None:
        """Remove packet hashes older than the window size

        Runs periodically to clean up old hashes and maintain bounded memory.
        """
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                async with self._lock:
                    now = time.time()
                    expired_hashes = [
                        h
                        for h, ts in self._packet_hashes.items()
                        if now - ts > self.window_seconds
                    ]

                    for h in expired_hashes:
                        del self._packet_hashes[h]

                    if expired_hashes:
                        logger.debug(
                            f"Cleaned up {len(expired_hashes)} expired packet hashes"
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast deduplication cleanup: {e}")

    async def flush(self) -> None:
        """Flush pending cleanup tasks"""
        import contextlib

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

    def get_metrics(self) -> dict:
        """Get deduplication metrics

        Returns:
            Dictionary with deduplication statistics
        """
        if self.total_packets == 0:
            return {
                "total_packets": 0,
                "forwarded_packets": 0,
                "deduplicated_packets": 0,
                "deduplicate_rate": 0.0,
                "tracked_hashes": len(self._packet_hashes),
            }

        return {
            "total_packets": self.total_packets,
            "forwarded_packets": self.forwarded_packets,
            "deduplicated_packets": self.deduplicated_packets,
            "deduplicate_rate": (self.deduplicated_packets / self.total_packets * 100),
            "tracked_hashes": len(self._packet_hashes),
        }

    def disable(self) -> None:
        """Disable deduplication (for testing/debugging)"""
        self.enabled = False

    def enable(self) -> None:
        """Enable deduplication"""
        self.enabled = True


class BroadcastEmulator:
    """
    Emulates LAN broadcast for games

    Many LAN games use UDP broadcast for discovery:
    - Minecraft: UDP broadcast on port 4445
    - Terraria: UDP broadcast on port 7777
    - Age of Empires: IPX broadcast

    This captures broadcasts and re-emits them to party members,
    with automatic deduplication to prevent network loops.
    """

    def __init__(self, config: Config):
        self.config = config
        self.running = False

        # Broadcast listeners
        self.listeners: dict[int, asyncio.DatagramProtocol] = {}

        # Track active peer IDs for filtering
        self.active_peers: set[str] = set()

        # Callback for forwarding packets to peers
        self.forward_callback: Callable[[BroadcastPacket], None] | None = None

        # Deduplication
        self.deduplicator = BroadcastDeduplicator()

        # Common game ports to monitor
        self.monitored_ports = [
            4445,  # Minecraft
            7777,  # Terraria
            27015,  # Source games
            27016,  # Source games
            6112,  # Warcraft III
            6073,  # Age of Empires II
        ]

    async def start(self):
        """Start broadcast emulation"""
        self.running = True

        # Start listeners for common ports
        for port in self.monitored_ports:
            try:
                await self._start_listener(port)
            except SocketError as e:
                logger.warning(f"Could not start listener on port {port}: {e}")
            except Exception as e:
                logger.error(
                    f"Unexpected error starting listener on port {port}: {type(e).__name__}: {e}"
                )

    async def stop(self):
        """Stop broadcast emulation"""
        self.running = False

        # Flush deduplicator
        await self.deduplicator.flush()

        # Stop all listeners
        for port, transport in list(self.listeners.items()):
            try:
                transport.close()
            except Exception as e:
                logger.warning(
                    f"Error closing transport for port {port}: {type(e).__name__}: {e}"
                )
            finally:
                del self.listeners[port]

        logger.info("Broadcast emulation stopped")

    async def _start_listener(self, port: int):
        """Start listening on a port for broadcasts"""
        loop = asyncio.get_event_loop()

        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)

        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            try:
                sock.bind(("0.0.0.0", port))
            except OSError as e:
                raise SocketError(f"Failed to bind to port {port}: {e}") from e

            # Create protocol
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: BroadcastProtocol(self, port), sock=sock
            )

            self.listeners[port] = transport
            logger.info(f"Broadcast listener started on port {port}")

        except Exception as e:
            sock.close()
            if isinstance(e, SocketError):
                raise
            raise SocketError(f"Failed to start listener on port {port}: {e}") from e

    def set_forward_callback(self, callback: Callable[[BroadcastPacket], None]):
        """Set callback for forwarding packets to peers"""
        self.forward_callback = callback

    def add_peer(self, peer_id: str):
        """Add a peer to active peers set"""
        self.active_peers.add(peer_id)

    def remove_peer(self, peer_id: str):
        """Remove a peer from active peers set"""
        self.active_peers.discard(peer_id)

    def handle_broadcast(self, data: bytes, addr: tuple, port: int):
        """Handle a received broadcast packet

        Deduplicates packets before forwarding to prevent network loops
        and wasted bandwidth.

        Args:
            data: Packet data bytes
            addr: (source_ip, source_port) tuple
            port: Destination port
        """
        source_ip, source_port = addr

        # Create packet
        packet = BroadcastPacket(
            data=data,
            source_ip=source_ip,
            source_port=source_port,
            dest_port=port,
            protocol="udp",
        )

        # Check for duplicates (async operation, but we can't await in sync context)
        # Instead, use synchronous check via asyncio.run_coroutine_threadsafe
        # For now, we'll queue the check asynchronously

        # Should we forward this packet?
        # We need to run the async check, so we'll do it in the forwarding path
        async def check_and_forward():
            if (await self.deduplicator.should_forward(packet)) and (
                self.forward_callback and len(self.active_peers) > 0
            ):
                self.forward_callback(packet)

        # Schedule the async check
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(check_and_forward())
            else:
                loop.run_until_complete(check_and_forward())
        except RuntimeError:
            # No event loop, just forward without dedup (fallback)
            if self.forward_callback and len(self.active_peers) > 0:
                self.forward_callback(packet)

    async def inject_broadcast(
        self, packet: BroadcastPacket, target_ip: str = "255.255.255.255"
    ):
        """Inject a broadcast packet (from remote peer)"""
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            # Send to broadcast address
            sock.sendto(packet.data, (target_ip, packet.dest_port))
        except OSError as e:
            # Log send failures (network unreachable, permission denied, etc.)
            logger.warning(
                f"Failed to send broadcast to {target_ip}:{packet.dest_port}: {e}"
            )
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error sending broadcast: {type(e).__name__}: {e}")
        finally:
            sock.close()


class BroadcastProtocol(asyncio.DatagramProtocol):
    """Protocol for handling broadcast packets"""

    def __init__(self, emulator: BroadcastEmulator, port: int):
        self.emulator = emulator
        self.port = port

    def datagram_received(self, data: bytes, addr: tuple):
        """Handle received datagram"""
        # Check if it's a broadcast
        if self._is_broadcast(addr[0]):
            self.emulator.handle_broadcast(data, addr, self.port)

    def _is_broadcast(self, ip: str) -> bool:
        """Check if IP is a broadcast address"""
        return ip.endswith(".255") or ip == "255.255.255.255"


class MulticastEmulator:
    """
    Emulates multicast for games

    Some games use multicast for discovery:
    - mDNS (224.0.0.251)
    - SSDP (239.255.255.250)
    """

    def __init__(self, config: Config):
        self.config = config
        self.running = False

        # Multicast groups
        self.groups = [
            ("224.0.0.251", 5353),  # mDNS
            ("239.255.255.250", 1900),  # SSDP
        ]

        # Listeners
        self.listeners: dict[tuple, asyncio.DatagramProtocol] = {}

        # Forward callback
        self.forward_callback: Callable[[BroadcastPacket], None] | None = None

    async def start(self):
        """Start multicast emulation"""
        self.running = True

        for group_ip, port in self.groups:
            try:
                await self._start_listener(group_ip, port)
            except OSError as e:
                # Log listener start failures (port in use, permission denied, etc.)
                logger.warning(
                    f"Failed to start multicast listener on {group_ip}:{port}: {e}"
                )
            except Exception as e:
                # Catch any other unexpected errors
                logger.error(
                    f"Unexpected error starting multicast listener: {type(e).__name__}: {e}"
                )

    async def stop(self):
        """Stop multicast emulation"""
        self.running = False

        for key, transport in list(self.listeners.items()):
            transport.close()
            del self.listeners[key]

    async def _start_listener(self, group_ip: str, port: int):
        """Start listening on a multicast group"""
        loop = asyncio.get_event_loop()

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind to port
        sock.bind(("", port))

        # Join multicast group
        mreq = struct.pack("4sl", socket.inet_aton(group_ip), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        sock.setblocking(False)

        # Create protocol
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: MulticastProtocol(self, group_ip, port), sock=sock
        )

        self.listeners[(group_ip, port)] = transport

    def set_forward_callback(self, callback: Callable[[BroadcastPacket], None]):
        """Set callback for forwarding packets"""
        self.forward_callback = callback

    def handle_multicast(self, data: bytes, addr: tuple, group_ip: str, port: int):
        """Handle received multicast packet"""
        source_ip, source_port = addr

        packet = BroadcastPacket(
            data=data,
            source_ip=source_ip,
            source_port=source_port,
            dest_port=port,
            protocol="multicast",
        )

        if self.forward_callback:
            self.forward_callback(packet)

    async def inject_multicast(self, packet: BroadcastPacket, group_ip: str):
        """Inject a multicast packet"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.sendto(packet.data, (group_ip, packet.dest_port))
        except OSError as e:
            # Log send failures (network unreachable, permission denied, etc.)
            logger.warning(
                f"Failed to send multicast to {group_ip}:{packet.dest_port}: {e}"
            )
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error sending multicast: {type(e).__name__}: {e}")
        finally:
            sock.close()


class MulticastProtocol(asyncio.DatagramProtocol):
    """Protocol for handling multicast packets"""

    def __init__(self, emulator: MulticastEmulator, group_ip: str, port: int):
        self.emulator = emulator
        self.group_ip = group_ip
        self.port = port

    def datagram_received(self, data: bytes, addr: tuple):
        """Handle received datagram"""
        self.emulator.handle_multicast(data, addr, self.group_ip, self.port)


class BroadcastManager:
    """
    Manages broadcast and multicast emulation

    Coordinates between local emulation and remote peers.
    """

    def __init__(self, config: Config):
        self.config = config
        self.broadcast = BroadcastEmulator(config)
        self.multicast = MulticastEmulator(config)

        # Peer forwarding
        self.peer_forwarders: dict[str, Callable] = {}

    async def start(self):
        """Start broadcast management"""
        # Set up forwarding callbacks
        self.broadcast.set_forward_callback(self._forward_to_peers)
        self.multicast.set_forward_callback(self._forward_to_peers)

        # Start emulators
        await self.broadcast.start()
        await self.multicast.start()

    async def start_listener(self, port: int, protocol: str = "udp"):
        """Start a listener on a specific port for game broadcast emulation

        Args:
            port: Port number to listen on
            protocol: Protocol type ("udp" or "tcp")
        """
        if protocol == "udp":
            # Add port to monitored ports if not already there
            if port not in self.broadcast.monitored_ports:
                self.broadcast.monitored_ports.append(port)

            # Start listener for this port
            try:
                await self.broadcast._start_listener(port)
            except SocketError as e:
                logger.warning(f"Could not start listener on port {port}: {e}")
            except Exception as e:
                logger.error(
                    f"Unexpected error starting listener on port {port}: {type(e).__name__}: {e}"
                )
        elif protocol == "tcp":
            # TCP broadcast emulation not yet implemented
            logger.warning(
                f"TCP broadcast emulation not yet implemented for port {port}"
            )

    async def stop(self):
        """Stop broadcast management"""
        await self.broadcast.stop()
        await self.multicast.stop()

    def register_peer(self, peer_id: str, forwarder: Callable):
        """Register a peer for broadcast forwarding"""
        self.peer_forwarders[peer_id] = forwarder

    def unregister_peer(self, peer_id: str):
        """Unregister a peer"""
        if peer_id in self.peer_forwarders:
            del self.peer_forwarders[peer_id]

    def _forward_to_peers(self, packet: BroadcastPacket):
        """Forward packet to all peers"""
        for peer_id, forwarder in self.peer_forwarders.items():
            try:
                forwarder(packet)
            except OSError as e:
                # Peer might be disconnected or unreachable
                logger.debug(f"Failed to forward broadcast to peer {peer_id}: {e}")
            except Exception as e:
                # Catch any other unexpected errors
                logger.error(
                    f"Unexpected error forwarding to peer {peer_id}: {type(e).__name__}: {e}"
                )

    async def handle_remote_broadcast(self, packet: BroadcastPacket):
        """Handle broadcast from remote peer"""
        # Inject into local network
        if packet.protocol == "multicast":
            # Determine multicast group from port
            group_map = {
                5353: "224.0.0.251",  # mDNS
                1900: "239.255.255.250",  # SSDP
            }
            group_ip = group_map.get(packet.dest_port, "224.0.0.1")
            await self.multicast.inject_multicast(packet, group_ip)
        else:
            # Regular broadcast
            await self.broadcast.inject_broadcast(packet)
