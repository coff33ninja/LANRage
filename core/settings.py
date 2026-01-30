"""
Persistent settings storage using SQLite
Async database operations for configuration and user preferences
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite


class SettingsDatabase:
    """
    Async SQLite database for persistent settings

    Stores:
    - Application settings (mode, network config, etc.)
    - User preferences (peer name, UI settings, etc.)
    - Server configurations (relay settings, control plane, etc.)
    - Game profiles and customizations
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()  # Use asyncio for thread-safe operations

    async def initialize(self):
        """Initialize database schema"""
        async with self._lock:  # Use asyncio lock for concurrent access protection
            async with aiosqlite.connect(self.db_path) as db:
                # Settings table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        type TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Server configurations table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS server_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1,
                        config TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Favorite servers table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS favorite_servers (
                        server_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        game TEXT NOT NULL,
                        address TEXT NOT NULL,
                        added_at TEXT NOT NULL
                    )
                """)

                # Game profiles table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS game_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        game TEXT NOT NULL,
                        profile TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                await db.commit()

    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            "SELECT value, type FROM settings WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                value, value_type = row
                return self._deserialize(value, value_type)
            return default

    async def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        value_str, value_type = self._serialize(value)
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO settings (key, value, type, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    type = excluded.type,
                    updated_at = excluded.updated_at
                """,
                (key, value_str, value_type, now),
            )
            await db.commit()

    async def get_all_settings(self) -> dict[str, Any]:
        """Get all settings"""
        settings = {}
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT key, value, type FROM settings") as cursor:
                async for row in cursor:
                    key, value, value_type = row
                    settings[key] = self._deserialize(value, value_type)
        return settings

    async def delete_setting(self, key: str):
        """Delete a setting"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM settings WHERE key = ?", (key,))
            await db.commit()

    # Server configurations

    async def save_server_config(self, name: str, mode: str, config: dict) -> int:
        """Save a server configuration"""
        now = datetime.now().isoformat()
        config_json = json.dumps(config)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO server_configs (name, mode, config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, mode, config_json, now, now),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_server_config(self, config_id: int) -> dict | None:
        """Get a server configuration"""
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            "SELECT name, mode, config, enabled FROM server_configs WHERE id = ?",
            (config_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                name, mode, config_json, enabled = row
                return {
                    "id": config_id,
                    "name": name,
                    "mode": mode,
                    "config": json.loads(config_json),
                    "enabled": bool(enabled),
                }
            return None

    async def get_all_server_configs(self) -> list[dict]:
        """Get all server configurations"""
        configs = []
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            "SELECT id, name, mode, config, enabled FROM server_configs ORDER BY name"
        ) as cursor:
            async for row in cursor:
                config_id, name, mode, config_json, enabled = row
                configs.append(
                    {
                        "id": config_id,
                        "name": name,
                        "mode": mode,
                        "config": json.loads(config_json),
                        "enabled": bool(enabled),
                    }
                )
        return configs

    async def update_server_config(self, config_id: int, config: dict):
        """Update a server configuration"""
        now = datetime.now().isoformat()
        config_json = json.dumps(config)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE server_configs
                SET config = ?, updated_at = ?
                WHERE id = ?
                """,
                (config_json, now, config_id),
            )
            await db.commit()

    async def delete_server_config(self, config_id: int):
        """Delete a server configuration"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM server_configs WHERE id = ?", (config_id,))
            await db.commit()

    async def toggle_server_config(self, config_id: int, enabled: bool):
        """Enable or disable a server configuration"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE server_configs SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, config_id),
            )
            await db.commit()

    # Favorite servers

    async def add_favorite_server(
        self, server_id: str, name: str, game: str, address: str
    ):
        """Add a server to favorites"""
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO favorite_servers (server_id, name, game, address, added_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(server_id) DO UPDATE SET
                    name = excluded.name,
                    game = excluded.game,
                    address = excluded.address
                """,
                (server_id, name, game, address, now),
            )
            await db.commit()

    async def remove_favorite_server(self, server_id: str):
        """Remove a server from favorites"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM favorite_servers WHERE server_id = ?", (server_id,)
            )
            await db.commit()

    async def get_favorite_servers(self) -> list[dict]:
        """Get all favorite servers"""
        favorites = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT server_id, name, game, address, added_at FROM favorite_servers ORDER BY added_at DESC"
            ) as cursor:
                async for row in cursor:
                    server_id, name, game, address, added_at = row
                    favorites.append(
                        {
                            "server_id": server_id,
                            "name": name,
                            "game": game,
                            "address": address,
                            "added_at": added_at,
                        }
                    )
        return favorites

    async def is_favorite(self, server_id: str) -> bool:
        """Check if a server is in favorites"""
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            "SELECT 1 FROM favorite_servers WHERE server_id = ?", (server_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

    # Game profiles

    async def save_game_profile(self, name: str, game: str, profile: dict) -> int:
        """Save a custom game profile"""
        now = datetime.now().isoformat()
        profile_json = json.dumps(profile)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO game_profiles (name, game, profile, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    game = excluded.game,
                    profile = excluded.profile,
                    updated_at = excluded.updated_at
                """,
                (name, game, profile_json, now, now),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_game_profile(self, name: str) -> dict | None:
        """Get a game profile"""
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            "SELECT game, profile FROM game_profiles WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                game, profile_json = row
                return {
                    "name": name,
                    "game": game,
                    "profile": json.loads(profile_json),
                }
            return None

    async def get_all_game_profiles(self) -> list[dict]:
        """Get all game profiles"""
        profiles = []
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            "SELECT name, game, profile FROM game_profiles ORDER BY name"
        ) as cursor:
            async for row in cursor:
                name, game, profile_json = row
                profiles.append(
                    {
                        "name": name,
                        "game": game,
                        "profile": json.loads(profile_json),
                    }
                )
        return profiles

    async def delete_game_profile(self, name: str):
        """Delete a game profile"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM game_profiles WHERE name = ?", (name,))
            await db.commit()

    # Database maintenance and validation

    def validate_database_integrity(self) -> bool:
        """
        Validate database integrity using synchronous sqlite3
        Useful for startup checks and diagnostics

        Returns:
            True if database is valid, False otherwise
        """
        try:
            # Use sqlite3 for synchronous integrity check
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            conn.close()

            return result[0] == "ok"
        except Exception:
            return False

    def get_database_size(self) -> int:
        """
        Get database file size in bytes using synchronous check

        Returns:
            Database size in bytes
        """
        try:
            return self.db_path.stat().st_size
        except Exception:
            return 0

    def backup_database(self, backup_path: Path) -> bool:
        """
        Create a backup of the database using sqlite3 backup API

        Args:
            backup_path: Path where backup should be created

        Returns:
            True if backup successful, False otherwise
        """
        try:
            # Use sqlite3 for synchronous backup
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(backup_path)

            # Perform backup
            source.backup(backup)

            source.close()
            backup.close()

            return True
        except Exception:
            return False

    # Helper methods

    def _serialize(self, value: Any) -> tuple[str, str]:
        """Serialize a value for storage"""
        if isinstance(value, bool):
            return str(value), "bool"
        if isinstance(value, int):
            return str(value), "int"
        if isinstance(value, float):
            return str(value), "float"
        if isinstance(value, str):
            return value, "str"
        if isinstance(value, (dict, list)):
            return json.dumps(value), "json"
        return str(value), "str"

    def _deserialize(self, value: str, value_type: str) -> Any:
        """Deserialize a value from storage"""
        if value_type == "bool":
            return value.lower() == "true"
        if value_type == "int":
            return int(value)
        if value_type == "float":
            return float(value)
        if value_type == "json":
            return json.loads(value)
        return value


# Global settings instance
_settings_db: SettingsDatabase | None = None


async def get_settings_db() -> SettingsDatabase:
    """Get the global settings database instance"""
    global _settings_db
    if _settings_db is None:
        db_path = Path.home() / ".lanrage" / "settings.db"
        _settings_db = SettingsDatabase(db_path)
        await _settings_db.initialize()
    return _settings_db


async def init_default_settings():
    """Initialize default settings if not present"""
    db = await get_settings_db()

    defaults = {
        "mode": "client",
        "peer_name": "Player",
        "api_host": "127.0.0.1",
        "api_port": 8666,
        "virtual_subnet": "10.66.0.0/16",
        "interface_name": "lanrage0",
        "wireguard_keepalive": 25,
        "control_server": "https://control.lanrage.io",
        "relay_port": 51820,
        "max_clients": 100,
        "auto_optimize_games": True,
        "enable_broadcast": True,
        "enable_discord": False,
        "discord_app_id": "",  # Discord Application ID for Rich Presence
        "discord_webhook": "",  # Discord webhook URL for notifications
        "discord_invite": "",  # Discord voice channel invite URL
        "enable_metrics": True,
    }

    # Only set if not already present
    for key, value in defaults.items():
        current = await db.get_setting(key)
        if current is None:
            await db.set_setting(key, value)
