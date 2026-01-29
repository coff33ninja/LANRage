# Game Detection and Profiles Documentation

The game detection system automatically detects running games and applies optimizations.

## Module: `core/games.py`

### Overview

The game system provides:
- Automatic game detection
- Game-specific optimization profiles
- Per-game network tuning
- Broadcast emulation configuration
- Custom profile support

### Data Classes

#### `GameProfile`

Profile for a specific game.

**Attributes**:
- `name` (str): Game name
- `executable` (str): Process name to detect
- `ports` (List[int]): Ports used by game
- `protocol` (str): "udp", "tcp", or "both"
- `broadcast` (bool): Uses broadcast discovery
- `multicast` (bool): Uses multicast discovery
- `keepalive` (int): WireGuard keepalive interval (seconds)
- `mtu` (int): Optimal MTU size
- `description` (str): Profile description
- `low_latency` (bool): Requires low latency
- `high_bandwidth` (bool): Requires high bandwidth
- `packet_priority` (str): "low", "medium", or "high"

**Example**:
```python
minecraft_profile = GameProfile(
    name="Minecraft Java Edition",
    executable="javaw.exe",
    ports=[25565],
    protocol="tcp",
    broadcast=True,
    multicast=False,
    keepalive=25,
    mtu=1420,
    description="Minecraft multiplayer",
    low_latency=True,
    high_bandwidth=False,
    packet_priority="high"
)
```

### Functions

#### `def load_game_profiles() -> Dict[str, GameProfile]`

Load game profiles from JSON files.

**Returns**: Dictionary mapping game_id to GameProfile

**Profile Locations**:
- `game_profiles/*.json` - Built-in profiles by genre
- `game_profiles/custom/*.json` - Custom profiles

**Profile Files**:
- `competitive.json` - FPS, MOBA, fighting games
- `coop.json` - Co-op games
- `party.json` - Party games
- `sandbox.json` - Sandbox/creative games
- `strategy.json` - RTS, turn-based strategy
- `survival.json` - Survival games

**Example**:
```python
profiles = load_game_profiles()
print(f"Loaded {len(profiles)} game profiles")

for game_id, profile in profiles.items():
    print(f"{profile.name}: {profile.ports}")
```

### Global Variable

#### `GAME_PROFILES: Dict[str, GameProfile]`

Dictionary of all loaded game profiles.

**Usage**:
```python
from core.games import GAME_PROFILES

minecraft = GAME_PROFILES.get("minecraft_java")
if minecraft:
    print(f"Minecraft ports: {minecraft.ports}")
```

### Class: `GameDetector`

Detects running games.

#### Initialization

```python
def __init__(self, config: Config):
    """
    Initialize game detector
    
    Args:
        config: LANrage configuration
    """
```

**Attributes**:
- `config`: Configuration object
- `detected_games`: Set of currently detected game IDs
- `running`: Detector running status
- `_game_manager`: Reference to GameManager
- `custom_profiles_path`: Path to custom profiles file

#### Core Methods

##### `async def start()`

Start game detection.

**Process**:
1. Load custom profiles
2. Set running flag
3. Start detection loop

**Example**:
```python
detector = GameDetector(config)
await detector.start()
```

##### `async def stop()`

Stop game detection.

**Process**:
1. Clear running flag
2. Stop detection loop

##### `def get_active_games() -> List[GameProfile]`

Get list of active games.

**Returns**: List of GameProfile objects for detected games

**Example**:
```python
active = detector.get_active_games()
for profile in active:
    print(f"Playing: {profile.name}")
```

##### `def get_profile(game_id: str) -> Optional[GameProfile]`

Get profile for a specific game.

**Parameters**:
- `game_id`: Game identifier

**Returns**: GameProfile or None

**Example**:
```python
profile = detector.get_profile("minecraft_java")
if profile:
    print(f"Ports: {profile.ports}")
```

##### `async def save_custom_profile(game_id: str, profile: GameProfile)`

Save a custom game profile.

**Parameters**:
- `game_id`: Unique game identifier
- `profile`: GameProfile to save

**File**: `~/.lanrage/game_profiles.json`

**Example**:
```python
custom_game = GameProfile(
    name="My Custom Game",
    executable="game.exe",
    ports=[12345],
    protocol="udp",
    broadcast=True,
    multicast=False,
    keepalive=25,
    mtu=1420,
    description="Custom game profile"
)

await detector.save_custom_profile("my_game", custom_game)
```

#### Internal Methods

##### `async def _detection_loop()`

Continuously detect running games.

**Process**:
1. Check every 5 seconds
2. Scan running processes
3. Match against game profiles
4. Detect new/stopped games
5. Trigger callbacks

