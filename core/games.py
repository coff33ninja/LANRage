"""Game detection and profiles"""

import asyncio
import json
import platform
import socket
import time
from dataclasses import dataclass
from pathlib import Path

import psutil

from .config import Config
from .logging_config import get_logger, set_context, timing_decorator
from .nat import NATType

logger = get_logger(__name__)


def calculate_adaptive_keepalive(
    nat_type: NATType, profile_keepalive: int | None = None
) -> int:
    """Calculate keepalive interval based on NAT type

    Symmetric NAT needs frequent keepalive to maintain bindings.
    Cone NAT is more forgiving and can use longer intervals.

    Args:
        nat_type: Detected NAT type
        profile_keepalive: Optional keepalive override from game profile

    Returns:
        Keepalive interval in seconds
    """
    # If profile specifies a keepalive and it's not the default, use it
    if profile_keepalive and profile_keepalive != 25:
        return profile_keepalive

    # Map NAT types to keepalive intervals
    # These are optimized for maintaining NAT bindings without excessive traffic
    nat_keepalive_map = {
        NATType.OPEN: 60,  # No NAT, can be very relaxed
        NATType.FULL_CONE: 45,  # Relaxed, mapping is stable
        NATType.RESTRICTED_CONE: 30,  # Moderate, address restricted
        NATType.PORT_RESTRICTED_CONE: 15,  # Strict, port restricted
        NATType.SYMMETRIC: 8,  # Very strict, needs frequent keepalive
        NATType.UNKNOWN: 25,  # Default to conservative value
    }

    return nat_keepalive_map.get(nat_type, 25)


@dataclass
class GameProfile:
    """Profile for a specific game"""

    name: str
    executable: str  # Process name
    ports: list[int]  # Ports used by game
    protocol: str  # "udp", "tcp", or "both"
    broadcast: bool  # Uses broadcast discovery
    multicast: bool  # Uses multicast discovery
    keepalive: int  # Keepalive interval (seconds)
    mtu: int  # Optimal MTU
    description: str

    # Optimization hints
    low_latency: bool = True
    high_bandwidth: bool = False
    packet_priority: str = "high"  # "low", "medium", "high"


@dataclass
class DetectionResult:
    """Result of game detection attempt"""

    game_id: str
    profile: GameProfile
    confidence: float  # 0.0 to 1.0
    method: str  # "process", "window_title", "port", "hash", etc.
    details: dict = None  # Detection-specific details

    def __post_init__(self):
        """Ensure confidence is in valid range"""
        if self.details is None:
            self.details = {}
        self.confidence = max(0.0, min(1.0, self.confidence))

    def __lt__(self, other):
        """Allow sorting by confidence (higher is better)"""
        return self.confidence > other.confidence


async def load_game_profiles() -> dict[str, GameProfile]:
    """Load game profiles from JSON files organized by genre

    Returns:
        Dictionary mapping game_id to GameProfile
    """
    profiles: dict[str, GameProfile] = {}

    # Get the game_profiles directory
    base_dir = Path(__file__).parent.parent / "game_profiles"

    if not base_dir.exists():
        print(f"Warning: Game profiles directory not found: {base_dir}")
        return profiles

    # Load all JSON files in the game_profiles directory
    json_files = list(base_dir.glob("*.json"))

    # Also load custom profiles
    custom_dir = base_dir / "custom"
    if custom_dir.exists():
        json_files.extend(custom_dir.glob("*.json"))

    for json_file in json_files:
        try:
            # Use aiofiles for async file I/O
            import aiofiles

            async with aiofiles.open(json_file, encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)

            # Skip files with comments (like example.json)
            if "_comment" in data:
                continue

            # Parse each game profile
            for game_id, profile_data in data.items():
                try:
                    profile = GameProfile(
                        name=profile_data["name"],
                        executable=profile_data["executable"],
                        ports=profile_data["ports"],
                        protocol=profile_data["protocol"],
                        broadcast=profile_data.get("broadcast", False),
                        multicast=profile_data.get("multicast", False),
                        keepalive=profile_data.get("keepalive", 25),
                        mtu=profile_data.get("mtu", 1420),
                        description=profile_data.get("description", ""),
                        low_latency=profile_data.get("low_latency", False),
                        high_bandwidth=profile_data.get("high_bandwidth", False),
                        packet_priority=profile_data.get("packet_priority", "medium"),
                    )
                    profiles[game_id] = profile
                except (KeyError, TypeError) as e:
                    print(
                        f"Warning: Invalid profile '{game_id}' in {json_file.name}: {e}"
                    )
                    continue

            print(f"✓ Loaded {len(data)} profiles from {json_file.name}")

        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse {json_file.name}: {e}")
        except Exception as e:
            print(f"Warning: Error loading {json_file.name}: {e}")

    print(f"🎮 Total game profiles loaded: {len(profiles)}")
    return profiles


