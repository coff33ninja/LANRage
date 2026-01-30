"""Broadcast emulation - Make LAN games work over the internet"""

import asyncio
import logging
import socket
import struct
from collections.abc import Callable
from dataclasses import dataclass

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


class BroadcastEmulator:
    """
    Emulates LAN broadcast for games

    Many LAN games use UDP broadcast for discovery:
    - Minecraft: UDP broadcast on port 4445
    - Terraria: UDP broadcast on port 7777
    - Age of Empires: IPX broadcast

    This captures broadcasts and re-emits them to party members.
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
        """Handle a received broadcast packet"""
        source_ip, source_port = addr

        # Create packet
        packet = BroadcastPacket(
            data=data,
            source_ip=source_ip,
            source_port=source_port,
            dest_port=port,
            protocol="udp",
        )

        # Forward to active peers only
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
