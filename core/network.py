"""Network management - WireGuard interface and routing"""

import asyncio
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

from .config import Config


class NetworkManager:
    """Manages WireGuard interface and network stack"""
    
    def __init__(self, config: Config):
        self.config = config
        self.interface_name = config.interface_name
        self.private_key: bytes | None = None
        self.public_key: bytes | None = None
        
    async def initialize(self):
        """Initialize network interface"""
        # Generate or load WireGuard keys
        await self._ensure_keys()
        
        # Create WireGuard interface (platform-specific)
        # TODO: Implement actual WireGuard setup
        # For now, just validate we have keys
        
    async def _ensure_keys(self):
        """Generate or load WireGuard keypair"""
        private_key_path = self.config.keys_dir / "private.key"
        public_key_path = self.config.keys_dir / "public.key"
        
        if private_key_path.exists() and public_key_path.exists():
            # Load existing keys
            self.private_key = private_key_path.read_bytes()
            self.public_key = public_key_path.read_bytes()
        else:
            # Generate new keypair
            private_key = x25519.X25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            self.private_key = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            self.public_key = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            # Save keys
            private_key_path.write_bytes(self.private_key)
            public_key_path.write_bytes(self.public_key)
            
            # Secure permissions
            private_key_path.chmod(0o600)
    
    async def measure_latency(self, peer_ip: str) -> float:
        """Measure latency to peer (in ms)"""
        # TODO: Implement actual ping measurement
        # For now, return mock value
        return 23.5
    
    async def add_peer(self, peer_public_key: bytes, peer_endpoint: str, allowed_ips: list[str]):
        """Add a WireGuard peer"""
        # TODO: Implement WireGuard peer configuration
        pass
    
    async def remove_peer(self, peer_public_key: bytes):
        """Remove a WireGuard peer"""
        # TODO: Implement peer removal
        pass
