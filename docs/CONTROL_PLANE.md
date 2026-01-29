# Control Plane Documentation

The control plane handles peer discovery, party management, and connection coordination.

## Module: `core/control.py`

### Overview

The control plane provides:
- Party registration and discovery
- Peer information storage and exchange
- Heartbeat monitoring
- State persistence
- Local and remote modes

### Data Classes

#### `PeerInfo`

Information about a peer in the network.

**Attributes**:
- `peer_id` (str): Unique peer identifier
- `name` (str): Display name
- `public_key` (str): WireGuard public key (base64)
- `nat_type` (str): NAT type ("open", "full_cone", etc.)
- `public_ip` (str): Public IP address
- `public_port` (int): Public port
- `local_ip` (str): Local IP address
- `local_port` (int): Local port
- `last_seen` (datetime): Last heartbeat timestamp

**Methods**:
- `to_dict()`: Convert to dictionary
- `from_dict(data)`: Create from dictionary
- `validate_nat_type()`: Validate NAT type is valid
- `get_nat_type_enum()`: Get NAT type as enum

**Example**:
```python
peer_info = PeerInfo(
    peer_id="peer123",
    name="Alice",
    public_key="base64_key...",
    nat_type="full_cone",
    public_ip="203.0.113.42",
    public_port=51820,
    local_ip="192.168.1.100",
    local_port=51820,
    last_seen=datetime.now()
)
```

#### `PartyInfo`

Information about a gaming party.

**Attributes**:
- `party_id` (str): Unique party identifier
- `name` (str): Party name
- `host_id` (str): Host peer ID
- `created_at` (datetime): Creation timestamp
- `peers` (Dict[str, PeerInfo]): Dictionary of peers

**Methods**:
- `to_dict()`: Convert to dictionary
- `from_dict(data)`: Create from dictionary
- `generate_party_id()`: Generate secure random party ID

**Example**:
```python
party = PartyInfo(
    party_id="party_abc123",
    name="Gaming Night",
    host_id="peer123",
    created_at=datetime.now(),
    peers={"peer123": peer_info}
)
```

### Class: `ControlPlane`

Base control plane implementation.

#### Initialization

```python
def __init__(self, config: Config):
    """
    Initialize control plane
    
    Args:
        config: LANrage configuration
    """
```

**Attributes**:
- `config`: Configuration object
- `parties`: Dictionary of parties by ID
- `my_peer_id`: Current peer ID
- `my_party_id`: Current party ID
- `active_party_ids`: Set of active party IDs
- `state_file`: Path to state persistence file

#### Core Methods

##### `async def initialize()`

Initialize control plane.

**Process**:
1. Load persisted state from disk
2. Start cleanup task for stale peers

**Example**:
```python
control = ControlPlane(config)
await control.initialize()
```

##### `async def register_party(party_id: str, name: str, host_peer_info: PeerInfo) -> PartyInfo`

Register a new party.

**Parameters**:
- `party_id`: Unique party identifier
- `name`: Party name
- `host_peer_info`: Host peer information

**Returns**: Created PartyInfo

**Example**:
```python
party = await control.register_party(
    party_id="party_abc123",
    name="Gaming Night",
    host_peer_info=my_peer_info
)
```

##### `async def join_party(party_id: str, peer_info: PeerInfo) -> PartyInfo`

Join an existing party.

**Parameters**:
- `party_id`: Party ID to join
- `peer_info`: Your peer information

**Returns**: PartyInfo with all peers

**Raises**: `ControlPlaneError` if party not found

**Example**:
```python
party = await control.join_party("party_abc123", my_peer_info)
print(f"Joined {party.name} with {len(party.peers)} peers")
```

##### `async def leave_party(party_id: str, peer_id: str)`

Leave a party.

**Parameters**:
- `party_id`: Party ID
- `peer_id`: Your peer ID

**Behavior**:
- Removes peer from party
- Deletes party if host leaves or no peers remain
- Saves state to disk

**Example**:
```python
await control.leave_party("party_abc123", "peer123")
```

##### `async def update_peer(party_id: str, peer_info: PeerInfo)`

Update peer information.

**Parameters**:
- `party_id`: Party ID
- `peer_info`: Updated peer information

**Updates**:
- Peer information
- Last seen timestamp
- Saves state to disk

**Example**:
```python
await control.update_peer("party_abc123", updated_peer_info)
```

