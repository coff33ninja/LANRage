"""Party management - the core gaming experience"""

import asyncio
import secrets
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .config import Config
from .connection import ConnectionManager
from .control import ControlPlane, PeerInfo, create_control_plane
from .nat import ConnectionCoordinator, NATTraversal, NATType
from .network import NetworkManager

# NAT compatibility matrix for direct P2P connections
NAT_COMPATIBILITY = {
    NATType.OPEN: [
        NATType.OPEN,
        NATType.FULL_CONE,
        NATType.RESTRICTED_CONE,
        NATType.PORT_RESTRICTED_CONE,
        NATType.SYMMETRIC,
    ],
    NATType.FULL_CONE: [
        NATType.OPEN,
        NATType.FULL_CONE,
        NATType.RESTRICTED_CONE,
        NATType.PORT_RESTRICTED_CONE,
    ],
    NATType.RESTRICTED_CONE: [
        NATType.OPEN,
        NATType.FULL_CONE,
        NATType.RESTRICTED_CONE,
    ],
    NATType.PORT_RESTRICTED_CONE: [NATType.OPEN, NATType.FULL_CONE],
    NATType.SYMMETRIC: [NATType.OPEN],  # Only direct to open NAT
    NATType.UNKNOWN: [],  # Unknown NAT requires relay
}


class Peer(BaseModel):
    """A peer in the party"""

    id: str
    name: str
    public_key: str  # Base64 encoded WireGuard public key
    virtual_ip: str
    endpoint: str | None = None
    latency_ms: float | None = None
    connection_type: str = "unknown"  # "direct", "relayed", "connecting"
    nat_type: str = "unknown"  # NAT type for compatibility checking
    joined_at: datetime = datetime.now()


