"""Game server browser and discovery"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from .config import Config


@dataclass
class GameServer:
    """Represents a game server"""

    id: str
    name: str
    game: str
    host_peer_id: str
    host_peer_name: str
    host_ip: str
    max_players: int
    current_players: int
    map_name: Optional[str] = None
    game_mode: Optional[str] = None
    password_protected: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    latency_ms: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "game": self.game,
            "host_peer_id": self.host_peer_id,
            "host_peer_name": self.host_peer_name,
            "host_ip": self.host_ip,
            "max_players": self.max_players,
            "current_players": self.current_players,
            "map_name": self.map_name,
            "game_mode": self.game_mode,
            "password_protected": self.password_protected,
            "tags": self.tags,
            "created_at": self.created_at,
            "last_heartbeat": self.last_heartbeat,
            "latency_ms": self.latency_ms,
            "is_full": self.current_players >= self.max_players,
            "age_seconds": time.time() - self.created_at,
        }

    def is_expired(self, timeout: int = 60) -> bool:
        """Check if server heartbeat has expired"""
        return time.time() - self.last_heartbeat > timeout

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = time.time()


class ServerBrowser:
    """Manages game server discovery and browsing"""

    def __init__(self, config: Config):
        self.config = config
        self.servers: dict[str, GameServer] = {}
        self.favorites: set[str] = set()
        self.running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start server browser"""
        self.running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        print("✓ Server browser started")

    async def stop(self):
        """Stop server browser"""
        self.running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        print("✓ Server browser stopped")

    async def register_server(
        self,
        server_id: str,
        name: str,
        game: str,
        host_peer_id: str,
        host_peer_name: str,
        host_ip: str,
        max_players: int,
        current_players: int = 0,
        map_name: Optional[str] = None,
        game_mode: Optional[str] = None,
        password_protected: bool = False,
        tags: Optional[list[str]] = None,
    ) -> GameServer:
        """Register a new game server

        Args:
            server_id: Unique server identifier
            name: Server name
            game: Game name
            host_peer_id: Host peer ID
            host_peer_name: Host peer name
            host_ip: Host IP address
            max_players: Maximum players
            current_players: Current player count
            map_name: Current map name
            game_mode: Game mode
            password_protected: Whether server requires password
            tags: Server tags for filtering

        Returns:
            Registered GameServer instance
        """
        if server_id in self.servers:
            # Update existing server
            server = self.servers[server_id]
            server.name = name
            server.current_players = current_players
            server.map_name = map_name
            server.game_mode = game_mode
            server.update_heartbeat()
        else:
            # Create new server
            server = GameServer(
                id=server_id,
                name=name,
                game=game,
                host_peer_id=host_peer_id,
                host_peer_name=host_peer_name,
                host_ip=host_ip,
                max_players=max_players,
                current_players=current_players,
                map_name=map_name,
                game_mode=game_mode,
                password_protected=password_protected,
                tags=tags or [],
            )
            self.servers[server_id] = server
            print(f"✓ Server registered: {name} ({game})")

        return server

    async def unregister_server(self, server_id: str) -> bool:
        """Unregister a game server

        Args:
            server_id: Server ID to unregister

        Returns:
            True if server was unregistered, False if not found
        """
        if server_id in self.servers:
            server = self.servers[server_id]
            del self.servers[server_id]
            print(f"✓ Server unregistered: {server.name}")
            return True
        return False

    async def update_heartbeat(self, server_id: str) -> bool:
        """Update server heartbeat

        Args:
            server_id: Server ID

        Returns:
            True if heartbeat updated, False if server not found
        """
        if server_id in self.servers:
            self.servers[server_id].update_heartbeat()
            return True
        return False

    async def update_player_count(self, server_id: str, current_players: int) -> bool:
        """Update server player count

        Args:
            server_id: Server ID
            current_players: Current player count

        Returns:
            True if updated, False if server not found
        """
        if server_id in self.servers:
            self.servers[server_id].current_players = current_players
            self.servers[server_id].update_heartbeat()
            return True
        return False

    def get_server(self, server_id: str) -> Optional[GameServer]:
        """Get server by ID

        Args:
            server_id: Server ID

        Returns:
            GameServer if found, None otherwise
        """
        return self.servers.get(server_id)

    def list_servers(
        self,
        game: Optional[str] = None,
        hide_full: bool = False,
        hide_empty: bool = False,
        hide_password: bool = False,
        tags: Optional[list[str]] = None,
        search: Optional[str] = None,
    ) -> list[GameServer]:
        """List servers with optional filtering

        Args:
            game: Filter by game name
            hide_full: Hide full servers
            hide_empty: Hide empty servers
            hide_password: Hide password-protected servers
            tags: Filter by tags (any match)
            search: Search in server name

        Returns:
            List of matching GameServer instances
        """
        servers = list(self.servers.values())

        # Filter by game
        if game:
            servers = [s for s in servers if s.game.lower() == game.lower()]

        # Filter full servers
        if hide_full:
            servers = [s for s in servers if s.current_players < s.max_players]

        # Filter empty servers
        if hide_empty:
            servers = [s for s in servers if s.current_players > 0]

        # Filter password-protected
        if hide_password:
            servers = [s for s in servers if not s.password_protected]

        # Filter by tags
        if tags:
            servers = [s for s in servers if any(tag in s.tags for tag in tags)]

        # Search in name
        if search:
            search_lower = search.lower()
            servers = [
                s
                for s in servers
                if search_lower in s.name.lower()
                or search_lower in s.game.lower()
                or (s.host_peer_name and search_lower in s.host_peer_name.lower())
            ]

        # Sort by player count (descending), then by name
        servers.sort(key=lambda s: (-s.current_players, s.name.lower()))

        return servers

    def get_games_list(self) -> list[str]:
        """Get list of unique games with active servers

        Returns:
            Sorted list of game names
        """
        games = set(server.game for server in self.servers.values())
        return sorted(games)

    def add_favorite(self, server_id: str):
        """Add server to favorites

        Args:
            server_id: Server ID to favorite
        """
        self.favorites.add(server_id)

    def remove_favorite(self, server_id: str):
        """Remove server from favorites

        Args:
            server_id: Server ID to unfavorite
        """
        self.favorites.discard(server_id)

    def is_favorite(self, server_id: str) -> bool:
        """Check if server is favorited

        Args:
            server_id: Server ID

        Returns:
            True if favorited, False otherwise
        """
        return server_id in self.favorites

    def get_favorites(self) -> list[GameServer]:
        """Get list of favorite servers

        Returns:
            List of favorited GameServer instances
        """
        return [
            server
            for server_id, server in self.servers.items()
            if server_id in self.favorites
        ]

    async def measure_latency(self, server_id: str) -> Optional[float]:
        """Measure latency to a server

        Args:
            server_id: Server ID

        Returns:
            Latency in milliseconds, or None if measurement failed
        """
        server = self.get_server(server_id)
        if not server:
            return None

        try:
            # Use ICMP ping to measure latency
            import platform
            import subprocess

            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", server.host_ip]

            start_time = time.time()
            result = subprocess.run(command, capture_output=True, text=True, timeout=2)
            elapsed = (time.time() - start_time) * 1000

            if result.returncode == 0:
                # Parse ping output for more accurate latency
                output = result.stdout.lower()
                if "time=" in output:
                    # Extract time value from ping output
                    time_str = output.split("time=")[1].split()[0]
                    latency = float(time_str.replace("ms", ""))
                    server.latency_ms = latency
                    return latency
                else:
                    server.latency_ms = elapsed
                    return elapsed

        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Latency measurement failed for {server.name}: {error_msg}")

        return None

    async def _cleanup_loop(self):
        """Background task to clean up expired servers"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Find expired servers
                expired = [
                    server_id
                    for server_id, server in self.servers.items()
                    if server.is_expired(timeout=90)  # 90 second timeout
                ]

                # Remove expired servers
                for server_id in expired:
                    server = self.servers[server_id]
                    print(f"⚠ Server expired: {server.name}")
                    del self.servers[server_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                error_msg = str(e)
                print(f"⚠ Server cleanup error: {error_msg}")

    def get_stats(self) -> dict:
        """Get server browser statistics

        Returns:
            Dictionary with browser stats
        """
        total_servers = len(self.servers)
        total_players = sum(s.current_players for s in self.servers.values())
        games = self.get_games_list()

        return {
            "total_servers": total_servers,
            "total_players": total_players,
            "unique_games": len(games),
            "games": games,
            "favorites": len(self.favorites),
        }
