#!/usr/bin/env python3
"""
LANrage Relay Server
Stateless packet forwarder for NAT traversal
"""

import asyncio
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.settings import get_settings_db


@dataclass
class RelayClient:
    """A client connected to the relay"""

    public_key: str
    address: tuple  # (ip, port)
    last_seen: datetime
    bytes_relayed: int = 0


class RelayServer:
    """
    Stateless WireGuard relay server

    Forwards encrypted packets between peers who can't connect directly.
    Never decrypts traffic - just forwards UDP packets.
    """

    def __init__(self, config: Config):
        self.config = config
        self.clients: dict[str, RelayClient] = {}
        self.blocked_ips: set[str] = set()  # Track blocked/rate-limited IPs
        self.running = False

        # Stats
        self.total_packets = 0
        self.total_bytes = 0

    async def start(self):
        """Start relay server"""
        self.running = True

        print("🔥 LANrage Relay Server")
        print("=" * 60)
        print(f"Listening on: 0.0.0.0:{self.config.relay_port}")
        print(f"Public IP: {self.config.relay_public_ip or 'auto-detect'}")
        print("=" * 60)

        # Start UDP listener
        loop = asyncio.get_event_loop()

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: RelayProtocol(self), local_addr=("0.0.0.0", self.config.relay_port)
        )

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

        # Start stats task
        asyncio.create_task(self._stats_task())

        print("✓ Relay server started")
        print("\nWaiting for connections...")

        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        finally:
            transport.close()

    async def stop(self):
        """Stop relay server"""
        self.running = False

    def handle_packet(self, data: bytes, addr: tuple):
        """Handle incoming packet"""
        # Check if IP is blocked
        if addr[0] in self.blocked_ips:
            return  # Silently drop packets from blocked IPs

        # WireGuard packets start with message type
        # We don't decrypt, just forward

        # Extract public key from WireGuard handshake (if present)
        public_key = self._extract_public_key(data)

        # Use public key if available, otherwise use address as identifier
        client_id = public_key if public_key else f"{addr[0]}:{addr[1]}"

        # Update or create client
        if client_id not in self.clients:
            self.clients[client_id] = RelayClient(
                public_key=public_key if public_key else client_id,
                address=addr,
                last_seen=datetime.now(),
            )
        else:
            self.clients[client_id].last_seen = datetime.now()
            # Update address in case it changed (NAT rebinding)
            self.clients[client_id].address = addr

        # Forward to all other clients
        forwarded = 0
        for other_id, client in self.clients.items():
            if other_id != client_id:
                try:
                    # Forward packet
                    # In production, this would use the transport
                    # For now, we just track stats
                    client.bytes_relayed += len(data)
                    forwarded += 1
                except OSError as e:
                    # Log forwarding failures (network errors, etc.)
                    print(
                        f"Warning: Failed to forward packet to client {other_id}: {e}",
                        file=sys.stderr,
                    )
                except Exception as e:
                    # Catch any other unexpected errors
                    print(
                        f"Warning: Unexpected error forwarding packet: {e}",
                        file=sys.stderr,
                    )

        # Update stats
        self.total_packets += 1
        self.total_bytes += len(data)

    def _extract_public_key(self, data: bytes) -> str | None:
        """Extract public key from WireGuard packet

        WireGuard packet format:
        - Handshake Initiation (type 1): Contains sender's public key at offset 8
        - Handshake Response (type 2): Contains sender's public key at offset 8
        - Data (type 4): No public key (encrypted)

        Args:
            data: Raw packet data

        Returns:
            Base64-encoded public key if found, None otherwise
        """
        try:
            # WireGuard packets must be at least 4 bytes
            if len(data) < 4:
                return None

            # First 4 bytes: message type (little-endian)
            import struct

            msg_type = struct.unpack("<I", data[:4])[0]

            # Handshake Initiation (type 1) or Response (type 2)
            if msg_type in (1, 2):
                # Public key is 32 bytes starting at offset 8
                if len(data) >= 40:  # 4 (type) + 4 (reserved) + 32 (public key)
                    import base64

                    public_key_bytes = data[8:40]
                    return base64.b64encode(public_key_bytes).decode("ascii")

            # Data packets (type 4) don't contain public key
            return None

        except struct.error as e:
            # Log parsing errors for debugging
            print(
                f"Debug: Failed to parse WireGuard packet structure: {e}",
                file=sys.stderr,
            )
            return None
        except Exception as e:
            # If extraction fails, return None but log unexpected errors
            print(
                f"Debug: Unexpected error extracting public key: {e}", file=sys.stderr
            )
            return None

    async def _cleanup_task(self):
        """Cleanup stale clients"""
        while self.running:
            await asyncio.sleep(60)  # Every minute

            now = datetime.now()
            timeout = timedelta(minutes=5)

            # Remove stale clients
            stale = [
                client_id
                for client_id, client in self.clients.items()
                if now - client.last_seen > timeout
            ]

            for client_id in stale:
                del self.clients[client_id]

            if stale:
                print(f"🧹 Cleaned up {len(stale)} stale clients")

    async def _stats_task(self):
        """Print stats periodically"""
        while self.running:
            await asyncio.sleep(30)  # Every 30 seconds

            if self.clients:
                print("\n📊 Stats:")
                print(f"   Active clients: {len(self.clients)}")
                print(f"   Total packets: {self.total_packets}")
                print(f"   Total bytes: {self.total_bytes / 1024 / 1024:.2f} MB")
                if self.blocked_ips:
                    print(f"   Blocked IPs: {len(self.blocked_ips)}")


class RelayProtocol(asyncio.DatagramProtocol):
    """Protocol for relay server"""

    def __init__(self, server: RelayServer):
        self.server = server
        self.transport = None

    def connection_made(self, transport):
        """Connection established"""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple):
        """Handle received datagram"""
        self.server.handle_packet(data, addr)

        # Forward to all other clients
        for client_id, client in self.server.clients.items():
            if client.address != addr:
                try:
                    self.transport.sendto(data, client.address)
                except OSError as e:
                    # Log send failures (network unreachable, etc.)
                    print(
                        f"Warning: Failed to send to client {client_id}: {e}",
                        file=sys.stderr,
                    )
                except Exception as e:
                    # Catch any other unexpected errors
                    print(
                        f"Warning: Unexpected error sending to client: {e}",
                        file=sys.stderr,
                    )


async def main():
    """Main entry point"""
    # Load settings from database
    db = await get_settings_db()
    settings = await db.get_all_settings()

    # Create config from settings
    config = Config(
        mode="relay",
        relay_port=settings.get("relay_port", 51820),
        relay_public_ip=settings.get("relay_public_ip"),
        api_host=settings.get("api_host", "127.0.0.1"),
        api_port=settings.get("api_port", 8666),
    )

    print("📋 Loaded settings from database")
    print(f"   Relay port: {config.relay_port}")
    print(f"   Public IP: {config.relay_public_ip or 'auto-detect'}")
    print(f"   Max clients: {settings.get('max_clients', 100)}")
    print()

    # Create relay server
    relay = RelayServer(config)

    try:
        await relay.start()
    except KeyboardInterrupt:
        print("\n\n👋 Relay server shutting down...")
        await relay.stop()
    except Exception as e:
        print(f"\n❌ Relay server error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
