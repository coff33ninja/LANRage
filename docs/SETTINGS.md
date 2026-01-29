# Settings System Documentation

LANrage uses SQLite for persistent settings storage with async operations.

## Module: `core/settings.py`

### Overview

The settings system provides:
- Persistent configuration storage
- Async database operations
- Multiple configuration profiles
- Favorite servers management
- Custom game profiles
- Database integrity validation

### Class: `SettingsDatabase`

#### Initialization

```python
def __init__(self, db_path: Path):
    """
    Initialize settings database
    
    Args:
        db_path: Path to SQLite database file
    """
```

**Attributes**:
- `db_path`: Path to database file
- `_lock`: Asyncio lock for thread-safe operations

**Database Location**: `~/.lanrage/settings.db`

#### Core Methods

##### `async def initialize()`

Initialize database schema.

**Creates Tables**:
1. `settings`: Key-value settings storage
2. `server_configs`: Saved server configurations
3. `favorite_servers`: Favorite game servers
4. `game_profiles`: Custom game profiles

**Schema**:
```sql
-- Settings table
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    type TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Server configurations
CREATE TABLE server_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mode TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    config TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Favorite servers
CREATE TABLE favorite_servers (
    server_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    game TEXT NOT NULL,
    address TEXT NOT NULL,
    added_at TEXT NOT NULL
);

-- Game profiles
CREATE TABLE game_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    game TEXT NOT NULL,
    profile TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**Example**:
```python
db = SettingsDatabase(Path.home() / ".lanrage" / "settings.db")
await db.initialize()
```

### Settings Management

##### `async def get_setting(key: str, default: Any = None) -> Any`

Get a setting value.

**Parameters**:
- `key`: Setting key
- `default`: Default value if not found

**Returns**: Setting value (deserialized) or default

**Example**:
```python
mode = await db.get_setting("mode", "client")
api_port = await db.get_setting("api_port", 8666)
```

##### `async def set_setting(key: str, value: Any)`

Set a setting value.

**Parameters**:
- `key`: Setting key
- `value`: Setting value (any JSON-serializable type)

**Supported Types**:
- `bool`: True/False
- `int`: Integer numbers
- `float`: Floating point numbers
- `str`: Text strings
- `dict`: JSON objects
- `list`: JSON arrays

**Example**:
```python
await db.set_setting("mode", "client")
await db.set_setting("api_port", 8666)
await db.set_setting("peer_name", "Player1")
await db.set_setting("features", {"discord": True, "metrics": True})
```

##### `async def get_all_settings() -> dict[str, Any]`

Get all settings as dictionary.

**Returns**: Dictionary of all settings

**Example**:
```python
settings = await db.get_all_settings()
print(f"Mode: {settings['mode']}")
print(f"Port: {settings['api_port']}")
```

##### `async def delete_setting(key: str)`

Delete a setting.

**Parameters**:
- `key`: Setting key to delete

**Example**:
```python
await db.delete_setting("old_setting")
```

### Server Configurations

##### `async def save_server_config(name: str, mode: str, config: dict) -> int`

Save a server configuration.

**Parameters**:
- `name`: Configuration name
- `mode`: "client" or "relay"
- `config`: Configuration dictionary

**Returns**: Configuration ID

**Example**:
```python
config_id = await db.save_server_config(
    name="Gaming Setup",
    mode="client",
    config={
        "peer_name": "Player1",
        "api_port": 8666,
        "enable_discord": True
    }
)
```

##### `async def get_server_config(config_id: int) -> Optional[dict]`

Get a server configuration.

**Parameters**:
- `config_id`: Configuration ID

**Returns**: Configuration dict or None

**Example**:
```python
config = await db.get_server_config(1)
if config:
    print(f"Name: {config['name']}")
    print(f"Mode: {config['mode']}")
    print(f"Config: {config['config']}")
```

##### `async def get_all_server_configs() -> list[dict]`

Get all server configurations.

**Returns**: List of configuration dicts

**Example**:
```python
configs = await db.get_all_server_configs()
for config in configs:
    print(f"{config['name']} ({config['mode']})")
