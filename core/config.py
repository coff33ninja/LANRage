"""Configuration management - Database-first approach"""

# import os  # Removed: Environment variable loading replaced by database-first approach
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .exceptions import ConfigError
from .logging_config import get_logger, timing_decorator

# from .exceptions import DatabaseConfigError  # Removed: No longer raised after database-first refactoring

logger = get_logger(__name__)


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
    @timing_decorator(name="config_load")
    async def load(cls) -> "Config":
        """
        Load config from settings database (primary and only source)

        Returns:
            Config: Configuration loaded from database

        Raises:
            ConfigError: If database cannot be loaded or is not initialized
        """
        try:
            logger.info("Loading configuration from settings database")
            from core.settings import get_settings_db

            db = await get_settings_db()
            settings = await db.get_all_settings()

            # Check if database is initialized (has required settings)
            if not settings:
                logger.error("Settings database is empty - not initialized")
                raise ConfigError(
                    "Settings database is empty. Please configure LANrage through the WebUI at http://localhost:8666/settings.html"
                )

            logger.debug(f"Loaded {len(settings)} settings from database")

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

            logger.info(
                f"Configuration loaded successfully (mode: {config.mode}, peer: {config.peer_name})"
            )
            return config

        except ImportError as e:
            logger.error(f"Settings database module not available: {e}")
            raise ConfigError(
                f"Settings database module not available: {e}. "
                "This is a critical error - please reinstall LANrage."
            ) from e
        except Exception as e:
            logger.error(f"Failed to load configuration: {type(e).__name__}: {e}")
            raise ConfigError(
                f"Failed to load configuration from database: {type(e).__name__}: {e}. "
                "Please ensure the database is initialized by running setup.py or accessing the WebUI."
            ) from e
