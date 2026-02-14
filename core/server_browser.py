"""Game server browser and discovery"""

import asyncio
import contextlib
import statistics
import time
from dataclasses import dataclass, field

from .config import Config
from .logging_config import get_logger, set_context, timing_decorator

logger = get_logger(__name__)


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
    map_name: str | None = None
    game_mode: str | None = None
    password_protected: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    latency_ms: float | None = None

    # Advanced latency metrics
    latency_ema: float | None = None  # Exponential Moving Average
    latency_trend: str = "stable"  # "improving", "stable", "degrading"
    latency_samples: list[float] = field(default_factory=list)  # Last 10 samples
    last_latency_check: float = field(default_factory=time.time)
    measurement_interval: int = 30  # Adaptive interval in seconds

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
            "latency_ema": self.latency_ema,
            "latency_trend": self.latency_trend,
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
        self._cleanup_task: asyncio.Task | None = None

    @timing_decorator(name="server_browser_start")
    async def start(self):
        """Start server browser"""
        self.running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Server browser started")

    async def stop(self):
        """Stop server browser"""
        self.running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
        logger.info(f"Server browser stopped ({len(self.servers)} servers in memory)")

    @timing_decorator(name="server_registration")
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
        map_name: str | None = None,
        game_mode: str | None = None,
        password_protected: bool = False,
        tags: list[str] | None = None,
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
        set_context(peer_id_val=host_peer_id)
        logger.info(
            f"Registering server: {name} ({game}) - {current_players}/{max_players} players"
        )
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

    def get_server(self, server_id: str) -> GameServer | None:
        """Get server by ID

        Args:
            server_id: Server ID

        Returns:
            GameServer if found, None otherwise
        """
        return self.servers.get(server_id)

    def list_servers(
        self,
        game: str | None = None,
        hide_full: bool = False,
        hide_empty: bool = False,
        hide_password: bool = False,
        tags: list[str] | None = None,
        search: str | None = None,
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
        games = {server.game for server in self.servers.values()}
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

    async def measure_latency(self, server_id: str) -> float | None:
        """Measure latency to a server using multiple samples for accuracy

        Includes exponential moving average smoothing and trend detection.

        Args:
            server_id: Server ID

        Returns:
            Median latency in milliseconds, or None if measurement failed
        """
        server = self.get_server(server_id)
        if not server:
            return None

        try:
            # Take multiple samples for more reliable latency measurement
            import platform

            param = "-n" if platform.system().lower() == "windows" else "-c"

            # Collect 3 ping samples in parallel
            sample_count = 3
            ping_tasks = []

            for _ in range(sample_count):
                command = ["ping", param, "1", server.host_ip]
                ping_tasks.append(self._single_ping(command))

            # Execute all pings concurrently
            results = await asyncio.gather(*ping_tasks, return_exceptions=True)

            # Filter out exceptions and failed measurements
            valid_latencies = [
                latency
                for latency in results
                if isinstance(latency, (int, float)) and latency < 999
            ]

            if valid_latencies:
                # Use median for more robust latency estimate (less affected by outliers)
                median_latency = statistics.median(valid_latencies)
                server.latency_ms = median_latency

                # Update EMA (Exponential Moving Average) for smoothing
                self._update_ema(server, median_latency)

                # Track samples and detect trends
                self._update_latency_samples(server, median_latency)

                # Adapt measurement interval based on latency quality
                self._adapt_measurement_interval(server)

                return median_latency
            # All measurements failed or timed out
            server.latency_ms = 999
            server.latency_trend = "degrading"
            return 999.0

        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Latency measurement failed for {server.name}: {error_msg}")

        return None

    def _update_ema(self, server: GameServer, new_latency: float, alpha: float = 0.3):
        """Update exponential moving average of latency

        EMA = alpha * current_value + (1 - alpha) * previous_EMA
        Lower alpha = more smoothing (less responsive)
        Higher alpha = less smoothing (more responsive)

        Args:
            server: GameServer instance
            new_latency: New latency measurement
            alpha: smoothing factor (0.3 = 30% new, 70% historical)
        """
        if server.latency_ema is None:
            server.latency_ema = new_latency
        else:
            server.latency_ema = (alpha * new_latency) + (
                (1 - alpha) * server.latency_ema
            )

    def _update_latency_samples(
        self, server: GameServer, latency: float, max_samples: int = 10
    ):
        """Track latency samples for trend analysis

        Args:
            server: GameServer instance
            latency: New latency measurement
            max_samples: Maximum samples to keep
        """
        server.latency_samples.append(latency)

        # Keep only recent samples
        if len(server.latency_samples) > max_samples:
            server.latency_samples = server.latency_samples[-max_samples:]

        # Detect trend based on samples
        if len(server.latency_samples) >= 3:
            recent = server.latency_samples[-3:]
            avg_old = sum(server.latency_samples[:-1]) / len(
                server.latency_samples[:-1]
            )
            avg_new = recent[-1]

            # Simple trend detection: compare recent measurement to historical average
            improvement_threshold = avg_old * 0.05  # 5% change

            if avg_new < avg_old - improvement_threshold:
                server.latency_trend = "improving"
            elif avg_new > avg_old + improvement_threshold:
                server.latency_trend = "degrading"
            else:
                server.latency_trend = "stable"

    def _adapt_measurement_interval(self, server: GameServer):
        """Adapt latency measurement interval based on connection quality

        Good connection: measure less frequently (60s)
        Degrading connection: measure more frequently (10s)

        Args:
            server: GameServer instance
        """
        if server.latency_ema is None:
            return

        # If latency is good and stable, measure less frequently
        if server.latency_ema < 50 and server.latency_trend != "degrading":
            server.measurement_interval = 60  # Check every 60s
        # If latency is moderate, check regularly
        elif server.latency_ema < 150:
            server.measurement_interval = 30  # Check every 30s
        # If latency is high or degrading, check frequently
        else:
            server.measurement_interval = 10  # Check every 10s

    async def _single_ping(self, command: list) -> float | None:
        """Execute a single ping and return latency

        Args:
            command: Ping command as list

        Returns:
            Latency in milliseconds or 999 on timeout/failure
        """
        try:
            start_time = time.time()
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=2.0)
                elapsed = (time.time() - start_time) * 1000

                if proc.returncode == 0:
                    # Parse ping output for more accurate latency
                    output = stdout.decode().lower()
                    if "time=" in output:
                        # Extract time value from ping output
                        time_str = output.split("time=")[1].split()[0]
                        return float(time_str.replace("ms", ""))
                    return elapsed
                return elapsed
            except TimeoutError:
                return 999.0

        except Exception:
            return 999.0

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
