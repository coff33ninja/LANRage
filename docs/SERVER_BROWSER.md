# Server Browser

The server browser (`core/server_browser.py`) provides game server discovery, registration, and browsing functionality for LANrage parties.

## Overview

The `ServerBrowser` class enables:
- **Server Registration**: Hosts can advertise game servers
- **Server Discovery**: Players can browse available servers
- **Filtering**: Search by game, player count, tags, etc.
- **Favorites**: Save favorite servers
- **Latency Measurement**: Ping servers to check responsiveness
- **Automatic Cleanup**: Remove expired/stale servers

---

## Classes

### GameServer

Represents a game server in the browser.

**Attributes:**
- `id` (str): Unique server identifier
- `name` (str): Server name
- `game` (str): Game name
- `host_peer_id` (str): Host peer ID
- `host_peer_name` (str): Host peer name
- `host_ip` (str): Host virtual IP address
- `max_players` (int): Maximum player capacity
- `current_players` (int): Current player count
- `map_name` (Optional[str]): Current map name
- `game_mode` (Optional[str]): Game mode (e.g., "Survival", "Creative")
- `password_protected` (bool): Whether server requires password
- `tags` (list[str]): Server tags for filtering (e.g., ["PvP", "Modded"])
- `created_at` (float): Server creation timestamp
- `last_heartbeat` (float): Last heartbeat timestamp
- `latency_ms` (Optional[float]): Measured latency in milliseconds

#### Methods

##### to_dict()

Convert server to dictionary.

```python
server_dict = server.to_dict()
```

**Returns:** dict with all server attributes plus:
- `is_full` (bool): Whether server is at capacity
- `age_seconds` (float): Seconds since server creation

---

##### is_expired(timeout)

Check if server heartbeat has expired.

```python
expired = server.is_expired(timeout=60)
```

**Parameters:**
- `timeout` (int): Timeout in seconds (default: 60)

**Returns:** bool - True if last heartbeat exceeds timeout

---

##### update_heartbeat()

Update last heartbeat timestamp.

```python
server.update_heartbeat()
```

**Behavior:**
- Sets `last_heartbeat` to current time
- Prevents server from being marked as expired

**Returns:** None

---

## ServerBrowser

Main server browser class.

### Initialization

```python
from core.config import Config
from core.server_browser import ServerBrowser

config = await Config.load()
browser = ServerBrowser(config)
```

**Parameters:**
- `config` (Config): LANrage configuration

**Attributes:**
- `servers` (dict[str, GameServer]): Active servers by ID
- `favorites` (set[str]): Set of favorited server IDs
- `running` (bool): Whether browser is active

---

### Methods

#### start()

Start server browser.

```python
await browser.start()
```

**Behavior:**
- Starts cleanup task (removes expired servers every 30 seconds)
- Prints confirmation message

**Returns:** None

---

#### stop()

Stop server browser.

```python
await browser.stop()
```

**Behavior:**
- Stops cleanup task
- Preserves server data in memory

**Returns:** None

---

#### register_server(...)

Register a new game server.

```python
server = await browser.register_server(
    server_id="minecraft-server-1",
    name="Alice's Minecraft Server",
    game="Minecraft",
    host_peer_id="peer-123",
    host_peer_name="Alice",
    host_ip="10.66.0.2",
    max_players=8,
    current_players=2,
    map_name="World 1",
    game_mode="Survival",
    password_protected=False,
    tags=["Vanilla", "PvE"]
)
```

**Parameters:**
- `server_id` (str): Unique server identifier
- `name` (str): Server name
- `game` (str): Game name
- `host_peer_id` (str): Host peer ID
- `host_peer_name` (str): Host peer name
- `host_ip` (str): Host IP address
- `max_players` (int): Maximum players
- `current_players` (int): Current player count (default: 0)
- `map_name` (Optional[str]): Current map name
- `game_mode` (Optional[str]): Game mode
- `password_protected` (bool): Password required (default: False)
- `tags` (Optional[list[str]]): Server tags

**Behavior:**
- Creates new `GameServer` instance if not exists
- Updates existing server if already registered
- Updates heartbeat timestamp
- Prints confirmation message

**Returns:** GameServer instance

---

#### unregister_server(server_id)

Unregister a game server.

```python
success = await browser.unregister_server("minecraft-server-1")
```

**Parameters:**
- `server_id` (str): Server ID to unregister

**Behavior:**
- Removes server from browser
- Prints confirmation message

**Returns:** bool - True if server was unregistered, False if not found

