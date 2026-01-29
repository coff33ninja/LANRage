# Party System Documentation

The party system is the core of LANrage's multiplayer experience, managing virtual LANs and peer connections.

## Module: `core/party.py`

### Overview

The party system provides:
- Party creation and management
- Peer discovery and coordination
- Connection orchestration
- Status tracking and monitoring
- Integration with NAT traversal and control plane

### Class: `Peer`

Pydantic model representing a peer in the party.

**Attributes**:
- `id` (str): Unique peer identifier
- `name` (str): Display name
- `public_key` (str): Base64-encoded WireGuard public key
- `virtual_ip` (str): Assigned virtual IP (10.66.0.x)
- `endpoint` (str | None): Public endpoint (IP:port) or None
- `latency_ms` (float | None): Measured latency in milliseconds
- `connection_type` (str): "direct", "relayed", "connecting", "host", "failed", "unknown"
- `joined_at` (datetime): Timestamp when peer joined

**Example**:
```python
peer = Peer(
    id="peer123",
    name="Alice",
    public_key="base64_key...",
    virtual_ip="10.66.0.2",
    endpoint="203.0.113.42:51820",
    latency_ms=25.5,
    connection_type="direct"
)
```

### Class: `Party`

Pydantic model representing a gaming party.

**Attributes**:
- `id` (str): Unique party identifier
- `name` (str): Party name
- `host_id` (str): Host peer ID
- `peers` (Dict[str, Peer]): Dictionary of peers by ID
- `created_at` (datetime): Party creation timestamp

#### Methods

##### `def get_peer_list() -> List[Peer]`

Get list of all peers in party.

**Returns**: List of Peer objects

**Example**:
```python
peers = party.get_peer_list()
for peer in peers:
    print(f"{peer.name}: {peer.virtual_ip}")
```

##### `def get_compatible_peers(my_nat_type: NATType) -> List[Peer]`

Get list of peers compatible with my NAT type for direct connection.

**Parameters**:
- `my_nat_type`: Your NAT type

**Returns**: List of compatible Peer objects

**Compatibility Logic**:
- Open/Full Cone: Can connect to anyone
- Restricted Cone: Can connect to non-symmetric NATs
- Symmetric: Cannot connect directly (needs relay)

**Example**:
```python
compatible = party.get_compatible_peers(NATType.FULL_CONE)
print(f"Can directly connect to {len(compatible)} peers")
```

### Class: `PartyManager`

Manages parties and peer connections.

#### Initialization

```python
def __init__(self, config: Config, network: NetworkManager):
    """
    Initialize party manager
    
    Args:
        config: LANrage configuration
        network: Network manager instance
    """
```

**Attributes**:
- `config`: Configuration object
- `network`: NetworkManager instance
- `current_party`: Current party or None
- `my_peer_id`: Unique peer identifier
- `nat`: NATTraversal instance
- `coordinator`: ConnectionCoordinator instance
- `control`: ControlPlane instance
- `connections`: ConnectionManager instance

#### Core Methods

##### `async def initialize_nat()`

Initialize NAT traversal.

**Process**:
1. Create NATTraversal instance
2. Detect NAT type using STUN
3. Create ConnectionCoordinator
4. Handle detection failures gracefully

**Fallback**: If NAT detection fails, uses relay-only mode

**Example**:
```python
party_manager = PartyManager(config, network)
await party_manager.initialize_nat()
print(f"NAT Type: {party_manager.nat.nat_type.value}")
```

##### `async def initialize_control()`

Initialize control plane.

**Process**:
1. Create ControlPlane instance
2. Initialize control plane
3. Create ConnectionManager
4. Link all components

**Example**:
```python
await party_manager.initialize_control()
print("Control plane ready")
```

##### `async def create_party(name: str) -> Party`

Create a new party.

**Parameters**:
- `name`: Party name

**Returns**: Created Party object

**Process**:
1. Generate unique party ID
2. Create Party object
3. Add self as first peer (host)
4. Register with control plane
5. Set as current party

**Example**:
```python
party = await party_manager.create_party("Gaming Night")
print(f"Party ID: {party.id}")
print(f"Share this ID with friends!")
```

##### `async def join_party(party_id: str, peer_name: str) -> Party`

