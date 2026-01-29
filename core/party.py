"""Party management - the core gaming experience"""

import asyncio
import secrets
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel

from .config import Config
from .network import NetworkManager


class Peer(BaseModel):
    """A peer in the party"""
    id: str
    name: str
    public_key: bytes
    virtual_ip: str
    endpoint: str | None = None
    latency_ms: float | None = None
    connection_type: str = "unknown"  # "direct", "relayed", "connecting"
    joined_at: datetime = datetime.now()


class Party(BaseModel):
    """A gaming party (virtual LAN)"""
    id: str
    name: str
    host_id: str
    peers: Dict[str, Peer] = {}
    created_at: datetime = datetime.now()
    
    class Config:
        arbitrary_types_allowed = True


class PartyManager:
    """Manages parties and peer connections"""
    
    def __init__(self, config: Config, network: NetworkManager):
        self.config = config
        self.network = network
        self.current_party: Party | None = None
        self.my_peer_id = secrets.token_hex(8)
        
    async def create_party(self, name: str) -> Party:
        """Create a new party"""
        party = Party(
            id=secrets.token_hex(6),
            name=name,
            host_id=self.my_peer_id
        )
        
        # Add self as first peer
        my_peer = Peer(
            id=self.my_peer_id,
            name="Me",  # TODO: Get from config
            public_key=self.network.public_key,
            virtual_ip="10.66.0.1",
            connection_type="host"
        )
        party.peers[self.my_peer_id] = my_peer
        
        self.current_party = party
        return party
    
    async def join_party(self, party_id: str, peer_name: str) -> Party:
        """Join an existing party"""
        # TODO: Implement party discovery and joining
        # This requires control plane communication
        raise NotImplementedError("Party joining requires control plane")
    
    async def leave_party(self):
        """Leave current party"""
        if self.current_party:
            # TODO: Notify peers, cleanup connections
            self.current_party = None
    
    async def get_party_status(self) -> dict:
        """Get current party status"""
        if not self.current_party:
            return {"status": "no_party"}
        
        # Measure latencies
        for peer in self.current_party.peers.values():
            if peer.id != self.my_peer_id and peer.virtual_ip:
                peer.latency_ms = await self.network.measure_latency(peer.virtual_ip)
        
        return {
            "status": "in_party",
            "party": self.current_party.model_dump(),
            "peer_count": len(self.current_party.peers)
        }