---

#### update_heartbeat(server_id)

Update server heartbeat.

```python
success = await browser.update_heartbeat("minecraft-server-1")
```

**Parameters:**
- `server_id` (str): Server ID

**Behavior:**
- Updates `last_heartbeat` timestamp
- Prevents server from expiring

**Returns:** bool - True if updated, False if server not found

**Note:** Hosts should call this every 30-60 seconds to keep server active.

---

#### update_player_count(server_id, current_players)

Update server player count.

```python
success = await browser.update_player_count("minecraft-server-1", 5)
```

**Parameters:**
- `server_id` (str): Server ID
- `current_players` (int): Current player count

**Behavior:**
- Updates `current_players` attribute
- Updates heartbeat timestamp

**Returns:** bool - True if updated, False if server not found

---

#### get_server(server_id)

Get server by ID.

```python
server = browser.get_server("minecraft-server-1")
```

**Parameters:**
- `server_id` (str): Server ID

**Returns:** Optional[GameServer] - Server instance or None if not found

---

#### list_servers(...)

List servers with optional filtering.

```python
servers = browser.list_servers(
    game="Minecraft",
    hide_full=True,
    hide_empty=False,
    hide_password=True,
    tags=["Vanilla"],
    search="Alice"
)
```

**Parameters:**
- `game` (Optional[str]): Filter by game name (case-insensitive)
- `hide_full` (bool): Hide full servers (default: False)
- `hide_empty` (bool): Hide empty servers (default: False)
- `hide_password` (bool): Hide password-protected servers (default: False)
- `tags` (Optional[list[str]]): Filter by tags (any match)
- `search` (Optional[str]): Search in server name, game, or host name

**Behavior:**
- Applies all filters in sequence
- Sorts by player count (descending), then by name

**Returns:** list[GameServer] - Filtered and sorted server list

---

#### get_games_list()

Get list of unique games with active servers.

```python
games = browser.get_games_list()
```

**Returns:** list[str] - Sorted list of game names

---

#### add_favorite(server_id)

Add server to favorites.

```python
browser.add_favorite("minecraft-server-1")
```

**Parameters:**
- `server_id` (str): Server ID to favorite

**Behavior:**
- Adds server ID to favorites set
- Persists across sessions (when integrated with settings database)

**Returns:** None

---

#### remove_favorite(server_id)

Remove server from favorites.

```python
browser.remove_favorite("minecraft-server-1")
```

**Parameters:**
- `server_id` (str): Server ID to unfavorite

**Returns:** None

---

#### is_favorite(server_id)

Check if server is favorited.

```python
favorited = browser.is_favorite("minecraft-server-1")
```

**Parameters:**
- `server_id` (str): Server ID

**Returns:** bool - True if favorited, False otherwise

---

#### get_favorites()

Get list of favorite servers.

```python
favorites = browser.get_favorites()
```

**Returns:** list[GameServer] - List of favorited servers (only active servers)

---

#### measure_latency(server_id)

Measure latency to a server.

```python
latency = await browser.measure_latency("minecraft-server-1")
```

**Parameters:**
- `server_id` (str): Server ID

**Behavior:**
- Uses ICMP ping to measure latency
- Parses ping output for accurate measurement
- Updates server's `latency_ms` attribute
- Timeout: 2 seconds

**Returns:** Optional[float] - Latency in milliseconds, or None if measurement failed

**Platform Support:**
- Windows: Uses `ping -n 1`
- Linux/Mac: Uses `ping -c 1`

---

#### get_stats()

Get server browser statistics.

```python
stats = browser.get_stats()
```

**Returns:** dict with structure:
```python
{
    "total_servers": 15,
    "total_players": 42,
    "unique_games": 5,
    "games": ["Minecraft", "Terraria", "Valheim", ...],
    "favorites": 3
}
```

---

## Usage Examples

### Basic Server Registration

```python
from core.config import Config
from core.server_browser import ServerBrowser

# Initialize
config = await Config.load()
browser = ServerBrowser(config)
await browser.start()

# Register server
server = await browser.register_server(
    server_id="my-server-1",
    name="My Awesome Server",
    game="Minecraft",
    host_peer_id="peer-123",
    host_peer_name="Alice",
    host_ip="10.66.0.2",
    max_players=10,
    current_players=2,
    tags=["Vanilla", "PvE"]
)

# Keep server alive with heartbeats
while True:
    await asyncio.sleep(30)
    await browser.update_heartbeat("my-server-1")
```

### Server Discovery