Join an existing party.

**Parameters**:
- `party_id`: Party ID to join
- `peer_name`: Your display name

**Returns**: Joined Party object

**Process**:
1. Create peer info with NAT details
2. Join via control plane
3. Receive party info and peer list
4. Convert to local Party format
5. Connect to all existing peers
6. Set as current party

**Example**:
```python
party = await party_manager.join_party("a3f7c2", "Bob")
print(f"Joined party: {party.name}")
print(f"Peers: {len(party.peers)}")
```

##### `async def leave_party()`

Leave current party.

**Process**:
1. Disconnect from all peers
2. Leave via control plane
3. Clear current party

**Example**:
```python
await party_manager.leave_party()
print("Left party")
```

##### `async def get_party_status() -> dict`

Get current party status.

**Returns**: Status dictionary with:
- `status`: "no_party" or "in_party"
- `party`: Party object (if in party)
- `peer_count`: Number of peers
- `nat_info`: NAT information dict

**Includes**:
- Updated latency measurements for all peers
- NAT type and public endpoint
- Connection types for each peer

**Example**:
```python
status = await party_manager.get_party_status()
if status['status'] == 'in_party':
    print(f"Party: {status['party']['name']}")
    print(f"Peers: {status['peer_count']}")
    print(f"NAT: {status['nat_info']['nat_type']}")
```

#### Internal Methods

##### `async def _connect_to_peer(party_id: str, peer_id: str)`

Connect to a peer (internal).

**Parameters**:
- `party_id`: Party ID
- `peer_id`: Peer ID to connect to

**Process**:
1. Use ConnectionManager to establish connection
2. Update peer connection type on success
3. Handle connection failures

**Called automatically** when joining a party

## Connection Flow

### Creating a Party

```
User                PartyManager           ControlPlane
 │                       │                       │
 │──create_party()──────>│                       │
 │                       │                       │
 │                       │──register_party()────>│
 │                       │                       │
 │                       │<──party_registered────│
 │                       │                       │
 │<──Party object────────│                       │
 │                       │                       │
```

### Joining a Party

```
User                PartyManager           ControlPlane           Peers
 │                       │                       │                 │
 │──join_party()────────>│                       │                 │
 │                       │                       │                 │
 │                       │──join_party()────────>│                 │
 │                       │                       │                 │
 │                       │<──party_info──────────│                 │
 │                       │   (with peer list)    │                 │
 │                       │                       │                 │
 │                       │──connect_to_peer()────────────────────>│
 │                       │                       │                 │
 │                       │<──connection_established───────────────│
 │                       │                       │                 │
 │<──Party object────────│                       │                 │
 │                       │                       │                 │
```

### Peer Connection

```
PartyManager        ConnectionManager      NATTraversal        Network
 │                       │                       │                 │
 │──connect_to_peer()───>│                       │                 │
 │                       │                       │                 │
 │                       │──coordinate()────────>│                 │
 │                       │                       │                 │
 │                       │<──strategy────────────│                 │
 │                       │   (direct/relay)      │                 │
 │                       │                       │                 │
 │                       │──add_peer()──────────────────────────>│
 │                       │                       │                 │
 │                       │<──peer_added──────────────────────────│
 │                       │                       │                 │
 │<──success─────────────│                       │                 │
 │                       │                       │                 │
```

## Virtual IP Allocation

LANrage uses a simple hash-based allocation:

```python
def allocate_virtual_ip(peer_id: str) -> str:
    peer_hash = hash(peer_id)
    octet3 = (peer_hash >> 8) & 0xFF
    octet4 = peer_hash & 0xFF
    
    if octet4 <= 1:
        octet4 = 2  # Reserve 0 and 1
    
    return f"10.66.{octet3}.{octet4}"
```

**Characteristics**:
- Deterministic (same peer ID → same IP)
- Distributed across subnet
- Avoids reserved addresses
- No central allocation needed

## Connection Types

### "host"
- Party creator
- Always at 10.66.0.1
- No latency measurement needed

### "direct"
- Direct P2P connection
- Best latency (<5ms overhead)
- Requires compatible NATs

### "relayed"
- Connection through relay server
- Higher latency (10-100ms overhead)
- Works with any NAT type

