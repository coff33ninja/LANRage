"""Control plane - Peer discovery and signaling"""

import asyncio
import json
import secrets
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from .config import Config
from .nat import NATType


@dataclass
class PeerInfo:
    """Information about a peer"""

    peer_id: str
    name: str
    public_key: str
    nat_type: str
    public_ip: str
    public_port: int
    local_ip: str
    local_port: int
    last_seen: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["last_seen"] = self.last_seen.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PeerInfo":
        """Create from dictionary"""
        data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        return cls(**data)

    def validate_nat_type(self) -> bool:
        """Validate that NAT type is valid"""
        try:
            NATType(self.nat_type)
            return True
        except ValueError:
            return False

    def get_nat_type_enum(self) -> NATType:
        """Get NAT type as enum"""
        return NATType(self.nat_type)


@dataclass
class PartyInfo:
    """Information about a party"""

    party_id: str
    name: str
    host_id: str
    created_at: datetime
    peers: Dict[str, PeerInfo]

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "party_id": self.party_id,
            "name": self.name,
            "host_id": self.host_id,
            "created_at": self.created_at.isoformat(),
            "peers": {k: v.to_dict() for k, v in self.peers.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PartyInfo":
        """Create from dictionary"""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["peers"] = {k: PeerInfo.from_dict(v) for k, v in data["peers"].items()}
        return cls(**data)

    @staticmethod
    def generate_party_id() -> str:
        """Generate a secure random party ID"""
        return secrets.token_hex(6)


class ControlPlane:
    """
    Control plane for peer discovery and signaling

    In production, this would be a centralized server.
    For now, we implement a simple local/file-based version
    that can be upgraded to client-server later.
    """

    def __init__(self, config: Config):
        self.config = config
        self.parties: Dict[str, PartyInfo] = {}
        self.my_peer_id: Optional[str] = None
        self.my_party_id: Optional[str] = None

        # Track active party IDs for quick lookup
        self.active_party_ids: Set[str] = set()

        # Persistence
        self.state_file = config.config_dir / "control_state.json"

    async def initialize(self):
        """Initialize control plane"""
        # Load persisted state
        await self._load_state()

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def register_party(
        self, party_id: str, name: str, host_peer_info: PeerInfo
    ) -> PartyInfo:
        """Register a new party"""
        party = PartyInfo(
            party_id=party_id,
            name=name,
            host_id=host_peer_info.peer_id,
            created_at=datetime.now(),
            peers={host_peer_info.peer_id: host_peer_info},
        )

        self.parties[party_id] = party
        self.active_party_ids.add(party_id)  # Track active party
        self.my_party_id = party_id
        self.my_peer_id = host_peer_info.peer_id

        await self._save_state()
        return party

    async def join_party(self, party_id: str, peer_info: PeerInfo) -> PartyInfo:
        """Join an existing party"""
        if party_id not in self.parties:
            raise ControlPlaneError(f"Party {party_id} not found")

        party = self.parties[party_id]
        party.peers[peer_info.peer_id] = peer_info

        self.my_party_id = party_id
        self.my_peer_id = peer_info.peer_id

        await self._save_state()
        return party

    async def leave_party(self, party_id: str, peer_id: str):
        """Leave a party"""
        if party_id not in self.parties:
            return

        party = self.parties[party_id]

        if peer_id in party.peers:
            del party.peers[peer_id]

        # If host left or no peers remain, delete party
        if peer_id == party.host_id or len(party.peers) == 0:
            del self.parties[party_id]
            self.active_party_ids.discard(party_id)  # Remove from active set

        if self.my_party_id == party_id:
            self.my_party_id = None
            self.my_peer_id = None

        await self._save_state()

    async def update_peer(self, party_id: str, peer_info: PeerInfo):
        """Update peer information"""
        if party_id not in self.parties:
            return

        party = self.parties[party_id]
        peer_info.last_seen = datetime.now()
        party.peers[peer_info.peer_id] = peer_info

        await self._save_state()

    async def get_party(self, party_id: str) -> Optional[PartyInfo]:
        """Get party information"""
        return self.parties.get(party_id)

    async def get_peers(self, party_id: str) -> Dict[str, PeerInfo]:
        """Get all peers in a party"""
        if party_id not in self.parties:
            return {}

        return self.parties[party_id].peers

    async def discover_peer(self, party_id: str, peer_id: str) -> Optional[PeerInfo]:
        """Discover a specific peer"""
        if party_id not in self.parties:
            return None

        return self.parties[party_id].peers.get(peer_id)

    async def signal_connection(
        self, party_id: str, from_peer_id: str, to_peer_id: str, signal_data: dict
    ):
        """
        Signal connection information between peers

        This is used for WebRTC-style signaling:
        - Exchange NAT info
        - Coordinate hole punching
        - Share relay endpoints
        """
        # In a real implementation, this would send to the peer
        # For now, we just store it for the peer to poll
        pass

    async def heartbeat(self, party_id: str, peer_id: str):
        """Send heartbeat to keep peer alive"""
        if party_id not in self.parties:
            return

        party = self.parties[party_id]
        if peer_id in party.peers:
            party.peers[peer_id].last_seen = datetime.now()

    async def _cleanup_task(self):
        """Cleanup stale peers and parties"""
        while True:
            await asyncio.sleep(60)  # Run every minute

            now = datetime.now()
            timeout = timedelta(minutes=5)

            parties_to_delete = []

            for party_id, party in self.parties.items():
                peers_to_delete = []

                # Find stale peers
                for peer_id, peer in party.peers.items():
                    if now - peer.last_seen > timeout:
                        peers_to_delete.append(peer_id)

                # Remove stale peers
                for peer_id in peers_to_delete:
                    del party.peers[peer_id]

                # Mark empty parties for deletion
                if len(party.peers) == 0:
                    parties_to_delete.append(party_id)

            # Delete empty parties
            for party_id in parties_to_delete:
                del self.parties[party_id]

            if parties_to_delete or any(peers_to_delete for _ in self.parties.values()):
                await self._save_state()

    async def _save_state(self):
        """Save state to disk"""
        try:
            import aiofiles
            
            state = {
                "parties": {k: v.to_dict() for k, v in self.parties.items()},
                "my_peer_id": self.my_peer_id,
                "my_party_id": self.my_party_id,
            }

            # Create parent directory if it doesn't exist
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Use async file I/O
            async with aiofiles.open(self.state_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(state, indent=2))
        except OSError as e:
            # Log but don't fail if we can't save (disk full, permissions, etc.)
            print(
                f"Warning: Failed to save state to {self.state_file}: {e}",
                file=sys.stderr,
            )
        except json.JSONEncodeError as e:
            # Log serialization errors
            print(f"Warning: Failed to serialize state: {e}", file=sys.stderr)
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Warning: Unexpected error saving state: {e}", file=sys.stderr)

    async def _load_state(self):
        """Load state from disk"""
        try:
            import aiofiles
            
            if self.state_file.exists():
                async with aiofiles.open(self.state_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    state = json.loads(content)

                self.parties = {
                    k: PartyInfo.from_dict(v)
                    for k, v in state.get("parties", {}).items()
                }
                self.my_peer_id = state.get("my_peer_id")
                self.my_party_id = state.get("my_party_id")
        except OSError as e:
            # Log but start fresh if we can't load (file not found, permissions, etc.)
            print(
                f"Warning: Failed to load state from {self.state_file}: {e}",
                file=sys.stderr,
            )
        except json.JSONDecodeError as e:
            # Log but start fresh if state file is corrupted
            print(
                f"Warning: Corrupted state file, starting fresh: {e}", file=sys.stderr
            )
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Warning: Unexpected error loading state: {e}", file=sys.stderr)


class LocalControlPlane(ControlPlane):
    """
    Local-only control plane for testing

    Uses file-based storage and local discovery.
    Good for same-LAN testing before deploying real control server.
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self.discovery_file = config.config_dir / "discovery.json"

    async def register_party(
        self, party_id: str, name: str, host_peer_info: PeerInfo
    ) -> PartyInfo:
        """Register party and announce on local network"""
        party = await super().register_party(party_id, name, host_peer_info)

        # Write to discovery file for local peers
        await self._announce_party(party)

        return party

    async def _announce_party(self, party: PartyInfo):
        """Announce party on local network"""
        try:
            import aiofiles
            
            # Write party info to shared discovery file
            discovery = {}
            if self.discovery_file.exists():
                async with aiofiles.open(self.discovery_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    discovery = json.loads(content)

            discovery[party.party_id] = party.to_dict()
            
            # Create parent directory if it doesn't exist
            self.discovery_file.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(self.discovery_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(discovery, indent=2))
        except OSError as e:
            # Log but don't fail if we can't announce (disk full, permissions, etc.)
            print(
                f"Warning: Failed to announce party to {self.discovery_file}: {e}",
                file=sys.stderr,
            )
        except json.JSONEncodeError as e:
            # Log serialization errors
            print(f"Warning: Failed to serialize party info: {e}", file=sys.stderr)
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Warning: Unexpected error announcing party: {e}", file=sys.stderr)

    async def discover_parties(self) -> Dict[str, PartyInfo]:
        """Discover parties on local network"""
        try:
            import aiofiles
            
            if self.discovery_file.exists():
                async with aiofiles.open(self.discovery_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                    discovery = json.loads(content)
                return {k: PartyInfo.from_dict(v) for k, v in discovery.items()}
        except OSError as e:
            # Log but return empty if we can't read discovery file
            print(
                f"Warning: Failed to read discovery file {self.discovery_file}: {e}",
                file=sys.stderr,
            )
        except json.JSONDecodeError as e:
            # Log but return empty if discovery file is corrupted
            print(f"Warning: Corrupted discovery file: {e}", file=sys.stderr)
        except Exception as e:
            # Catch any other unexpected errors
            print(
                f"Warning: Unexpected error discovering parties: {e}", file=sys.stderr
            )

        return {}


class RemoteControlPlane(ControlPlane):
    """
    Remote control plane client

    Connects to a centralized control server for peer discovery.
    This is what will be used in production.
    """

    def __init__(self, config: Config, server_url: str):
        super().__init__(config)
        self.server_url = server_url
        self.ws = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds

    async def initialize(self):
        """Initialize connection to control server"""
        await super().initialize()

        # Attempt to connect to control server
        try:
            await self._connect()
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Failed to connect to control server: {error_msg}")
            print("   Falling back to local mode")
            # Fall back to local mode on failure

    async def _connect(self):
        """Connect to control server via WebSocket"""
        try:
            # Import websockets here to avoid dependency if not using remote control
            try:
                import websockets
            except ImportError:
                print("⚠️  websockets library not installed")
                raise ControlPlaneError(
                    "websockets library required for remote control"
                )

            # Convert HTTP(S) URL to WebSocket URL
            ws_url = self.server_url.replace("https://", "wss://").replace(
                "http://", "ws://"
            )

            # Add WebSocket path
            if not ws_url.endswith("/"):
                ws_url += "/"
            ws_url += "ws"

            print(f"Connecting to control server: {ws_url}")

            # Connect with timeout
            self.ws = await asyncio.wait_for(
                websockets.connect(ws_url, ping_interval=30, ping_timeout=10),
                timeout=10,
            )

            self.connected = True
            self.reconnect_attempts = 0

            print("✓ Connected to control server")

            # Start message handler
            asyncio.create_task(self._handle_messages())

            # Send authentication if needed
            await self._authenticate()

        except asyncio.TimeoutError:
            print("⚠️  Connection timeout")
            raise ControlPlaneError("Connection timeout")
        except ImportError:
            # Already handled above
            raise
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Connection failed: {error_msg}")
            raise ControlPlaneError(f"Connection failed: {error_msg}")

    async def _authenticate(self):
        """Authenticate with control server"""
        # TODO: Implement authentication
        # For now, just send a hello message
        try:
            await self._send_message(
                {"type": "hello", "version": "1.0", "client": "lanrage"}
            )
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Authentication failed: {error_msg}")

    async def _handle_messages(self):
        """Handle incoming messages from control server"""
        # Import websockets for exception handling
        try:
            import websockets
        except ImportError:
            print("⚠️  websockets library not available")
            return

        while self.connected and self.ws:
            try:
                message = await self.ws.recv()
                data = json.loads(message)

                # Handle different message types
                msg_type = data.get("type")

                if msg_type == "party_update":
                    await self._handle_party_update(data)
                elif msg_type == "peer_joined":
                    await self._handle_peer_joined(data)
                elif msg_type == "peer_left":
                    await self._handle_peer_left(data)
                elif msg_type == "signal":
                    await self._handle_signal(data)
                elif msg_type == "error":
                    error_msg = data.get("message", "Unknown error")
                    print(f"⚠️  Server error: {error_msg}")

            except websockets.exceptions.ConnectionClosed:
                print("⚠️  Connection to control server closed")
                self.connected = False
                await self._reconnect()
                break
            except json.JSONDecodeError as e:
                error_msg = str(e)
                print(f"⚠️  Invalid message from server: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️  Error handling message: {error_msg}")

    async def _reconnect(self):
        """Attempt to reconnect to control server"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(
                f"❌ Failed to reconnect after {self.max_reconnect_attempts} attempts"
            )
            print("   Falling back to local mode")
            return

        self.reconnect_attempts += 1
        print(
            f"🔄 Reconnecting to control server (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})..."
        )

        await asyncio.sleep(self.reconnect_delay)

        try:
            await self._connect()
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Reconnection failed: {error_msg}")
            await self._reconnect()

    async def _send_message(self, data: dict):
        """Send message to control server"""
        if not self.connected or not self.ws:
            raise ControlPlaneError("Not connected to control server")

        try:
            await self.ws.send(json.dumps(data))
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Failed to send message: {error_msg}")
            self.connected = False
            raise ControlPlaneError(f"Failed to send message: {error_msg}")

    async def _handle_party_update(self, data: dict):
        """Handle party update from server"""
        try:
            party_data = data.get("party")
            if party_data:
                party = PartyInfo.from_dict(party_data)
                self.parties[party.party_id] = party
                await self._save_state()
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Error handling party update: {error_msg}")

    async def _handle_peer_joined(self, data: dict):
        """Handle peer joined notification"""
        try:
            party_id = data.get("party_id")
            peer_data = data.get("peer")

            if party_id and peer_data and party_id in self.parties:
                peer = PeerInfo.from_dict(peer_data)
                self.parties[party_id].peers[peer.peer_id] = peer
                print(f"👤 Peer {peer.name} joined party")
                await self._save_state()
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Error handling peer joined: {error_msg}")

    async def _handle_peer_left(self, data: dict):
        """Handle peer left notification"""
        try:
            party_id = data.get("party_id")
            peer_id = data.get("peer_id")

            if party_id and peer_id and party_id in self.parties:
                if peer_id in self.parties[party_id].peers:
                    peer_name = self.parties[party_id].peers[peer_id].name
                    del self.parties[party_id].peers[peer_id]
                    print(f"👤 Peer {peer_name} left party")
                    await self._save_state()
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Error handling peer left: {error_msg}")

    async def _handle_signal(self, data: dict):
        """Handle signaling message"""
        # TODO: Implement signaling for WebRTC-style connection setup
        pass

    async def register_party(
        self, party_id: str, name: str, host_peer_info: PeerInfo
    ) -> PartyInfo:
        """Register party with control server"""
        if self.connected:
            try:
                # Send registration request to server
                await self._send_message(
                    {
                        "type": "register_party",
                        "party_id": party_id,
                        "name": name,
                        "host_peer": host_peer_info.to_dict(),
                    }
                )

                # Wait for confirmation (with timeout)
                # For now, just create locally and assume server will sync
                party = await super().register_party(party_id, name, host_peer_info)
                return party

            except Exception as e:
                error_msg = str(e)
                print(f"⚠️  Failed to register party with server: {error_msg}")
                print("   Using local registration")

        # Fall back to local registration
        return await super().register_party(party_id, name, host_peer_info)

    async def join_party(self, party_id: str, peer_info: PeerInfo) -> PartyInfo:
        """Join party via control server"""
        if self.connected:
            try:
                # Send join request to server
                await self._send_message(
                    {
                        "type": "join_party",
                        "party_id": party_id,
                        "peer": peer_info.to_dict(),
                    }
                )

                # Wait for party info from server
                # For now, use local join
                party = await super().join_party(party_id, peer_info)
                return party

            except Exception as e:
                error_msg = str(e)
                print(f"⚠️  Failed to join party via server: {error_msg}")
                print("   Using local join")

        # Fall back to local join
        return await super().join_party(party_id, peer_info)

    async def leave_party(self, party_id: str, peer_id: str):
        """Leave party via control server"""
        if self.connected:
            try:
                await self._send_message(
                    {"type": "leave_party", "party_id": party_id, "peer_id": peer_id}
                )
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️  Failed to notify server of leave: {error_msg}")

        # Always update local state
        await super().leave_party(party_id, peer_id)

    async def heartbeat(self, party_id: str, peer_id: str):
        """Send heartbeat to control server"""
        if self.connected:
            try:
                {"type": "heartbeat", "party_id": party_id, "peer_id": peer_id}

            except OSError as e:
                # Heartbeat failures are not critical, but log for debugging
                print(
                    f"Debug: Heartbeat failed for party {party_id}: {e}",
                    file=sys.stderr,
                )
            except Exception as e:
                # Catch any other unexpected errors
                print(f"Debug: Unexpected error in heartbeat: {e}", file=sys.stderr)
                pass

        # Always update local state
        await super().heartbeat(party_id, peer_id)

    async def close(self):
        """Close connection to control server"""
        self.connected = False
        if self.ws:
            await self.ws.close()
            self.ws = None


class ControlPlaneError(Exception):
    """Control plane errors"""

    pass


def create_control_plane(config: Config) -> ControlPlane:
    """Factory function to create appropriate control plane"""
    # Check if remote control plane is configured
    if config.control_server and config.control_server != "https://control.lanrage.io":
        # Use HTTP-based remote control plane client
        try:
            from .control_client import create_control_plane_client

            print(f"🌐 Using remote control plane: {config.control_server}")
            return create_control_plane_client(config)
        except ImportError as e:
            print(f"⚠️  Failed to import control client: {e}")
            print("   Falling back to local control plane")
            return LocalControlPlane(config)
    else:
        # Use local control plane
        return LocalControlPlane(config)