```python
# List all servers
all_servers = browser.list_servers()

# Filter by game
minecraft_servers = browser.list_servers(game="Minecraft")

# Hide full servers
available_servers = browser.list_servers(hide_full=True)

# Search by name
alice_servers = browser.list_servers(search="Alice")

# Filter by tags
pvp_servers = browser.list_servers(tags=["PvP"])

# Complex filtering
servers = browser.list_servers(
    game="Minecraft",
    hide_full=True,
    hide_empty=True,
    hide_password=True,
    tags=["Vanilla", "PvE"],
    search="survival"
)

# Display results
for server in servers:
    print(f"{server.name} - {server.current_players}/{server.max_players} players")
```

### Favorites Management

```python
# Add to favorites
browser.add_favorite("minecraft-server-1")

# Check if favorited
if browser.is_favorite("minecraft-server-1"):
    print("Server is favorited!")

# Get all favorites
favorites = browser.get_favorites()
for server in favorites:
    print(f"⭐ {server.name}")

# Remove from favorites
browser.remove_favorite("minecraft-server-1")
```

### Latency Measurement

```python
# Measure latency to server
latency = await browser.measure_latency("minecraft-server-1")
if latency:
    print(f"Latency: {latency:.1f}ms")
else:
    print("Failed to measure latency")

# Measure latency to all servers
for server in browser.list_servers():
    latency = await browser.measure_latency(server.id)
    if latency:
        print(f"{server.name}: {latency:.1f}ms")
```

### Server Updates

```python
# Update player count
await browser.update_player_count("my-server-1", 5)

# Update server details (re-register)
await browser.register_server(
    server_id="my-server-1",
    name="My Awesome Server [UPDATED]",
    game="Minecraft",
    host_peer_id="peer-123",
    host_peer_name="Alice",
    host_ip="10.66.0.2",
    max_players=10,
    current_players=5,
    map_name="New World",
    game_mode="Creative",
    tags=["Vanilla", "Creative"]
)
```

### Statistics

```python
# Get browser stats
stats = browser.get_stats()
print(f"Total servers: {stats['total_servers']}")
print(f"Total players: {stats['total_players']}")
print(f"Games: {', '.join(stats['games'])}")

# Get games list
games = browser.get_games_list()
for game in games:
    servers = browser.list_servers(game=game)
    print(f"{game}: {len(servers)} servers")
```

---

## Integration with API

The server browser integrates with the REST API (`api/server.py`):

### Endpoints

- `GET /api/servers` - List servers with filtering
- `POST /api/servers` - Register server
- `GET /api/servers/{server_id}` - Get server details
- `DELETE /api/servers/{server_id}` - Unregister server
- `POST /api/servers/{server_id}/heartbeat` - Update heartbeat
- `POST /api/servers/{server_id}/players` - Update player count
- `POST /api/servers/{server_id}/join` - Join server
- `POST /api/servers/{server_id}/favorite` - Add to favorites
- `DELETE /api/servers/{server_id}/favorite` - Remove from favorites
- `GET /api/servers/{server_id}/latency` - Measure latency
- `GET /api/servers/stats` - Get browser statistics
- `GET /api/games` - List games

See `docs/API.md` for full API documentation.

---

## Automatic Cleanup

The browser automatically removes expired servers:

- **Cleanup Interval**: Every 30 seconds
- **Expiration Timeout**: 90 seconds (no heartbeat)
- **Behavior**: Silently removes expired servers

**Best Practice:** Hosts should send heartbeats every 30-60 seconds.

---

## Performance Characteristics

### Memory Usage

- **Per Server**: ~1KB (metadata only)
- **1000 Servers**: ~1MB
- **Typical Usage**: <100KB (10-20 servers)

### CPU Usage

- **Registration**: <0.1ms per server
- **Filtering**: <1ms for 100 servers
- **Cleanup**: <1ms per cleanup cycle
- **Latency Measurement**: 1-2 seconds (blocking ping)

---

## Future Enhancements

1. **Persistent Storage**: Save favorites to database
2. **Server History**: Track server uptime and reliability
3. **Player Tracking**: Track which players are on which servers
4. **Server Ratings**: Allow players to rate servers
5. **Automatic Join**: One-click join to server's party
6. **Server Announcements**: Broadcast server events
7. **Mod/Plugin Detection**: Detect and display server mods
8. **Region Filtering**: Filter by geographic region
9. **Server Rules**: Display server rules and policies
10. **Ban Lists**: Share ban lists between servers
