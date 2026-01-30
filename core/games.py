"""Game detection and profiles"""

import asyncio
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

import psutil

from .config import Config


@dataclass
class GameProfile:
    """Profile for a specific game"""

    name: str
    executable: str  # Process name
    ports: List[int]  # Ports used by game
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


async def load_game_profiles() -> Dict[str, GameProfile]:
    """Load game profiles from JSON files organized by genre

    Returns:
        Dictionary mapping game_id to GameProfile
    """
    profiles: Dict[str, GameProfile] = {}

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

            async with aiofiles.open(json_file, "r", encoding="utf-8") as f:
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
GAME_PROFILES: Dict[str, GameProfile] = {}


async def initialize_game_profiles():
    """Initialize game profiles asynchronously"""
    global GAME_PROFILES
    GAME_PROFILES = await load_game_profiles()


class GameDetector:
    """Detects running games"""

    def __init__(self, config: Config):
        self.config = config
        self.detected_games: Set[str] = set()
        self.running = False
        self._game_manager = None  # Will be set by GameManager

        # Path for custom game profiles
        self.custom_profiles_path = Path(config.config_dir) / "game_profiles.json"

    async def start(self):
        """Start game detection"""
        self.running = True

        # Load custom profiles if they exist
        await self._load_custom_profiles()

        asyncio.create_task(self._detection_loop())

    async def _load_custom_profiles(self):
        """Load custom game profiles from file"""
        if self.custom_profiles_path.exists():
            try:
                import json

                with open(self.custom_profiles_path, "r") as f:
                    custom_data = json.load(f)

                # Parse and add custom profiles to GAME_PROFILES
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
                        print(f"Loaded custom profile: {game_id} - {profile.name}")
                    except (KeyError, TypeError) as e:
                        error_msg = str(e)
                        print(
                            f"Warning: Invalid profile data for {game_id}: {error_msg}"
                        )
                        continue

                print(
                    f"Loaded {len(custom_data)} custom profiles from {self.custom_profiles_path}"
                )
            except json.JSONDecodeError as e:
                error_msg = str(e)
                print(f"Warning: Could not parse custom profiles JSON: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                print(f"Warning: Could not load custom profiles: {error_msg}")

    async def stop(self):
        """Stop game detection"""
        self.running = False

    async def _detection_loop(self):
        """Continuously detect running games"""
        while self.running:
            await self._detect_games()
            await asyncio.sleep(5)  # Check every 5 seconds

    async def _detect_games(self):
        """Detect currently running games"""
        current_games = set()

        # Get all running processes
        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = proc.info["name"]

                # Check against game profiles
                for game_id, profile in GAME_PROFILES.items():
                    if proc_name.lower() == profile.executable.lower():
                        current_games.add(game_id)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

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

    async def _on_game_started(self, game_id: str):
        """Handle game started"""
        profile = GAME_PROFILES[game_id]
        print(f"🎮 Detected: {profile.name}")
        print(f"   Optimizing for {profile.name}...")

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

        # Clear active profile and reset to defaults
        if self.active_profile and self.active_profile.name == profile.name:
            print("   Resetting network configuration to defaults...")
            await self.clear_profile()
            print("   ✓ Configuration reset complete")

    def get_active_games(self) -> List[GameProfile]:
        """Get list of active games"""
        return [GAME_PROFILES[game_id] for game_id in self.detected_games]

    def get_profile(self, game_id: str) -> Optional[GameProfile]:
        """Get profile for a specific game"""
        return GAME_PROFILES.get(game_id)

    async def save_custom_profile(self, game_id: str, profile: GameProfile):
        """Save a custom game profile to disk"""
        try:
            import json

            custom_profiles = {}

            # Load existing profiles
            if self.custom_profiles_path.exists():
                with open(self.custom_profiles_path, "r") as f:
                    custom_profiles = json.load(f)

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
            with open(self.custom_profiles_path, "w") as f:
                json.dump(custom_profiles, f, indent=2)

            print(f"Saved custom profile for {profile.name}")
        except Exception as e:
            print(f"Error saving custom profile: {e}")


class GameOptimizer:
    """Applies game-specific optimizations"""

    def __init__(self, config: Config):
        self.config = config
        self.active_profile: Optional[GameProfile] = None

    async def apply_profile(
        self, profile: GameProfile, network_manager=None, broadcast_manager=None
    ):
        """Apply game profile optimizations

        Args:
            profile: Game profile to apply
            network_manager: NetworkManager instance for WireGuard config
            broadcast_manager: BroadcastManager instance for broadcast emulation
        """
        self.active_profile = profile

        # Store manager references for later reset
        self._network_manager_ref = network_manager
        self._broadcast_manager_ref = broadcast_manager

        print(f"⚙️  Applying optimizations for {profile.name}")

        # Adjust WireGuard keepalive
        if profile.keepalive != 25 and network_manager:
            print(f"   - Keepalive: {profile.keepalive}s")
            await self._update_keepalive(network_manager, profile.keepalive)

        # Enable broadcast emulation if needed
        if profile.broadcast and broadcast_manager:
            print("   - Broadcast emulation: ON")
            await self._enable_broadcast(broadcast_manager, profile)

        # Set packet priority
        if profile.packet_priority == "high":
            print("   - Packet priority: HIGH")
            await self._set_packet_priority(profile.packet_priority)

        # Adjust MTU if needed
        if profile.mtu != 1420 and network_manager:
            print(f"   - MTU: {profile.mtu}")
            await self._update_mtu(network_manager, profile.mtu)

        print(f"✓ Optimizations applied for {profile.name}")

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

    async def _enable_broadcast(self, broadcast_manager, profile: GameProfile):
        """Enable broadcast emulation for game ports"""
        try:
            # Start broadcast listeners for each game port
            for port in profile.ports:
                if profile.protocol in ("udp", "both"):
                    await broadcast_manager.start_listener(port, "udp")
                    print(f"   ✓ Broadcast listener started on UDP port {port}")
                if profile.protocol in ("tcp", "both"):
                    await broadcast_manager.start_listener(port, "tcp")
                    print(f"   ✓ Broadcast listener started on TCP port {port}")
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠ Failed to enable broadcast: {error_msg}")

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

            if result.returncode != 0:
                # Rule might already exist, check if it's a duplicate error
                if (
                    b"already exists" not in stderr
                    and b"Chain already exists" not in stderr
                ):
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

    async def _disable_broadcast(self, broadcast_manager, profile: GameProfile):
        """Disable broadcast emulation for game ports"""
        try:
            # Stop broadcast listeners for each game port
            for port in profile.ports:
                if profile.protocol in ("udp", "both"):
                    await broadcast_manager.stop_listener(port)
                    print(f"   ✓ Broadcast listener stopped on UDP port {port}")
                if profile.protocol in ("tcp", "both"):
                    await broadcast_manager.stop_listener(port)
                    print(f"   ✓ Broadcast listener stopped on TCP port {port}")
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠ Failed to disable broadcast: {error_msg}")


class GameManager:
    """Manages game detection and optimization"""

    def __init__(self, config: Config, network_manager=None, broadcast_manager=None):
        self.config = config
        self.detector = GameDetector(config)
        self.optimizer = GameOptimizer(config)
        self.network_manager = network_manager
        self.broadcast_manager = broadcast_manager

        # Hook up detector to optimizer
        self.detector._game_manager = self

    async def start(self):
        """Start game management"""
        await self.detector.start()

    async def stop(self):
        """Stop game management"""
        await self.detector.stop()

    def get_active_games(self) -> List[GameProfile]:
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

    def list_supported_games(self) -> List[GameProfile]:
        """List all supported games"""
        return list(GAME_PROFILES.values())
