"""NAT traversal - STUN/TURN and UDP hole punching"""

import asyncio
import logging
import secrets
import socket
import struct
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum

from .config import Config
from .exceptions import NATError, STUNError

logger = logging.getLogger(__name__)


class NATType(Enum):
    """Types of NAT"""

    UNKNOWN = "unknown"
    OPEN = "open"  # No NAT (direct internet)
    FULL_CONE = "full_cone"  # Easy to traverse
    RESTRICTED_CONE = "restricted_cone"  # Moderate difficulty
    PORT_RESTRICTED_CONE = "port_restricted_cone"  # Harder
    SYMMETRIC = "symmetric"  # Very difficult, needs relay


@dataclass
class STUNResponse:
    """STUN server response"""

    public_ip: str
    public_port: int
    nat_type: NATType
    local_ip: str
    local_port: int


class NATTraversal:
    """Handles NAT detection and traversal"""

    # Public STUN servers
    STUN_SERVERS = [
        ("stun.l.google.com", 19302),
        ("stun1.l.google.com", 19302),
        ("stun2.l.google.com", 19302),
        ("stun3.l.google.com", 19302),
        ("stun4.l.google.com", 19302),
    ]

    def __init__(self, config: Config, control_client=None):
        self.config = config
        self.control_client = (
            control_client  # Optional control plane client for relay discovery
        )
        self.public_ip: str | None = None
        self.public_port: int | None = None
        self.nat_type: NATType = NATType.UNKNOWN
        self.local_ip: str | None = None
        self.local_port: int | None = None

    async def detect_nat(self) -> STUNResponse:
        """Detect NAT type using STUN"""
        # Try multiple STUN servers
        last_error = None

        for stun_server in self.STUN_SERVERS:
            try:
                response = await self._stun_request(stun_server)
                if response:
                    self.public_ip = response.public_ip
                    self.public_port = response.public_port
                    self.nat_type = response.nat_type
                    self.local_ip = response.local_ip
                    self.local_port = response.local_port
                    logger.info(
                        f"NAT detected via {stun_server[0]}: {response.nat_type.value} "
                        f"(Public: {response.public_ip}:{response.public_port})"
                    )
                    return response
            except STUNError as e:
                logger.warning(
                    f"STUN server {stun_server[0]} returned invalid response: {e}"
                )
                last_error = e
                continue
            except TimeoutError:
                logger.warning(f"STUN server {stun_server[0]} timed out")
                continue
            except OSError as e:
                logger.warning(
                    f"Network error contacting STUN server {stun_server[0]}: {e}"
                )
                last_error = e
                continue

        error_msg = "Failed to detect NAT type (all STUN servers failed)"
        if last_error:
            error_msg += f". Last error: {type(last_error).__name__}: {last_error}"
        logger.error(error_msg)
        raise NATError(error_msg)

    async def _stun_request(self, stun_server: tuple[str, int]) -> STUNResponse | None:
        """Send STUN request to server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        try:
            # Bind to random port
            sock.bind(("0.0.0.0", 0))
            local_ip, local_port = sock.getsockname()

            # Build STUN Binding Request
            # RFC 5389: STUN Message Structure
            message_type = 0x0001  # Binding Request
            message_length = 0
            magic_cookie = 0x2112A442
            transaction_id = secrets.token_bytes(12)

            # Pack STUN header
            stun_request = struct.pack(
                "!HHI12s", message_type, message_length, magic_cookie, transaction_id
            )

            # Send request
            sock.sendto(stun_request, stun_server)

            # Receive response
            data, addr = sock.recvfrom(1024)

            # Parse STUN response
            if len(data) < 20:
                raise STUNError("Response too short")

            # Parse header
            msg_type, msg_len, cookie, trans_id = struct.unpack("!HHI12s", data[:20])

            # Verify this is a Binding Response
            if msg_type != 0x0101:  # Binding Response
                raise STUNError(f"Invalid message type: {hex(msg_type)}")

            # Verify transaction ID matches
            if trans_id != transaction_id:
                raise STUNError("Transaction ID mismatch")

            # Parse attributes
            public_ip, public_port = self._parse_stun_attributes(data[20:])

            if not public_ip or not public_port:
                raise STUNError("No mapped address in response")

            # Determine NAT type (simplified)
            nat_type = self._determine_nat_type(
                local_ip, local_port, public_ip, public_port
            )

            return STUNResponse(
                public_ip=public_ip,
                public_port=public_port,
                nat_type=nat_type,
                local_ip=local_ip,
                local_port=local_port,
            )

        except TimeoutError:
            return None
        except STUNError:
            raise
        except OSError as e:
            raise OSError(f"Network error in STUN request: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in STUN request: {type(e).__name__}: {e}")
            raise STUNError(f"Unexpected error: {type(e).__name__}: {e}") from e
        finally:
            sock.close()

    def _parse_stun_attributes(self, data: bytes) -> tuple[str | None, int | None]:
        """Parse STUN attributes to extract mapped address"""
        offset = 0
        public_ip = None
        public_port = None

        while offset < len(data):
            if offset + 4 > len(data):
                break

            # Parse attribute header
            attr_type, attr_len = struct.unpack("!HH", data[offset : offset + 4])
            offset += 4

            if offset + attr_len > len(data):
                break

            # MAPPED-ADDRESS (0x0001) or XOR-MAPPED-ADDRESS (0x0020)
            if attr_type in (0x0001, 0x0020) and attr_len >= 8:
                # Parse address
                family = data[offset + 1]
                port = struct.unpack("!H", data[offset + 2 : offset + 4])[0]

                if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
                    # XOR with magic cookie
                    port ^= 0x2112

                if family == 0x01:  # IPv4
                    ip_bytes = data[offset + 4 : offset + 8]

                    if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
                        # XOR with magic cookie
                        magic = struct.pack("!I", 0x2112A442)
                        ip_bytes = bytes(
                            a ^ b for a, b in zip(ip_bytes, magic, strict=False)
                        )

                    public_ip = ".".join(str(b) for b in ip_bytes)
                    public_port = port

            # Move to next attribute (with padding)
            offset += attr_len
            # Attributes are padded to 4-byte boundary
            offset = (offset + 3) & ~3

        return public_ip, public_port

    def _determine_nat_type(
        self, local_ip: str, local_port: int, public_ip: str, public_port: int
    ) -> NATType:
        """Determine NAT type (simplified detection)"""
        # If public IP matches local IP, no NAT
        if public_ip == local_ip:
            return NATType.OPEN

        # If ports match, likely full cone NAT
        if public_port == local_port:
            return NATType.FULL_CONE

        # Otherwise, assume port-restricted cone
        # (Full detection requires multiple STUN requests)
        return NATType.PORT_RESTRICTED_CONE

    async def attempt_hole_punch(
        self, peer_public_ip: str, peer_public_port: int, local_port: int = 51820
    ) -> bool:
        """Attempt UDP hole punching with peer"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)

        try:
            # Bind to WireGuard port
            sock.bind(("0.0.0.0", local_port))

            # Send multiple packets to punch hole
            punch_message = b"LANRAGE_PUNCH"

            for _ in range(5):
                sock.sendto(punch_message, (peer_public_ip, peer_public_port))
                await asyncio.sleep(0.1)

            # Try to receive response
            try:
                data, addr = sock.recvfrom(1024)
                if data == b"LANRAGE_PUNCH_ACK":
                    return True
            except TimeoutError:
                pass

            return False

        except OSError as e:
            # Log socket errors (network unreachable, permission denied, etc.)
            print(f"Warning: Hole punching failed: {e}", file=sys.stderr)
            return False
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Warning: Unexpected error in hole punching: {e}", file=sys.stderr)
            return False
        finally:
            sock.close()

    def can_direct_connect(self, peer_nat_type: NATType) -> bool:
        """Check if direct P2P connection is possible"""
        # Open NAT can connect to anything
        if self.nat_type == NATType.OPEN or peer_nat_type == NATType.OPEN:
            return True

        # Full cone NATs can connect to each other
        if self.nat_type == NATType.FULL_CONE and peer_nat_type == NATType.FULL_CONE:
            return True

        # Restricted cone can work with hole punching
        if self.nat_type in (
            NATType.FULL_CONE,
            NATType.RESTRICTED_CONE,
            NATType.PORT_RESTRICTED_CONE,
        ) and peer_nat_type in (
            NATType.FULL_CONE,
            NATType.RESTRICTED_CONE,
            NATType.PORT_RESTRICTED_CONE,
        ):
            return True

        # Symmetric NAT needs relay
        if self.nat_type == NATType.SYMMETRIC or peer_nat_type == NATType.SYMMETRIC:
            return False

        return False

    def get_connection_strategy(self, peer_nat_type: NATType) -> str:
        """Determine best connection strategy"""
        if self.can_direct_connect(peer_nat_type):
            return "direct"
        return "relay"


