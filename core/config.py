"""Configuration management"""

import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


class Config(BaseModel):
    """LANrage configuration"""
    
    # Mode: client or relay
    mode: Literal["client", "relay"] = "client"
    
    # Network settings
    virtual_subnet: str = "10.66.0.0/16"
    interface_name: str = "lanrage0"
    
    # API settings
    api_host: str = "127.0.0.1"
    api_port: int = 8666
    
    # Control plane
    control_server: str = "https://control.lanrage.io"  # TODO: implement
    
    # Relay settings (for relay mode)
    relay_public_ip: str | None = None
    relay_port: int = 51820
    
    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".lanrage")
    keys_dir: Path = Field(default_factory=lambda: Path.home() / ".lanrage" / "keys")
    
    @classmethod
    def load(cls) -> "Config":
        """Load config from environment or defaults"""
        config = cls(
            mode=os.getenv("LANRAGE_MODE", "client"),
            api_host=os.getenv("LANRAGE_API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("LANRAGE_API_PORT", "8666")),
            relay_public_ip=os.getenv("LANRAGE_RELAY_IP"),
        )
        
        # Ensure directories exist
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.keys_dir.mkdir(parents=True, exist_ok=True)
        
        return config