##### `async def get_party(party_id: str) -> Optional[PartyInfo]`

Get party information.

**Parameters**:
- `party_id`: Party ID

**Returns**: PartyInfo or None if not found

**Example**:
```python
party = await control.get_party("party_abc123")
if party:
    print(f"Party: {party.name}")
```

##### `async def get_peers(party_id: str) -> Dict[str, PeerInfo]`

Get all peers in a party.

**Parameters**:
- `party_id`: Party ID

**Returns**: Dictionary of peers by ID

**Example**:
```python
peers = await control.get_peers("party_abc123")
for peer_id, peer in peers.items():
    print(f"{peer.name}: {peer.public_ip}")
```

##### `async def discover_peer(party_id: str, peer_id: str) -> Optional[PeerInfo]`

Discover a specific peer.

**Parameters**:
- `party_id`: Party ID
- `peer_id`: Peer ID to discover

**Returns**: PeerInfo or None if not found

**Example**:
```python
peer = await control.discover_peer("party_abc123", "peer456")
if peer:
    print(f"Found {peer.name} at {peer.public_ip}")
```

##### `async def heartbeat(party_id: str, peer_id: str)`

Send heartbeat to keep peer alive.

**Parameters**:
- `party_id`: Party ID
- `peer_id`: Your peer ID

**Behavior**:
- Updates last_seen timestamp
- Prevents peer from being cleaned up

**Example**:
```python
# Send heartbeat every 30 seconds
while True:
    await control.heartbeat("party_abc123", "peer123")
    await asyncio.sleep(30)
```

#### Internal Methods

##### `async def _cleanup_task()`

Background task to clean up stale peers and parties.

**Behavior**:
- Runs every 60 seconds
- Removes peers inactive for >5 minutes
- Removes empty parties
- Saves state after cleanup

##### `async def _save_state()`

Save state to disk.

**File**: `~/.lanrage/control_state.json`

**Content**:
- All parties with peers
- Current peer ID
- Current party ID

##### `async def _load_state()`

Load state from disk.

**Behavior**:
- Loads persisted parties
- Restores peer and party IDs
- Handles corrupted files gracefully

### Class: `LocalControlPlane`

Local-only control plane for testing and same-LAN scenarios.

**Extends**: `ControlPlane`

#### Additional Features

- File-based party discovery
- Shared discovery file for local peers
- No network communication required

#### Additional Methods

##### `async def _announce_party(party: PartyInfo)`

Announce party on local network.

**File**: `~/.lanrage/discovery.json`

**Behavior**:
- Writes party info to shared file
- Other local instances can discover party
- Updates on party changes

##### `async def discover_parties() -> Dict[str, PartyInfo]`

Discover parties on local network.

**Returns**: Dictionary of parties by ID

**Example**:
```python
local_control = LocalControlPlane(config)
await local_control.initialize()

parties = await local_control.discover_parties()
for party_id, party in parties.items():
    print(f"{party.name}: {len(party.peers)} peers")
```

### Class: `RemoteControlPlane`

Remote control plane client for production use.

**Extends**: `ControlPlane`

#### Additional Attributes

- `server_url`: Control server URL
- `ws`: WebSocket connection
- `connected`: Connection status
- `reconnect_attempts`: Reconnection counter
- `max_reconnect_attempts`: Maximum reconnection attempts (5)
- `reconnect_delay`: Delay between reconnections (5s)

#### Additional Methods

##### `async def _connect()`

Connect to control server via WebSocket.

**Process**:
1. Convert HTTP(S) URL to WebSocket URL
2. Connect with timeout (10s)
3. Start message handler
4. Send authentication

**Raises**: `ControlPlaneError` if connection fails

##### `async def _authenticate()`

Authenticate with control server.

**Currently**: Sends hello message  
**Future**: Implement proper authentication

##### `async def _handle_messages()`

Handle incoming messages from control server.

**Message Types**:
- `party_update`: Party information changed
- `peer_joined`: New peer joined party
- `peer_left`: Peer left party
- `signal`: WebRTC-style signaling
- `error`: Server error message

##### `async def _reconnect()`

Attempt to reconnect to control server.

**Behavior**:
- Tries up to 5 times
- 5-second delay between attempts
- Falls back to local mode on failure

##### `async def close()`

Close connection to control server.

**Behavior**:
- Sets connected flag to false
- Closes WebSocket connection
- Cleans up resources