##### `async def _detect_games()`

Detect currently running games.

**Process**:
1. Get all running processes
2. Match process names against profiles
3. Update detected_games set
4. Call _on_game_started for new games
5. Call _on_game_stopped for stopped games

##### `async def _on_game_started(game_id: str)`

Handle game started event.

**Parameters**:
- `game_id`: Game identifier

**Process**:
1. Log detection
2. Notify GameManager
3. Apply optimizations

##### `async def _on_game_stopped(game_id: str)`

Handle game stopped event.

**Parameters**:
- `game_id`: Game identifier

**Process**:
1. Log stop
2. Clear optimizations

##### `async def _load_custom_profiles()`

Load custom game profiles from file.

**File**: `~/.lanrage/game_profiles.json`

**Process**:
1. Check if file exists
2. Parse JSON
3. Create GameProfile objects
4. Add to GAME_PROFILES

### Class: `GameOptimizer`

Applies game-specific optimizations.

#### Initialization

```python
def __init__(self, config: Config):
    """
    Initialize game optimizer
    
    Args:
        config: LANrage configuration
    """
```

**Attributes**:
- `config`: Configuration object
- `active_profile`: Currently active GameProfile

#### Core Methods

##### `async def apply_profile(profile: GameProfile, network_manager=None, broadcast_manager=None)`

Apply game profile optimizations.

**Parameters**:
- `profile`: GameProfile to apply
- `network_manager`: NetworkManager instance (optional)
- `broadcast_manager`: BroadcastManager instance (optional)

**Optimizations Applied**:
1. Adjust WireGuard keepalive
2. Enable broadcast emulation
3. Set packet priority
4. Adjust MTU

**Example**:
```python
optimizer = GameOptimizer(config)
await optimizer.apply_profile(
    minecraft_profile,
    network_manager,
    broadcast_manager
)
```

##### `async def clear_profile()`

Clear active profile and reset to defaults.

**Process**:
1. Log clearing
2. Reset to default configuration
3. Clear active_profile

**Example**:
```python
await optimizer.clear_profile()
```

#### Internal Methods

##### `async def _update_keepalive(network_manager, keepalive: int)`

Update WireGuard keepalive interval.

**Parameters**:
- `network_manager`: NetworkManager instance
- `keepalive`: Keepalive interval in seconds

##### `async def _enable_broadcast(broadcast_manager, profile: GameProfile)`

Enable broadcast emulation for game ports.

**Parameters**:
- `broadcast_manager`: BroadcastManager instance
- `profile`: GameProfile with port information

**Process**:
1. Start listeners for each port
2. Configure protocol (UDP/TCP)

##### `async def _set_packet_priority(priority: str)`

Set packet priority (QoS/TOS bits) using platform-specific methods.

**Parameters**:
- `priority`: "low", "medium", or "high"

**DSCP Values**:
- low: 0 (CS0 - Best Effort)
- medium: 18 (CS2/AF21 - Standard)
- high: 46 (EF - Expedited Forwarding)

**Platform Support**:
- **Linux**: Uses iptables for DSCP marking + tc (Traffic Control) for bandwidth shaping
- **Windows**: Uses netsh QoS policies for DSCP marking
- **Other**: Gracefully skips QoS setup

**Linux Implementation**:
- iptables DSCP marking in mangle table
- tc HTB (Hierarchical Token Bucket) queueing
- Bandwidth guarantees based on priority:
  - High: 800mbit guaranteed, 1gbit ceiling
  - Medium: 500mbit guaranteed, 800mbit ceiling
  - Low: 100mbit guaranteed, 500mbit ceiling
- TOS-based packet filtering

**Windows Implementation**:
- netsh QoS policy creation
- DSCP marking on UDP protocol
- Requires administrator privileges

**Requirements**:
- Linux: sudo access for iptables/tc
- Windows: Administrator privileges for netsh
- Both: Respective tools must be available

##### `async def _set_qos_linux(dscp_value: int)`

Set QoS on Linux using iptables and tc (Traffic Control).

**Parameters**:
- `dscp_value`: DSCP value (0-63)

**Process**:
1. Check if iptables is available
2. Set DSCP marking on outgoing packets
3. Set up tc (Traffic Control) for bandwidth shaping
4. Create HTB qdisc and classes
5. Add filters for TOS-based routing

##### `async def _setup_tc_qos(interface: str, tos_value: int, dscp_value: int)`

Set up Linux Traffic Control (tc) for advanced QoS.

**Parameters**:
- `interface`: Network interface name
- `tos_value`: TOS value (DSCP << 2)
- `dscp_value`: DSCP value for priority mapping