```

##### `async def update_server_config(config_id: int, config: dict)`

Update a server configuration.

**Parameters**:
- `config_id`: Configuration ID
- `config`: New configuration dictionary

**Example**:
```python
await db.update_server_config(1, {
    "peer_name": "Player2",
    "api_port": 8667
})
```

##### `async def delete_server_config(config_id: int)`

Delete a server configuration.

**Parameters**:
- `config_id`: Configuration ID

**Example**:
```python
await db.delete_server_config(1)
```

##### `async def toggle_server_config(config_id: int, enabled: bool)`

Enable or disable a server configuration.

**Parameters**:
- `config_id`: Configuration ID
- `enabled`: True to enable, False to disable

**Example**:
```python
await db.toggle_server_config(1, False)  # Disable
await db.toggle_server_config(1, True)   # Enable
```

### Favorite Servers

##### `async def add_favorite_server(server_id: str, name: str, game: str, address: str)`

Add a server to favorites.

**Parameters**:
- `server_id`: Unique server identifier
- `name`: Server name
- `game`: Game name
- `address`: Server address (IP:port)

**Example**:
```python
await db.add_favorite_server(
    server_id="server123",
    name="Epic PvP Server",
    game="Minecraft",
    address="10.66.0.2:25565"
)
```

##### `async def remove_favorite_server(server_id: str)`

Remove a server from favorites.

**Parameters**:
- `server_id`: Server identifier

**Example**:
```python
await db.remove_favorite_server("server123")
```

##### `async def get_favorite_servers() -> list[dict]`

Get all favorite servers.

**Returns**: List of favorite server dicts

**Example**:
```python
favorites = await db.get_favorite_servers()
for server in favorites:
    print(f"{server['name']} - {server['game']}")
```

##### `async def is_favorite(server_id: str) -> bool`

Check if a server is in favorites.

**Parameters**:
- `server_id`: Server identifier

**Returns**: True if favorite, False otherwise

**Example**:
```python
if await db.is_favorite("server123"):
    print("Server is favorited")
```

### Game Profiles

##### `async def save_game_profile(name: str, game: str, profile: dict) -> int`

Save a custom game profile.

**Parameters**:
- `name`: Profile name (unique)
- `game`: Game name
- `profile`: Profile configuration dict

**Returns**: Profile ID

**Example**:
```python
profile_id = await db.save_game_profile(
    name="Minecraft Optimized",
    game="Minecraft",
    profile={
        "mtu": 1420,
        "keepalive": 25,
        "ports": [25565],
        "broadcast": True
    }
)
```

##### `async def get_game_profile(name: str) -> Optional[dict]`

Get a game profile.

**Parameters**:
- `name`: Profile name

**Returns**: Profile dict or None

**Example**:
```python
profile = await db.get_game_profile("Minecraft Optimized")
if profile:
    print(f"Game: {profile['game']}")
    print(f"Config: {profile['profile']}")
```

##### `async def get_all_game_profiles() -> list[dict]`

Get all game profiles.

**Returns**: List of profile dicts

**Example**:
```python
profiles = await db.get_all_game_profiles()
for profile in profiles:
    print(f"{profile['name']} - {profile['game']}")
```

##### `async def delete_game_profile(name: str)`

Delete a game profile.

**Parameters**:
- `name`: Profile name

**Example**:
```python
await db.delete_game_profile("Minecraft Optimized")
```

### Database Maintenance

##### `def validate_database_integrity() -> bool`

Validate database integrity using synchronous sqlite3.

**Returns**: True if database is valid, False otherwise

**Usage**: Startup checks and diagnostics

**Example**:
```python
if db.validate_database_integrity():
    print("Database OK")
else:
    print("Database corrupted!")
```

##### `def get_database_size() -> int`

Get database file size in bytes.

**Returns**: Database size in bytes

**Example**:
```python
size = db.get_database_size()
print(f"Database size: {size / 1024:.2f} KB")
```

##### `def backup_database(backup_path: Path) -> bool`

Create a backup of the database.

**Parameters**:
- `backup_path`: Path where backup should be created

**Returns**: True if backup successful, False otherwise

**Example**:
```python
backup_path = Path.home() / ".lanrage" / "backups" / "settings_backup.db"
if db.backup_database(backup_path):
    print("Backup created successfully")