### Exception: `ControlPlaneError`

Custom exception for control plane errors.

**Usage**:
```python
try:
    party = await control.join_party("invalid_id", peer_info)
except ControlPlaneError as e:
    print(f"Failed to join party: {e}")
```

### Factory Function

##### `def create_control_plane(config: Config) -> ControlPlane`

Factory function to create appropriate control plane.

**Logic**:
- If `control_server` configured → RemoteControlPlane
- Otherwise → LocalControlPlane

**Example**:
```python
control = create_control_plane(config)
await control.initialize()
```

## State Persistence

### Control State File

**Location**: `~/.lanrage/control_state.json`

**Format**:
```json
{
  "parties": {
    "party_abc123": {
      "party_id": "party_abc123",
      "name": "Gaming Night",
      "host_id": "peer123",
      "created_at": "2026-01-29T12:00:00",
      "peers": {
        "peer123": {
          "peer_id": "peer123",
          "name": "Alice",
          "public_key": "base64_key...",
          "nat_type": "full_cone",
          "public_ip": "203.0.113.42",
          "public_port": 51820,
          "local_ip": "192.168.1.100",
          "local_port": 51820,
          "last_seen": "2026-01-29T12:05:00"
        }
      }
    }
  },
  "my_peer_id": "peer123",
  "my_party_id": "party_abc123"
}
```

### Discovery File (Local Mode)

**Location**: `~/.lanrage/discovery.json`

**Format**: Same as control state, but shared between local instances

## Cleanup Behavior

### Peer Timeout

- **Interval**: Checked every 60 seconds
- **Timeout**: 5 minutes without heartbeat
- **Action**: Remove peer from party

### Party Cleanup

- **Trigger**: No peers remaining or host left
- **Action**: Delete party from state

### State Persistence

- **Trigger**: After any state change
- **File**: `~/.lanrage/control_state.json`
- **Format**: JSON with ISO timestamps

## Remote Control Plane Protocol

### WebSocket Messages

**Connect**:
```json
{
  "type": "hello",
  "version": "1.0",
  "client": "lanrage"
}
```

**Register Party**:
```json
{
  "type": "register_party",
  "party_id": "party_abc123",
  "name": "Gaming Night",
  "host_peer": { /* PeerInfo */ }
}
```

**Join Party**:
```json
{
  "type": "join_party",
  "party_id": "party_abc123",
  "peer": { /* PeerInfo */ }
}
```

**Leave Party**:
```json
{
  "type": "leave_party",
  "party_id": "party_abc123",
  "peer_id": "peer123"
}
```

**Heartbeat**:
```json
{
  "type": "heartbeat",
  "party_id": "party_abc123",
  "peer_id": "peer123"
}
```

### Server Responses

**Party Update**:
```json
{
  "type": "party_update",
  "party": { /* PartyInfo */ }
}
```

**Peer Joined**:
```json
{
  "type": "peer_joined",
  "party_id": "party_abc123",
  "peer": { /* PeerInfo */ }
}
```

**Peer Left**:
```json
{
  "type": "peer_left",
  "party_id": "party_abc123",
  "peer_id": "peer123"
}
```

**Error**:
```json
{
  "type": "error",
  "message": "Party not found"
}
```

## Testing

### Unit Tests

```bash
python -c "
from core.control import LocalControlPlane, PeerInfo
from core.config import Config
from datetime import datetime
import asyncio

async def test():
    config = Config.load()
    control = LocalControlPlane(config)
    await control.initialize()
    
    # Create peer info
    peer_info = PeerInfo(
        peer_id='test_peer',
        name='Test',
        public_key='test_key',
        nat_type='full_cone',
        public_ip='127.0.0.1',
        public_port=51820,
        local_ip='127.0.0.1',
        local_port=51820,
        last_seen=datetime.now()
    )
    
    # Register party
    party = await control.register_party('test_party', 'Test Party', peer_info)
    print(f'Party created: {party.name}')
    
    # Get party
    retrieved = await control.get_party('test_party')
    print(f'Party retrieved: {retrieved.name}')
    
    print('✓ Control plane test passed')

asyncio.run(test())
"
```

## Future Enhancements

- WebSocket control server implementation
- Centralized relay coordination
- Party discovery (public parties)
- Invite links with expiration
- Party passwords
- Peer kick/ban functionality
- Voice chat signaling
- Screen share coordination