**Process**:
1. Check if tc is available
2. Remove existing qdisc (cleanup)
3. Create HTB root qdisc
4. Create root class with maximum bandwidth
5. Create priority classes based on DSCP
6. Add filters to match TOS-marked packets

##### `async def _set_qos_windows(dscp_value: int)`

Set QoS on Windows using netsh and QoS policies.

**Parameters**:
- `dscp_value`: DSCP value (0-63)

**Process**:
1. Check if netsh is available
2. Remove existing policy if present
3. Create QoS policy with DSCP marking
4. Handle permission errors gracefully

##### `async def _update_mtu(network_manager, mtu: int)`

Update WireGuard interface MTU.

**Parameters**:
- `network_manager`: NetworkManager instance
- `mtu`: MTU size in bytes

### Class: `GameManager`

Manages game detection and optimization.

#### Initialization

```python
def __init__(self, config: Config, network_manager=None, broadcast_manager=None):
    """
    Initialize game manager
    
    Args:
        config: LANrage configuration
        network_manager: NetworkManager instance (optional)
        broadcast_manager: BroadcastManager instance (optional)
    """
```

**Attributes**:
- `config`: Configuration object
- `detector`: GameDetector instance
- `optimizer`: GameOptimizer instance
- `network_manager`: NetworkManager reference
- `broadcast_manager`: BroadcastManager reference

#### Core Methods

##### `async def start()`

Start game management.

**Process**:
1. Start game detector
2. Begin monitoring

**Example**:
```python
manager = GameManager(config, network_manager, broadcast_manager)
await manager.start()
```

##### `async def stop()`

Stop game management.

**Process**:
1. Stop game detector
2. Clear optimizations

##### `def get_active_games() -> List[GameProfile]`

Get active games.

**Returns**: List of GameProfile objects

##### `async def optimize_for_game(game_id: str)`

Manually optimize for a specific game.

**Parameters**:
- `game_id`: Game identifier

**Example**:
```python
await manager.optimize_for_game("minecraft_java")
```

##### `async def on_game_detected(game_id: str)`

Called when a game is detected.

**Parameters**:
- `game_id`: Game identifier

**Process**:
1. Get game profile
2. Apply optimizations

##### `def list_supported_games() -> List[GameProfile]`

List all supported games.

**Returns**: List of all GameProfile objects

**Example**:
```python
games = manager.list_supported_games()
for profile in games:
    print(f"{profile.name} - {profile.description}")
```

## Game Profile Format

### JSON Structure

```json
{
  "game_id": {
    "name": "Game Name",
    "executable": "game.exe",
    "ports": [25565, 25566],
    "protocol": "tcp",
    "broadcast": true,
    "multicast": false,
    "keepalive": 25,
    "mtu": 1420,
    "description": "Game description",
    "low_latency": true,
    "high_bandwidth": false,
    "packet_priority": "high"
  }
}
```

### Example Profiles

**Minecraft**:
```json
{
  "minecraft_java": {
    "name": "Minecraft Java Edition",
    "executable": "javaw.exe",
    "ports": [25565],
    "protocol": "tcp",
    "broadcast": true,
    "keepalive": 25,
    "mtu": 1420,
    "description": "Minecraft multiplayer",
    "low_latency": true,
    "packet_priority": "high"
  }
}
```

**Terraria**:
```json
{
  "terraria": {
    "name": "Terraria",
    "executable": "Terraria.exe",
    "ports": [7777],
    "protocol": "tcp",
    "broadcast": true,
    "keepalive": 25,
    "mtu": 1420,
    "description": "Terraria multiplayer",
    "low_latency": true,
    "packet_priority": "high"
  }
}
```

## Supported Games

See `game_profiles/` directory for full list. Categories include:
- Competitive (FPS, MOBA, fighting)
- Co-op (PvE, story-driven)
- Party (casual multiplayer)
- Sandbox (creative, building)
- Strategy (RTS, turn-based)
- Survival (crafting, exploration)

## Testing

### Unit Tests

```bash
python -c "
from core.games import GameManager, GAME_PROFILES
from core.config import Config
import asyncio

async def test():
    config = Config.load()
    manager = GameManager(config)
    
    await manager.start()
    print(f'✓ Game manager started')
    print(f'✓ Loaded {len(GAME_PROFILES)} profiles')
    
    # List supported games
    games = manager.list_supported_games()
    print(f'✓ {len(games)} games supported')
    
    await manager.stop()

asyncio.run(test())
"
```

## Future Enhancements

- Automatic profile creation
- Machine learning for optimization
- Cloud profile repository
- Community profiles
- Profile versioning
- A/B testing
- Performance analytics