# Load profiles on module import - need to handle async loading
GAME_PROFILES: dict[str, GameProfile] = {}


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings (fuzzy matching)"""
    s1 = s1.lower()
    s2 = s2.lower()

    if len(s1) < len(s2):
        # pylint: disable=arguments-out-of-order  # Intentional swap for algorithm
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _fuzzy_match_executable(
    proc_name: str, profile_exe: str, threshold: float = 0.85
) -> bool:
    """Check if process name fuzzy matches profile executable

    Args:
        proc_name: Running process name
        profile_exe: Profile executable name
        threshold: Match threshold (0-1, higher = stricter)

    Returns:
        True if fuzzy match passes
    """
    # Exact match first (fastest path)
    if proc_name.lower() == profile_exe.lower():
        return True

    # Remove extensions for comparison
    proc_clean = proc_name.lower().replace(".exe", "").replace(".bat", "")
    exe_clean = profile_exe.lower().replace(".exe", "").replace(".bat", "")

    if proc_clean == exe_clean:
        return True

    # Levenshtein distance based fuzzy match
    # pylint: disable=arguments-out-of-order
    distance = _levenshtein_distance(proc_clean, exe_clean)
    max_len = max(len(proc_clean), len(exe_clean))

    if max_len == 0:
        return False

    similarity = 1.0 - (distance / max_len)
    return similarity >= threshold


class ProfileCache:
    """Cache for game profiles with TTL"""

    def __init__(self, ttl_seconds: float = 30.0):
        self.ttl = ttl_seconds
        self.profiles = {}
        self.last_load_time = 0
        self._lock = asyncio.Lock()

    async def get(self) -> dict[str, GameProfile]:
        """Get cached profiles, reload if expired"""
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_load_time > self.ttl:
                self.profiles = await load_game_profiles()
                self.last_load_time = current_time
            return self.profiles

    async def invalidate(self):
        """Force reload on next access"""
        async with self._lock:
            self.last_load_time = 0


_profile_cache = ProfileCache(ttl_seconds=30.0)


async def initialize_game_profiles():
    """Initialize game profiles asynchronously"""
    global GAME_PROFILES  # pylint: disable=global-variable-not-assigned
    profiles = await load_game_profiles()
    GAME_PROFILES.clear()
    GAME_PROFILES.update(profiles)


class GameDetector:
    """Detects running games"""

    def __init__(self, config: Config, optimizer=None):
        self.config = config
        self.detected_games: set[str] = set()
        self.running = False
        self._game_manager = None  # Will be set by GameManager
        self.optimizer = optimizer  # Will be set after initialization

        # Path for custom game profiles
        self.custom_profiles_path = Path(config.config_dir) / "game_profiles.json"

        # Detection history tracking: (timestamp, game_id, action)
        self.detection_history: list[tuple[float, str, str]] = []

    async def start(self):
        """Start game detection"""
        self.running = True
        logger.info("Game detection starting")

        # Load custom profiles if they exist
        await self._load_custom_profiles()

        asyncio.create_task(self._detection_loop())
        logger.debug(f"Loaded {len(GAME_PROFILES)} game profiles")

    async def _load_custom_profiles(self):
        """Load custom game profiles from file"""
        if self.custom_profiles_path.exists():
            try:
                import json

                import aiofiles

                async with aiofiles.open(
                    self.custom_profiles_path, encoding="utf-8"
                ) as f:
                    content = await f.read()
                    custom_data = json.loads(content)

                # Parse and add custom profiles to GAME_PROFILES
                loaded_count = 0
                for game_id, profile_data in custom_data.items():
                    try:
                        # Create GameProfile from profile_data
                        profile = GameProfile(
                            name=profile_data["name"],
                            executable=profile_data["executable"],
                            ports=profile_data["ports"],
                            protocol=profile_data["protocol"],
                            broadcast=profile_data.get("broadcast", False),
                            multicast=profile_data.get("multicast", False),
                            keepalive=profile_data.get("keepalive", 25),
                            mtu=profile_data.get("mtu", 1420),
                            description=profile_data.get("description", ""),
                            low_latency=profile_data.get("low_latency", False),
                            high_bandwidth=profile_data.get("high_bandwidth", False),
                            packet_priority=profile_data.get(
                                "packet_priority", "medium"
                            ),
                        )

                        # Add to GAME_PROFILES
                        GAME_PROFILES[game_id] = profile
                        loaded_count += 1
                        logger.debug(
                            f"Loaded custom profile: {game_id} - {profile.name}"
                        )
                    except (KeyError, TypeError) as e:
                        error_msg = str(e)
                        logger.warning(
                            f"Invalid profile data for {game_id}: {error_msg}"
                        )
                        print(
                            f"Warning: Invalid profile data for {game_id}: {error_msg}"
                        )
                        continue

                logger.info(f"Loaded {loaded_count} custom game profiles")
                print(
                    f"Loaded {len(custom_data)} custom profiles from {self.custom_profiles_path}"
                )
            except json.JSONDecodeError as e:
                error_msg = str(e)
                logger.error(f"Could not parse custom profiles JSON: {error_msg}")
                print(f"Warning: Could not parse custom profiles JSON: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Could not load custom profiles: {error_msg}")
                print(f"Warning: Could not load custom profiles: {error_msg}")

    async def stop(self):
        """Stop game detection"""
        self.running = False
        logger.info(
            f"Game detection stopped (detected {len(self.detected_games)} games)"
        )

    async def _detection_loop(self):
        """Continuously detect running games"""
        while self.running:
            await self._detect_games()
            await asyncio.sleep(5)  # Check every 5 seconds

    @timing_decorator(name="game_detection")
    async def _detect_games(self):
        """Detect currently running games using multiple detection methods

        Detection ranking (by confidence):
        1. Process name matching (95% confidence when matched)
        2. Window title detection (80% confidence)
        3. Open port detection (60% confidence)
        """
        current_games = set()
        detection_results: dict[str, list[DetectionResult]] = {}

        # Get all running processes
        loop = asyncio.get_event_loop()

        def _get_processes():
            processes = []
            for proc in psutil.process_iter(["name"]):
                try:
                    processes.append(proc.info["name"])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes

        proc_names = await loop.run_in_executor(None, _get_processes)

        # Method 1: Process name matching (highest priority)
        for proc_name in proc_names:
            for game_id, profile in GAME_PROFILES.items():
                if _fuzzy_match_executable(proc_name, profile.executable):
                    if game_id not in detection_results:
                        detection_results[game_id] = []
                    detection_results[game_id].append(
                        DetectionResult(
                            game_id=game_id,
                            profile=profile,
                            confidence=0.95,
                            method="process",
                            details={"process_name": proc_name},
                        )
                    )

        # Method 2: Window title detection (Windows only)
        if platform.system() == "Windows":
            window_detections = await self._detect_by_window_title()
            for result in window_detections:
                if result.game_id not in detection_results:
                    detection_results[result.game_id] = []
                detection_results[result.game_id].append(result)

        # Method 3: Port-based detection
        port_detections = await self._detect_by_open_ports()
        for result in port_detections:
            if result.game_id not in detection_results:
                detection_results[result.game_id] = []
            detection_results[result.game_id].append(result)

        # Select best detection per game (highest confidence)
        for game_id, results in detection_results.items():
            if results:
                max(results, key=lambda x: x.confidence)
                current_games.add(game_id)

        # Detect new games
        new_games = current_games - self.detected_games
        if new_games:
            for game_id in new_games:
                await self._on_game_started(game_id)
                # Notify game manager to apply optimizations
                if self._game_manager:
                    await self._game_manager.on_game_detected(game_id)

        # Detect stopped games
        stopped_games = self.detected_games - current_games
        if stopped_games:
            for game_id in stopped_games:
                await self._on_game_stopped(game_id)

        self.detected_games = current_games

    async def _detect_by_window_title(self) -> list[DetectionResult]:
        """Detect games by window title (Windows only)

        Returns:
            List of DetectionResult with confidence scores
        """
        results = []

        if platform.system() != "Windows":
            return results

        try:
            # pylint: disable=import-outside-toplevel
            import win32gui  # noqa: F401

            window_titles = []

            def get_window_titles():
                """Collect open window titles"""
                titles = []

                def enum_windows(hwnd, _):
                    try:
                        if win32gui.IsWindowVisible(hwnd):
                            title = win32gui.GetWindowText(hwnd)
                            if title and len(title) > 2:
                                titles.append(title)
                    except Exception:
                        pass
                    return True

                win32gui.EnumWindows(enum_windows, None)
                return titles

            loop = asyncio.get_event_loop()
            window_titles = await loop.run_in_executor(None, get_window_titles)

            # Try to match window titles to game profiles
            for window_title in window_titles:
                for game_id, profile in GAME_PROFILES.items():
                    # Check if game name appears in window title
                    if profile.name.lower() in window_title.lower():
                        results.append(
                            DetectionResult(
                                game_id=game_id,
                                profile=profile,
                                confidence=0.80,
                                method="window_title",
                                details={"window_title": window_title},
                            )
                        )

        except ImportError:
            # pywin32 not installed, skip window title detection
            pass
        except Exception:
            # Silently ignore errors in window detection
            pass

        return results

    async def _detect_by_open_ports(self) -> list[DetectionResult]:
        """Detect games by checking for open ports

        Returns:
            List of DetectionResult with confidence scores
        """
        results = []

        try:
            loop = asyncio.get_event_loop()

            def check_ports():
                """Check which ports are open"""
                open_ports = {}

                for game_id, profile in GAME_PROFILES.items():
                    matched_ports = []
                    for port in profile.ports:
                        # Try UDP
                        if profile.protocol in ("udp", "both"):
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.settimeout(0.1)
                            try:
                                sock.bind(("127.0.0.1", port))
                                sock.close()
                                # Port is available (not in use)
                            except OSError:
                                # Port is in use
                                matched_ports.append(port)
                        # Try TCP
                        if profile.protocol in ("tcp", "both"):
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(0.1)
                            try:
                                result = sock.connect_ex(("127.0.0.1", port))
                                if result == 0:
                                    matched_ports.append(port)
                            except Exception:
                                pass
                            sock.close()

                    if matched_ports:
                        # Calculate confidence based on port match percentage
                        match_ratio = len(matched_ports) / len(profile.ports)
                        confidence = min(0.6 + (match_ratio * 0.2), 0.75)
                        open_ports[game_id] = (profile, matched_ports, confidence)

                return open_ports

            open_ports_dict = await loop.run_in_executor(None, check_ports)

            for game_id, (
                profile,
                matched_ports,
                confidence,
            ) in open_ports_dict.items():
                results.append(
                    DetectionResult(
                        game_id=game_id,
                        profile=profile,
                        confidence=confidence,
                        method="port",
                        details={"matched_ports": matched_ports},
                    )
                )

        except Exception:
            # Silently ignore port detection errors
            pass

        return results

    async def _on_game_started(self, game_id: str):
        """Handle game started"""
        profile = GAME_PROFILES[game_id]
        print(f"🎮 Detected: {profile.name}")
        print(f"   Optimizing for {profile.name}...")

        # Set context for detection event
        set_context(correlation_id_val=f"game_{game_id}_{int(time.time()*1000)}")
        logger.info(
            f"Game detected: {profile.name} (game_id={game_id}, ports={profile.ports})"
        )

        # Record in detection history with timestamp
        self.detection_history.append((time.time(), game_id, "started"))

        # Keep history to last 100 events
        if len(self.detection_history) > 100:
            self.detection_history = self.detection_history[-100:]

        # Apply game-specific optimizations through optimizer
        # This will be called by the GameManager which has access to the optimizer
        # For now, just log the detection
        print(f"   Profile: {profile.description}")
        print(f"   Ports: {', '.join(str(p) for p in profile.ports)}")
        print(f"   Protocol: {profile.protocol.upper()}")

    async def _on_game_stopped(self, game_id: str):
        """Handle game stopped"""
        profile = GAME_PROFILES[game_id]
        print(f"🎮 Stopped: {profile.name}")

        logger.info(f"Game stopped: {profile.name} (game_id={game_id})")

        # Record in detection history with timestamp
        self.detection_history.append((time.time(), game_id, "stopped"))

        # Keep history to last 100 events
        if len(self.detection_history) > 100:
            self.detection_history = self.detection_history[-100:]

        # Clear active profile and reset to defaults
        if (
            hasattr(self, "optimizer")
            and self.optimizer.active_profile
            and self.optimizer.active_profile.name == profile.name
        ):
            logger.debug(f"Resetting network configuration for {profile.name}")
            print("   Resetting network configuration to defaults...")
            await self.optimizer.clear_profile()
            print("   ✓ Configuration reset complete")

    def get_active_games(self) -> list[GameProfile]:
        """Get list of active games"""
        return [GAME_PROFILES[game_id] for game_id in self.detected_games]

    def get_profile(self, game_id: str) -> GameProfile | None:
        """Get profile for a specific game"""
        return GAME_PROFILES.get(game_id)

    def get_detection_history(self) -> list[tuple[float, str, str]]:
        """Get game detection history

        Returns:
            List of tuples: (timestamp, game_id, action)
            where action is 'started' or 'stopped'
        """
        return self.detection_history.copy()

    async def save_custom_profile(self, game_id: str, profile: GameProfile):
        """Save a custom game profile to disk"""
        try:
            import json

            import aiofiles

            custom_profiles = {}

            # Load existing profiles
            if self.custom_profiles_path.exists():
                async with aiofiles.open(
                    self.custom_profiles_path, encoding="utf-8"
                ) as f:
                    content = await f.read()
                    custom_profiles = json.loads(content)

            # Add new profile
            custom_profiles[game_id] = {
                "name": profile.name,
                "executable": profile.executable,
                "ports": profile.ports,
                "protocol": profile.protocol,
                "broadcast": profile.broadcast,
                "multicast": profile.multicast,
                "keepalive": profile.keepalive,
                "mtu": profile.mtu,
                "description": profile.description,
                "low_latency": profile.low_latency,
                "high_bandwidth": profile.high_bandwidth,
                "packet_priority": profile.packet_priority,
            }

            # Save to file
            self.custom_profiles_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(
                self.custom_profiles_path, "w", encoding="utf-8"
            ) as f:
                await f.write(json.dumps(custom_profiles, indent=2))

            print(f"Saved custom profile for {profile.name}")
        except Exception as e:
            print(f"Error saving custom profile: {e}")


class GameOptimizer:
    """Applies game-specific optimizations"""

    def __init__(self, config: Config, nat_type: NATType | None = None):
        self.config = config
        self.nat_type = nat_type or NATType.UNKNOWN
        self.active_profile: GameProfile | None = None

        # Dynamic broadcast port monitoring
        self.game_ports: dict[str, set[int]] = {}  # game_id -> set of ports
        self.monitored_ports: set[int] = set()  # Currently monitored ports
        self.custom_ports_whitelist: set[int] = set()  # User-added ports
        self._load_custom_ports_whitelist()

    def set_nat_type(self, nat_type: NATType):
        """Update NAT type for adaptive keepalive calculation"""
        self.nat_type = nat_type

    def _load_custom_ports_whitelist(self):
        """Load user-defined custom ports for broadcast monitoring

        Reads from config file: custom_broadcast_ports.json
        Format: {"ports": [23456, 45678], "description": "Custom game server"}
        """
        try:
            custom_ports_file = (
                Path(self.config.config_dir) / "custom_broadcast_ports.json"
            )
            if custom_ports_file.exists():
                import json

                with open(custom_ports_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "ports" in data:
                        self.custom_ports_whitelist = set(data["ports"])
                        logger.info(
                            f"Loaded custom broadcast ports: {sorted(self.custom_ports_whitelist)}"
                        )
                    elif isinstance(data, list):
                        self.custom_ports_whitelist = set(data)
                        logger.info(
                            f"Loaded custom broadcast ports: {sorted(self.custom_ports_whitelist)}"
                        )
        except Exception as e:
            logger.debug(f"No custom broadcast ports file or error loading: {e}")

        # Also check for hardcoded custom ports in config
        if hasattr(self.config, "custom_broadcast_ports"):
            self.custom_ports_whitelist.update(self.config.custom_broadcast_ports)

    def add_custom_broadcast_port(self, port: int, description: str = ""):
        """Add a port to custom broadcast monitoring whitelist

        Args:
            port: Port number to add
            description: Optional description for the port
        """
        self.custom_ports_whitelist.add(port)
        logger.info(
            f"Added custom broadcast port {port}{f' ({description})' if description else ''}"
        )

        # Persist to file
        try:
            import json

            custom_ports_file = (
                Path(self.config.config_dir) / "custom_broadcast_ports.json"
            )
            with open(custom_ports_file, "w") as f:
                json.dump(
                    {
                        "ports": sorted(self.custom_ports_whitelist),
                        "description": "Custom ports for LANrage broadcast monitoring",
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"Failed to persist custom broadcast port {port}: {e}")

    def remove_custom_broadcast_port(self, port: int):
        """Remove a port from custom broadcast monitoring

        Args:
            port: Port number to remove
        """
        self.custom_ports_whitelist.discard(port)
        logger.info(f"Removed custom broadcast port {port}")

        # Persist to file
        try:
            import json

            custom_ports_file = (
                Path(self.config.config_dir) / "custom_broadcast_ports.json"
            )
            with open(custom_ports_file, "w") as f:
                json.dump(
                    {
                        "ports": sorted(self.custom_ports_whitelist),
                        "description": "Custom ports for LANrage broadcast monitoring",
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.warning(
                f"Failed to persist custom broadcast port removal {port}: {e}"
            )

    @timing_decorator(name="apply_game_profile")
    async def apply_profile(
        self,
        profile: GameProfile,
        network_manager=None,
        broadcast_manager=None,
        game_id: str = "",
    ):
        """Apply game profile optimizations with NAT-aware keepalive and dynamic broadcast

        Args:
            profile: Game profile to apply
            network_manager: NetworkManager instance for WireGuard config
            broadcast_manager: BroadcastManager instance for broadcast emulation
            game_id: Game identifier for tracking dynamic ports
        """
        self.active_profile = profile

        # Store manager references for later reset
        self._network_manager_ref = network_manager
        self._broadcast_manager_ref = broadcast_manager
        self._active_game_id = game_id

        print(f"⚙️  Applying optimizations for {profile.name}")
        logger.info(f"Applying game profile: {profile.name} (game_id={game_id})")

        # Calculate adaptive keepalive based on NAT type
        adaptive_keepalive = calculate_adaptive_keepalive(
            self.nat_type, profile.keepalive
        )

        # Adjust WireGuard keepalive
        if (
            adaptive_keepalive != 25
            and network_manager
            or network_manager
            and adaptive_keepalive != 25
        ):
            print(f"   - Keepalive: {adaptive_keepalive}s (NAT: {self.nat_type.value})")
            await self._update_keepalive(network_manager, adaptive_keepalive)

        # Enable broadcast emulation if needed (with dynamic tracking)
        if profile.broadcast and broadcast_manager:
            print("   - Broadcast emulation: ON (dynamic port monitoring enabled)")
            await self._enable_broadcast(broadcast_manager, profile, game_id)
            logger.info(
                f"Dynamic broadcast monitoring enabled for {len(profile.ports)} ports: {profile.ports}"
            )

        # Set packet priority
        if profile.packet_priority == "high":
            print("   - Packet priority: HIGH")
            await self._set_packet_priority(profile.packet_priority)

        # Adjust MTU if needed
        if profile.mtu != 1420 and network_manager:
            print(f"   - MTU: {profile.mtu}")
            await self._update_mtu(network_manager, profile.mtu)

        print(f"✓ Optimizations applied for {profile.name}")
        logger.info(
            f"Game profile applied: {profile.name}, Active ports: {sorted(self.monitored_ports)}"
        )

    async def _update_keepalive(self, network_manager, keepalive: int):
        """Update WireGuard keepalive for all peers"""
        try:
            # Update keepalive for all connected peers
            # This requires updating each peer's configuration
            # For now, store the value to be used when adding new peers
            self.config.wireguard_keepalive = keepalive
            print(f"   ✓ Keepalive set to {keepalive}s (will apply to new connections)")
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠ Failed to update keepalive: {error_msg}")

    async def _enable_broadcast(
        self, broadcast_manager, profile: GameProfile, game_id: str = ""
    ):
        """Enable broadcast emulation for game ports with dynamic port tracking

        Tracks which ports are used by which games to enable/disable listeners dynamically.

        Args:
            broadcast_manager: BroadcastManager instance
            profile: GameProfile with port information
            game_id: Game identifier for tracking purposes
        """
        try:
            # Track ports for this game
            if game_id:
                self.game_ports[game_id] = set(profile.ports)
                logger.debug(f"Registered game {game_id} with ports: {profile.ports}")

            # Start broadcast listeners for each game port
            for port in profile.ports:
                if port not in self.monitored_ports:
                    if profile.protocol in ("udp", "both"):
                        await broadcast_manager.start_listener(port, "udp")
                        self.monitored_ports.add(port)
                        print(f"   ✓ Broadcast listener started on UDP port {port}")
                        logger.info(
                            f"Dynamic: Started UDP broadcast listener on port {port}"
                        )
                    if profile.protocol in ("tcp", "both"):
                        await broadcast_manager.start_listener(port, "tcp")
                        self.monitored_ports.add(port)
                        print(f"   ✓ Broadcast listener started on TCP port {port}")
                        logger.info(
                            f"Dynamic: Started TCP broadcast listener on port {port}"
                        )
                else:
                    # Port already being monitored
                    logger.debug(
                        f"Port {port} already being monitored, skipping duplicate"
                    )
                    print(f"   ℹ Broadcast listener already active on port {port}")
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠ Failed to enable broadcast: {error_msg}")
            logger.warning(f"Failed to enable broadcast: {error_msg}")

    async def _set_packet_priority(self, priority: str):
        """Set packet priority (QoS/TOS bits) using platform-specific methods"""
        try:
            # Map priority to DSCP values
            dscp_map = {"low": 0, "medium": 18, "high": 46}  # CS0  # CS2 (AF21)  # EF

            dscp_value = dscp_map.get(priority, 0)

            # Apply platform-specific QoS
            if platform.system() == "Linux":
                await self._set_qos_linux(dscp_value)
            elif platform.system() == "Windows":
                await self._set_qos_windows(dscp_value)
            else:
                print(
                    f"   ℹ QoS not supported on {platform.system()}, skipping packet priority"
                )
                return

            print(f"   ✓ Packet priority set to {priority.upper()} (DSCP {dscp_value})")

        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠ Failed to set packet priority: {error_msg}")

    async def _set_qos_linux(self, dscp_value: int):
        """Set QoS on Linux using iptables and tc (Traffic Control)"""
        try:
            interface = self.config.interface_name

            # Convert DSCP to TOS value (DSCP << 2)
            tos_value = dscp_value << 2

            # Check if iptables is available
            check_cmd = "which iptables"
            result = await asyncio.create_subprocess_shell(
                check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            if result.returncode != 0:
                print("   ℹ iptables not available, skipping QoS setup")
                return

            # Set DSCP marking on outgoing packets from WireGuard interface
            # This marks packets so they get proper QoS treatment
            iptables_cmd = f"sudo iptables -t mangle -A POSTROUTING -o {interface} -j DSCP --set-dscp {dscp_value}"

            result = await asyncio.create_subprocess_shell(
                iptables_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if (
                result.returncode != 0
                and b"already exists" not in stderr
                and b"Chain already exists" not in stderr
            ):
                # Rule might already exist, check if it's a duplicate error
                error_msg = stderr.decode().strip()
                print(f"   ℹ iptables rule setup: {error_msg}")

            # Set up tc (Traffic Control) for advanced egress shaping
            # This provides bandwidth management and priority queuing
            await self._setup_tc_qos(interface, tos_value, dscp_value)

        except Exception as e:
            error_msg = str(e)
            print(f"   ℹ Linux QoS setup note: {error_msg}")

    async def _setup_tc_qos(self, interface: str, tos_value: int, dscp_value: int):
        """Set up Linux Traffic Control (tc) for advanced QoS"""
        try:
            # Check if tc is available
            check_cmd = "which tc"
            result = await asyncio.create_subprocess_shell(
                check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            if result.returncode != 0:
                print("   ℹ tc (Traffic Control) not available, using iptables only")
                return

            # Remove existing qdisc if present (cleanup)
            cleanup_cmd = f"sudo tc qdisc del dev {interface} root 2>/dev/null || true"
            result = await asyncio.create_subprocess_shell(
                cleanup_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            # Create HTB (Hierarchical Token Bucket) root qdisc
            # This allows bandwidth shaping and priority queuing
            root_cmd = (
                f"sudo tc qdisc add dev {interface} root handle 1: htb default 10"
            )
            result = await asyncio.create_subprocess_shell(
                root_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            if result.returncode != 0:
                print("   ℹ tc qdisc setup skipped (may already exist)")
                return

            # Create root class with maximum bandwidth (1Gbit)
            class_cmd = f"sudo tc class add dev {interface} parent 1: classid 1:1 htb rate 1gbit"
            result = await asyncio.create_subprocess_shell(
                class_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            # Create priority class based on DSCP value
            # High priority (DSCP 46): 800mbit guaranteed, 1gbit ceiling
            # Medium priority (DSCP 18): 500mbit guaranteed, 800mbit ceiling
            # Low priority (DSCP 0): 100mbit guaranteed, 500mbit ceiling
            if dscp_value >= 40:  # High priority (EF)
                rate = "800mbit"
                ceil = "1gbit"
                prio = 1
            elif dscp_value >= 10:  # Medium priority (AF/CS)
                rate = "500mbit"
                ceil = "800mbit"
                prio = 2
            else:  # Low priority (BE)
                rate = "100mbit"
                ceil = "500mbit"
                prio = 3

            # Create priority class
            prio_class_cmd = f"sudo tc class add dev {interface} parent 1:1 classid 1:{prio} htb rate {rate} ceil {ceil} prio {prio}"
            result = await asyncio.create_subprocess_shell(
                prio_class_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            # Add filter to match TOS/DSCP marked packets
            filter_cmd = f"sudo tc filter add dev {interface} protocol ip parent 1:0 prio {prio} u32 match ip tos {tos_value} 0xff flowid 1:{prio}"
            result = await asyncio.create_subprocess_shell(
                filter_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            if result.returncode == 0:
                print(
                    f"   ✓ Traffic Control configured (rate: {rate}, ceiling: {ceil})"
                )
            else:
                print("   ℹ tc filter setup skipped")

        except Exception as e:
            error_msg = str(e)
            print(f"   ℹ Traffic Control setup note: {error_msg}")

    async def _set_qos_windows(self, dscp_value: int):
        """Set QoS on Windows using netsh and QoS policies"""
        try:
            interface = self.config.interface_name

            # Windows QoS policy name
            policy_name = f"LANrage_{interface}_QoS"

            # Check if netsh is available (should be on all Windows systems)
            check_cmd = "where netsh"
            result = await asyncio.create_subprocess_shell(
                check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            if result.returncode != 0:
                print("   ℹ netsh not available, skipping QoS setup")
                return

            # Remove existing policy if it exists
            remove_cmd = f'netsh qos policy delete "{policy_name}"'
            result = await asyncio.create_subprocess_shell(
                remove_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()

            # Create QoS policy for WireGuard interface
            # This sets DSCP marking on outgoing packets
            create_cmd = (
                f'netsh qos policy add "{policy_name}" dscp={dscp_value} protocol=udp'
            )

            result = await asyncio.create_subprocess_shell(
                create_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode().strip()
                # Check if it's a permission error
                if "access is denied" in error_msg.lower():
                    print(
                        "   ℹ QoS setup requires administrator privileges (run as admin)"
                    )
                else:
                    print(f"   ℹ Windows QoS setup note: {error_msg}")

        except Exception as e:
            error_msg = str(e)
            print(f"   ℹ Windows QoS setup note: {error_msg}")

    async def _update_mtu(self, network_manager, mtu: int):
        """Update WireGuard interface MTU"""
        try:
            # Update interface MTU
            if network_manager.is_linux:
                await network_manager._run_command(
                    [
                        "sudo",
                        "ip",
                        "link",
                        "set",
                        "mtu",
                        str(mtu),
                        "dev",
                        network_manager.interface_name,
                    ]
                )
                print(f"   ✓ MTU updated to {mtu}")
            elif network_manager.is_windows:
                # Windows MTU update requires netsh
                await network_manager._run_command(
                    [
                        "netsh",
                        "interface",
                        "ipv4",
                        "set",
                        "subinterface",
                        network_manager.interface_name,
                        f"mtu={mtu}",
                    ]
                )
                print(f"   ✓ MTU updated to {mtu}")
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠ Failed to update MTU: {error_msg}")

    async def clear_profile(self):
        """Clear active profile and reset to defaults"""
        if self.active_profile:
            print(f"⚙️  Clearing optimizations for {self.active_profile.name}")
            profile_name = self.active_profile.name
            profile = self.active_profile
            self.active_profile = None

            # Reset to defaults
            print("   - Resetting to default configuration")

            # Reset keepalive to default (25s)
            if profile.keepalive != 25:
                print("   - Keepalive: 25s (default)")
                self.config.wireguard_keepalive = 25

            # Disable broadcast emulation if it was enabled
            if profile.broadcast and hasattr(self, "_broadcast_manager_ref"):
                broadcast_manager = self._broadcast_manager_ref
                if broadcast_manager:
                    print("   - Broadcast emulation: OFF")
                    await self._disable_broadcast(broadcast_manager, profile)

            # Reset packet priority to medium (default)
            if profile.packet_priority != "medium":
                print("   - Packet priority: MEDIUM (default)")

            # Reset MTU to default (1420)
            if profile.mtu != 1420 and hasattr(self, "_network_manager_ref"):
                network_manager = self._network_manager_ref
                if network_manager:
                    print("   - MTU: 1420 (default)")
                    await self._update_mtu(network_manager, 1420)

            print(f"✓ Reset complete for {profile_name}")

    async def _disable_broadcast(
        self, broadcast_manager, profile: GameProfile, game_id: str = ""
    ):
        """Disable broadcast emulation for game ports with dynamic untracking

        Only stop listening on ports if no other running game needs them.

        Args:
            broadcast_manager: BroadcastManager instance
            profile: GameProfile with port information
            game_id: Game identifier for untracking purposes
        """
        try:
            # Untrack ports for this game
            if game_id and game_id in self.game_ports:
                del self.game_ports[game_id]
                logger.debug(f"Unregistered game {game_id}")

            # Check if any other active game needs each port
            for port in profile.ports:
                ports_in_use = set()
                for other_game_id, ports in self.game_ports.items():
                    ports_in_use.update(ports)

                # Only stop listener if no other game uses this port
                if port not in ports_in_use and port not in self.custom_ports_whitelist:
                    if port in self.monitored_ports:
                        if profile.protocol in ("udp", "both"):
                            await broadcast_manager.stop_listener(port)
                            self.monitored_ports.discard(port)
                            print(f"   ✓ Broadcast listener stopped on UDP port {port}")
                            logger.info(
                                f"Dynamic: Stopped UDP broadcast listener on port {port}"
                            )
                        if profile.protocol in ("tcp", "both"):
                            await broadcast_manager.stop_listener(port)
                            self.monitored_ports.discard(port)
                            print(f"   ✓ Broadcast listener stopped on TCP port {port}")
                            logger.info(
                                f"Dynamic: Stopped TCP broadcast listener on port {port}"
                            )
                else:
                    logger.debug(
                        f"Port {port} still in use by other game(s), keeping listener active"
                    )
                    print(
                        f"   ℹ Port {port} still in use, keeping broadcast listener active"
                    )
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠ Failed to disable broadcast: {error_msg}")
            logger.warning(f"Failed to disable broadcast: {error_msg}")


class GameManager:
    """Manages game detection and optimization"""

    def __init__(
        self,
        config: Config,
        network_manager=None,
        broadcast_manager=None,
        nat_traversal=None,
    ):
        self.config = config
        self.optimizer = GameOptimizer(config)
        self.detector = GameDetector(config, optimizer=self.optimizer)
        self.network_manager = network_manager
        self.broadcast_manager = broadcast_manager
        self.nat_traversal = nat_traversal

        # Hook up detector to game manager
        self.detector._game_manager = self

    async def start(self):
        """Start game management"""
        # Ensure game profiles are loaded
        if not GAME_PROFILES:
            await initialize_game_profiles()

        # Update optimizer with current NAT type if available
        if self.nat_traversal and hasattr(self.nat_traversal, "nat_type"):
            self.optimizer.set_nat_type(self.nat_traversal.nat_type)

        await self.detector.start()

    async def stop(self):
        """Stop game management"""
        await self.detector.stop()

    def get_active_games(self) -> list[GameProfile]:
        """Get active games"""
        return self.detector.get_active_games()

    async def optimize_for_game(self, game_id: str):
        """Manually optimize for a specific game"""
        profile = self.detector.get_profile(game_id)
        if profile:
            await self.optimizer.apply_profile(
                profile, self.network_manager, self.broadcast_manager
            )

    async def on_game_detected(self, game_id: str):
        """Called when a game is detected - apply optimizations"""
        profile = self.detector.get_profile(game_id)
        if profile:
            await self.optimizer.apply_profile(
                profile, self.network_manager, self.broadcast_manager
            )

    def list_supported_games(self) -> list[GameProfile]:
        """List all supported games"""
        return list(GAME_PROFILES.values())
