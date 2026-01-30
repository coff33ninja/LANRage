"""Configuration management"""

import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .exceptions import ConfigError, DatabaseConfigError

logger = logging.getLogger(__name__)


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

    # User settings
    peer_name: str = "Player"

    # WireGuard settings
    wireguard_keepalive: int = 25  # Default keepalive in seconds

    # Control plane
    control_server: str = "https://control.lanrage.io"  # TODO: implement

    # Relay settings (for relay mode)
    relay_public_ip: str | None = None
    relay_port: int = 51820
    max_clients: int = 100

    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".lanrage")
    keys_dir: Path = Field(default_factory=lambda: Path.home() / ".lanrage" / "keys")

    @classmethod
    def load(cls) -> "Config":
        """Load config from environment or defaults"""
        try:
            api_port = int(os.getenv("LANRAGE_API_PORT", "8666"))
        except ValueError as e:
            raise ConfigError(
                f"Invalid LANRAGE_API_PORT: must be an integer: {e}"
            ) from e

        try:
            config = cls(
                mode=os.getenv("LANRAGE_MODE", "client"),
                api_host=os.getenv("LANRAGE_API_HOST", "127.0.0.1"),
                api_port=api_port,
                peer_name=os.getenv("LANRAGE_PEER_NAME", "Player"),
                relay_public_ip=os.getenv("LANRAGE_RELAY_IP"),
            )
        except Exception as e:
            raise ConfigError(
                f"Failed to create config: {type(e).__name__}: {e}"
            ) from e

        # Ensure directories exist
        try:
            config.config_dir.mkdir(parents=True, exist_ok=True)
            config.keys_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigError(f"Failed to create config directories: {e}") from e

        logger.info("Configuration loaded from environment")
        return config

    @classmethod
    async def load_from_db(cls) -> "Config":
        """
        Load config from settings database
        Falls back to environment variables if database not available
        """
        try:
            from core.settings import get_settings_db

            db = await get_settings_db()
            settings = await db.get_all_settings()

            config = cls(
                mode=settings.get("mode", "client"),
                virtual_subnet=settings.get("virtual_subnet", "10.66.0.0/16"),
                interface_name=settings.get("interface_name", "lanrage0"),
                api_host=settings.get("api_host", "127.0.0.1"),
                api_port=settings.get("api_port", 8666),
                peer_name=settings.get("peer_name", "Player"),
                wireguard_keepalive=settings.get("wireguard_keepalive", 25),
                control_server=settings.get(
                    "control_server", "https://control.lanrage.io"
                ),
                relay_public_ip=settings.get("relay_public_ip"),
                relay_port=settings.get("relay_port", 51820),
                max_clients=settings.get("max_clients", 100),
            )

            # Ensure directories exist
            config.config_dir.mkdir(parents=True, exist_ok=True)
            config.keys_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Configuration loaded from database")
            return config

        except ImportError as e:
            logger.warning(
                f"Settings database not available: {e}. Falling back to environment variables."
            )
            raise DatabaseConfigError(f"Settings module import failed: {e}") from e
        except Exception as e:
            logger.warning(
                f"Failed to load config from database ({type(e).__name__}: {e}). Falling back to environment variables."
            )
            raise DatabaseConfigError(
                f"Database configuration loading failed: {type(e).__name__}: {e}"
            ) from e