class ConnectionCoordinator:
    """Coordinates peer connections with NAT traversal"""

    def __init__(self, config: Config, nat: NATTraversal):
        self.config = config
        self.nat = nat

    async def coordinate_connection(
        self, peer_public_key: str, peer_nat_info: dict
    ) -> dict:
        """Coordinate connection with peer"""
        peer_nat_type = NATType(peer_nat_info.get("nat_type", "unknown"))

        # Determine strategy
        strategy = self.nat.get_connection_strategy(peer_nat_type)

        if strategy == "direct":
            # Attempt direct connection with hole punching
            success = await self._attempt_direct_connection(peer_nat_info)

            if success:
                return {
                    "strategy": "direct",
                    "endpoint": f"{peer_nat_info['public_ip']}:{peer_nat_info['public_port']}",
                    "success": True,
                }
            # Fall back to relay
            strategy = "relay"

        if strategy == "relay":
            # Use relay server
            relay_endpoint = await self._get_relay_endpoint()

            return {"strategy": "relay", "endpoint": relay_endpoint, "success": True}

        return {
            "strategy": "failed",
            "success": False,
            "error": "No connection strategy available",
        }

    async def _attempt_direct_connection(self, peer_nat_info: dict) -> bool:
        """Attempt direct P2P connection"""
        peer_ip = peer_nat_info["public_ip"]
        peer_port = peer_nat_info["public_port"]

        # Attempt hole punching
        return await self.nat.attempt_hole_punch(peer_ip, peer_port)

    async def _get_relay_endpoint(self) -> str:
        """Get relay server endpoint with discovery and latency measurement"""
        # Try to discover relays from control plane
        relays = await self._discover_relays()

        if not relays:
            # Fall back to configured relay or default
            if self.config.relay_public_ip:
                return f"{self.config.relay_public_ip}:{self.config.relay_port}"
            return "relay.lanrage.io:51820"

        # Measure latency to each relay and select the best one
        best_relay = await self._select_best_relay(relays)

        if best_relay:
            return f"{best_relay['ip']}:{best_relay['port']}"

        # Fall back to first relay if latency measurement fails
        return f"{relays[0]['ip']}:{relays[0]['port']}"

    async def _discover_relays(self) -> list:
        """Discover available relay servers from control plane"""
        relays = []

        # Try to get relays from control plane if available
        if self.control_client:
            try:
                # Query control plane for relay list
                control_relays = await self.control_client.list_relays()

                # Convert control plane format to internal format
                for relay in control_relays:
                    relays.append(
                        {
                            "ip": relay["public_ip"],
                            "port": relay["port"],
                            "region": relay.get("region", "unknown"),
                            "relay_id": relay.get("relay_id", "unknown"),
                        }
                    )

                if relays:
                    print(
                        f"✓ Discovered {len(relays)} relay servers from control plane"
                    )
                    return relays

            except Exception as e:
                error_msg = str(e)
                print(f"⚠ Failed to discover relays from control plane: {error_msg}")
                # Fall through to use configured/default relays

        # Fall back to configured relay if available
        if self.config.relay_public_ip:
            relays.append(
                {
                    "ip": self.config.relay_public_ip,
                    "port": self.config.relay_port,
                    "region": "configured",
                    "relay_id": "configured",
                }
            )
            print("✓ Using configured relay server")

        # Add default relay as final fallback
        if not relays:
            relays.append(
                {
                    "ip": "relay.lanrage.io",
                    "port": 51820,
                    "region": "default",
                    "relay_id": "default",
                }
            )
            print("ℹ Using default relay server (relay.lanrage.io)")

        return relays

    async def _select_best_relay(self, relays: list) -> dict | None:
        """Select relay with lowest latency"""
        best_relay = None
        best_latency = float("inf")

        for relay in relays:
            try:
                # Measure latency to relay
                latency = await self._measure_relay_latency(relay["ip"])

                if latency is not None and latency < best_latency:
                    best_latency = latency
                    best_relay = relay
            except (TimeoutError, OSError) as e:
                logger.warning(f"Failed to measure latency to relay {relay['ip']}: {e}")
                continue

        if best_relay:
            logger.info(
                f"Selected relay {best_relay['ip']} with {best_latency:.1f}ms latency"
            )

        return best_relay

    async def _measure_relay_latency(self, relay_ip: str) -> float | None:
        """Measure latency to relay server"""
        try:
            # Use ICMP ping to measure latency
            import platform

            is_windows = platform.system() == "Windows"

            if is_windows:
                cmd = ["ping", "-n", "1", "-w", "1000", relay_ip]
            else:
                cmd = ["ping", "-c", "1", "-W", "1", relay_ip]

            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode("utf-8", errors="ignore")
                import re

                if is_windows:
                    match = re.search(r"time[<=](\d+)ms", output)
                else:
                    match = re.search(r"time=(\d+\.?\d*)", output)

                if match:
                    return float(match.group(1))

            return None
        except subprocess.CalledProcessError as e:
            # Log ping command failures
            logger.debug(f"Ping to relay {relay_ip} failed: {e}")
            return None
        except ValueError as e:
            # Log parsing errors
            logger.debug(f"Failed to parse ping latency for {relay_ip}: {e}")
            return None
        except (TimeoutError, OSError) as e:
            # Network errors or timeouts
            logger.debug(f"Network error measuring latency to {relay_ip}: {e}")
            return None