### "connecting"
- Connection in progress
- Temporary state
- Will become "direct" or "relayed"

### "failed"
- Connection attempt failed
- May retry or use different strategy
- User should be notified

### "unknown"
- Initial state
- Before connection attempt
- Should not persist

## Status Monitoring

### Latency Measurement

Latency is measured periodically for all peers:

```python
for peer in party.peers.values():
    if peer.id != my_peer_id and peer.virtual_ip:
        peer.latency_ms = await network.measure_latency(peer.virtual_ip)
```

**Frequency**: On-demand (when status requested)  
**Method**: ICMP ping  
**Timeout**: 1 second

### Connection Health

Connection health is monitored by ConnectionManager:
- Periodic latency checks
- Automatic reconnection on failure
- Route optimization for high latency

## Integration Points

### With Network Layer

```python
# Add peer to WireGuard
await network.add_peer(
    peer_public_key=peer.public_key,
    peer_endpoint=endpoint,
    allowed_ips=[f"{peer.virtual_ip}/32"]
)

# Measure latency
latency = await network.measure_latency(peer.virtual_ip)
```

### With NAT Traversal

```python
# Detect NAT type
await nat.detect_nat()

# Check compatibility
can_connect = nat.can_direct_connect(peer_nat_type)

# Coordinate connection
result = await coordinator.coordinate_connection(
    peer_public_key, peer_nat_info
)
```

### With Control Plane

```python
# Register party
await control.register_party(party_id, name, my_peer_info)

# Join party
party_info = await control.join_party(party_id, my_peer_info)

# Leave party
await control.leave_party(party_id, my_peer_id)
```

## Error Handling

### Party Creation Failures

```python
try:
    party = await party_manager.create_party("My Party")
except Exception as e:
    print(f"Failed to create party: {e}")
    # Handle error (show user message, retry, etc.)
```

### Join Failures

```python
try:
    party = await party_manager.join_party(party_id, name)
except Exception as e:
    print(f"Failed to join party: {e}")
    # Possible causes:
    # - Invalid party ID
    # - Party full
    # - Network issues
    # - Control plane unavailable
```

### Connection Failures

```python
# Handled internally by _connect_to_peer
# Peer status updated to "failed"
# User notified via UI
```

## Performance

### Party Creation

- **Time**: <100ms
- **Network**: 1 control plane request
- **CPU**: Minimal

### Joining Party

- **Time**: 1-3 seconds
- **Network**: 1 control plane request + N peer connections
- **CPU**: Moderate (NAT traversal, WireGuard setup)

### Status Updates

- **Time**: <500ms (with latency measurements)
- **Network**: N ICMP pings
- **CPU**: Minimal

## Security

### Party IDs

- Random 6-byte hex strings
- Not guessable
- No sequential allocation
- Invite-only model

### Peer Authentication

- WireGuard public key authentication
- No passwords needed
- Cryptographic verification
- Man-in-the-middle resistant

### Privacy

- Party membership visible to control plane
- Peer endpoints visible to control plane
- Game traffic encrypted end-to-end
- No logging of game data

## Testing

### Unit Tests

```bash
python tests/test_multi_peer.py
```

### Manual Testing

```python
from core.config import Config
from core.network import NetworkManager
from core.party import PartyManager
import asyncio

async def test():
    config = Config.load()
    network = NetworkManager(config)
    await network.initialize()
    
    party_manager = PartyManager(config, network)
    await party_manager.initialize_nat()
    await party_manager.initialize_control()
    
    # Create party
    party = await party_manager.create_party("Test Party")
    print(f"Party ID: {party.id}")
    
    # Get status
    status = await party_manager.get_party_status()
    print(f"Status: {status}")
    
    # Cleanup
    await party_manager.leave_party()
    await network.cleanup()

asyncio.run(test())
```

## Future Enhancements

- Party passwords (access control)
- Peer kick/ban (moderation)
- Party size limits (scaling)
- Party discovery (public parties)
- **Voice chat** - Via [Discord Integration](DISCORD.md)
- **Screen sharing** - Via [Discord Integration](DISCORD.md)
- Game state sync (advanced features)
- Persistent parties (clan servers)