class Party(BaseModel):
    """A gaming party (virtual LAN)"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    host_id: str
    peers: dict[str, Peer] = {}
    created_at: datetime = datetime.now()

    def get_peer_list(self) -> list[Peer]:
        """Get list of all peers in party"""
        return list(self.peers.values())

    def get_compatible_peers(self, my_nat_type: NATType) -> list[Peer]:
        """Get list of peers compatible with my NAT type for direct connection

        Uses NAT compatibility matrix to determine which peers can establish
        direct P2P connections without relay.

        Args:
            my_nat_type: My NAT type

        Returns:
            List of peers that can be directly connected to
        """
        compatible = []
        compatible_types = NAT_COMPATIBILITY.get(my_nat_type, [])

        for peer in self.peers.values():
            # Get peer's NAT type from the nat_type field
            try:
                peer_nat_type = NATType(peer.nat_type)
            except (ValueError, KeyError):
                peer_nat_type = NATType.UNKNOWN

            # Check if peer's NAT type is compatible
            if peer_nat_type in compatible_types:
                compatible.append(peer)

        return compatible


class PartyManager:
    """Manages parties and peer connections"""

    def __init__(self, config: Config, network: NetworkManager):
        self.config = config
        self.network = network
        self.current_party: Party | None = None
        self.my_peer_id = secrets.token_hex(8)

        # NAT traversal
        self.nat: NATTraversal | None = None
        self.coordinator: ConnectionCoordinator | None = None

        # Control plane
        self.control: ControlPlane | None = None

        # Connection manager
        self.connections: ConnectionManager | None = None

    async def initialize_nat(self):
        """Initialize NAT traversal"""
        # Pass control client if available for relay discovery
        control_client = None
        if self.control:
            # Get the control client from control plane
            if hasattr(self.control, "client"):
                control_client = self.control.client

        self.nat = NATTraversal(self.config, control_client)

        try:
            # Detect NAT type
            await self.nat.detect_nat()
            self.coordinator = ConnectionCoordinator(self.config, self.nat)
        except Exception as e:
            # NAT detection failed, but continue
            # Will fall back to relay-only mode
            print(f"NAT detection failed: {e}. Using relay-only mode.")

    async def initialize_control(self):
        """Initialize control plane"""
        self.control = create_control_plane(self.config)
        await self.control.initialize()

        # Initialize connection manager
        if self.nat and self.control:
            self.connections = ConnectionManager(
                self.config, self.network, self.nat, self.control
            )

    async def create_party(self, name: str) -> Party:
        """Create a new party"""
        party = Party(id=secrets.token_hex(6), name=name, host_id=self.my_peer_id)

        # Add self as first peer
        my_peer = Peer(
            id=self.my_peer_id,
            name=self.config.peer_name,
            public_key=self.network.public_key_b64,
            virtual_ip="10.66.0.1",
            connection_type="host",
            nat_type=self.nat.nat_type.value if self.nat else "unknown",
        )
        party.peers[self.my_peer_id] = my_peer

        self.current_party = party

        # Register with control plane
        if self.control and self.nat:
            my_peer_info = PeerInfo(
                peer_id=self.my_peer_id,
                name="Me",
                public_key=self.network.public_key_b64,
                nat_type=self.nat.nat_type.value,
                public_ip=self.nat.public_ip or "unknown",
                public_port=self.nat.public_port or 0,
                local_ip=self.nat.local_ip or "unknown",
                local_port=self.nat.local_port or 0,
                last_seen=datetime.now(),
            )

            await self.control.register_party(party.id, name, my_peer_info)

        return party

    async def join_party(self, party_id: str, peer_name: str) -> Party:
        """Join an existing party"""
        if not self.control or not self.nat:
            raise NotImplementedError("Control plane not initialized")

        # Create peer info
        my_peer_info = PeerInfo(
            peer_id=self.my_peer_id,
            name=peer_name,
            public_key=self.network.public_key_b64,
            nat_type=self.nat.nat_type.value,
            public_ip=self.nat.public_ip or "unknown",
            public_port=self.nat.public_port or 0,
            local_ip=self.nat.local_ip or "unknown",
            local_port=self.nat.local_port or 0,
            last_seen=datetime.now(),
        )

        # Join via control plane
        party_info = await self.control.join_party(party_id, my_peer_info)

        # Convert to local party format
        party = Party(
            id=party_info.party_id,
            name=party_info.name,
            host_id=party_info.host_id,
            created_at=party_info.created_at,
        )

        # Add all peers
        for peer_id, peer_info in party_info.peers.items():
            peer = Peer(
                id=peer_id,
                name=peer_info.name,
                public_key=peer_info.public_key,
                virtual_ip=f"10.66.0.{hash(peer_id) % 254 + 2}",  # Simple allocation
                connection_type="connecting",
                nat_type=peer_info.nat_type,
            )
            party.peers[peer_id] = peer

        self.current_party = party

        # Connect to all existing peers
        if self.connections:
            for peer_id in party.peers.keys():
                if peer_id != self.my_peer_id:
                    asyncio.create_task(self._connect_to_peer(party_id, peer_id))

        return party

    async def leave_party(self):
        """Leave current party"""
        if self.current_party and self.control:
            # Disconnect from all peers
            if self.connections:
                for peer_id in list(self.connections.connections.keys()):
                    await self.connections.disconnect_from_peer(peer_id)

            # Leave via control plane
            await self.control.leave_party(self.current_party.id, self.my_peer_id)

            self.current_party = None

    async def _connect_to_peer(self, party_id: str, peer_id: str):
        """Connect to a peer (internal)"""
        if not self.connections:
            return

        try:
            success = await self.connections.connect_to_peer(party_id, peer_id)

            if success and self.current_party and peer_id in self.current_party.peers:
                # Update peer status
                self.current_party.peers[peer_id].connection_type = "direct"
        except Exception as e:
            # Connection failed
            print(f"Failed to connect to peer {peer_id}: {e}")
            if self.current_party and peer_id in self.current_party.peers:
                self.current_party.peers[peer_id].connection_type = "failed"

    async def get_party_status(self) -> dict:
        """Get current party status"""
        if not self.current_party:
            return {"status": "no_party"}

        # Measure latencies
        for peer in self.current_party.peers.values():
            if peer.id != self.my_peer_id and peer.virtual_ip:
                peer.latency_ms = await self.network.measure_latency(peer.virtual_ip)

        # Include NAT info
        nat_info = {}
        if self.nat:
            nat_info = {
                "nat_type": self.nat.nat_type.value,
                "public_ip": self.nat.public_ip,
                "public_port": self.nat.public_port,
            }

        return {
            "status": "in_party",
            "party": self.current_party.model_dump(),
            "peer_count": len(self.current_party.peers),
            "nat_info": nat_info,
        }