```

### Helper Methods

##### `def _serialize(value: Any) -> tuple[str, str]`

Serialize a value for storage.

**Parameters**:
- `value`: Value to serialize

**Returns**: Tuple of (serialized_value, type_name)

**Type Mapping**:
- `bool` → "bool"
- `int` → "int"
- `float` → "float"
- `str` → "str"
- `dict/list` → "json"

##### `def _deserialize(value: str, value_type: str) -> Any`

Deserialize a value from storage.

**Parameters**:
- `value`: Serialized value string
- `value_type`: Type name

**Returns**: Deserialized value

## Global Functions

### `async def get_settings_db() -> SettingsDatabase`

Get the global settings database instance.

**Returns**: Singleton SettingsDatabase instance

**Example**:
```python
db = await get_settings_db()
mode = await db.get_setting("mode")
```

### `async def init_default_settings()`

Initialize default settings if not present.

**Default Settings**:
- `mode`: "client"
- `peer_name`: "Player"
- `api_host`: "127.0.0.1"
- `api_port`: 8666
- `virtual_subnet`: "10.66.0.0/16"
- `interface_name`: "lanrage0"
- `wireguard_keepalive`: 25
- `control_server`: "https://control.lanrage.io"
- `relay_port`: 51820
- `auto_optimize_games`: True
- `enable_broadcast`: True
- `enable_discord`: False
- `enable_metrics`: True

**Example**:
```python
await init_default_settings()
```

## Integration with Config

### Loading from Database

```python
from core.config import Config

# Load config from database
config = await Config.load_from_db()
```

**Fallback**: If database fails, falls back to environment variables

## Web UI Integration

### Settings Page

**URL**: http://localhost:8666/settings.html

**Features**:
- Mode selection (Client/Relay)
- All configuration options
- Save/load multiple configurations
- Reset to defaults
- Real-time validation

### API Endpoints

**Get Settings**:
```http
GET /api/settings
```

**Update Settings**:
```http
POST /api/settings
Content-Type: application/json

{
  "mode": "client",
  "peer_name": "Player1",
  "api_port": 8666
}
```

**Reset Settings**:
```http
POST /api/settings/reset
```

**List Configurations**:
```http
GET /api/settings/configs
```

**Save Configuration**:
```http
POST /api/settings/configs
Content-Type: application/json

{
  "name": "Gaming Setup",
  "mode": "client",
  "config": { /* settings */ }
}
```

**Delete Configuration**:
```http
DELETE /api/settings/configs/{config_id}
```

## Thread Safety

The settings database uses `asyncio.Lock()` for thread-safe concurrent access:

```python
async with self._lock:
    # Database operations
    pass
```

This ensures:
- No race conditions
- Consistent reads/writes
- Safe concurrent access

## Performance

- **Read operations**: <1ms
- **Write operations**: <5ms
- **Database size**: ~100KB for typical usage
- **Concurrent access**: Thread-safe with asyncio lock

## Security

- **Local storage**: Database stored in user's home directory
- **No encryption**: Settings are not sensitive (no passwords)
- **File permissions**: Relies on OS file permissions
- **No network access**: Database is local only

## Troubleshooting

### "Database locked"

**Cause**: Concurrent access without proper locking

**Solution**: Use `async with self._lock` for all operations

### "Database corrupted"

**Cause**: Disk failure, power loss, or improper shutdown

**Solution**:
```python
if not db.validate_database_integrity():
    # Restore from backup
    backup_path = Path.home() / ".lanrage" / "backups" / "settings_backup.db"
    shutil.copy(backup_path, db.db_path)
```

### "Settings not persisting"

**Cause**: Database not initialized or write failure

**Solution**:
- Check database file exists
- Verify write permissions
- Check disk space

## Testing

### Unit Tests

```bash
python -c "
from core.settings import SettingsDatabase
from pathlib import Path
import asyncio

async def test():
    db = SettingsDatabase(Path('test.db'))
    await db.initialize()
    
    # Test settings
    await db.set_setting('test_key', 'test_value')
    value = await db.get_setting('test_key')
    assert value == 'test_value'
    
    print('✓ Settings test passed')

asyncio.run(test())
"
```

## Future Enhancements

- Settings encryption for sensitive data
- Settings sync across devices
- Settings import/export
- Settings versioning
- Settings migration tools
- Settings validation schemas
