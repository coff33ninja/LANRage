# Connection Management Documentation

The connection manager orchestrates peer connections, handling the entire lifecycle from discovery to monitoring.

## Module: `core/connection.py`

### Overview

The connection manager provides:
- Peer connection orchestration
- NAT traversal coordination
- WireGuard peer configuration
- Connection health monitoring
- Automatic reconnection
- Relay switching for optimization

### Class: `ConnectionManager`

Manages connections to peers.

#### Initialization

```python
def __init__(
    self,
    config: Config,
    network: NetworkManager,
    nat: NATTraversal,
    control: ControlPlane
):
    """
    Initialize connection manager
    
    Args:
        config: LANrage configuration
        network: Network manager instance
        nat: NAT traversal instance
        control: Control plane instance
    """
```

**Attributes**:
- `config`: Configuration object
- `network`: NetworkManager for WireGuard operations
- `nat`: NATTraversal for NAT detection
- `control`: ControlPlane for peer discovery
- `coordinator`: ConnectionCoordinator for strategy selection
- `connections`: Dictionary of active PeerConnection objects

#### Core Methods

##### `async def connect_to_peer(party_id: str, peer_id: str) -> bool`

Connect to a peer with full orchestration.

**Parameters**:
- `party_id`: Party ID
- `peer_id`: Peer ID to connect to

**Returns**: True if connection successful

**Process**:
1. Discover peer via control plane
2. Determine connection strategy (direct/relay)
3. Attempt hole punching if needed
4. Configure WireGuard peer
5. Allocate virtual IP
6. Create connection record
7. Start monitoring task

**Raises**: `ConnectionError` if peer not found or connection fails

**Example**:
```python
conn_manager = ConnectionManager(config, network, nat, control)
success = await conn_manager.connect_to_peer("party_abc123", "peer456")
if success:
    print("Connected to peer!")
```

##### `async def disconnect_from_peer(peer_id: str)`

Disconnect from a peer.

**Parameters**:
- `peer_id`: Peer ID to disconnect

**Process**:
1. Remove WireGuard peer configuration
2. Delete connection record
3. Stop monitoring task

**Example**:
```python
await conn_manager.disconnect_from_peer("peer456")
```

##### `async def get_connection_status(peer_id: str) -> Optional[dict]`

Get connection status for a peer.

**Parameters**:
- `peer_id`: Peer ID

**Returns**: Status dictionary or None if not connected

**Status Dictionary**:
```python
{
    "peer_id": "peer456",
    "virtual_ip": "10.66.0.42",
    "endpoint": "203.0.113.42:51820",
    "strategy": "direct",  # or "relay"
    "latency_ms": 25.5,
    "connected_at": "2026-01-29T12:00:00",
    "status": "connected"  # or "degraded"
}
```

**Example**:
```python
status = await conn_manager.get_connection_status("peer456")
if status:
    print(f"Latency: {status['latency_ms']}ms")
    print(f"Strategy: {status['strategy']}")
```

#### Internal Methods

##### `def _allocate_virtual_ip(peer_id: str) -> str`

Allocate a virtual IP for a peer.

**Parameters**:
- `peer_id`: Peer ID

**Returns**: Virtual IP address (10.66.x.x)

**Algorithm**:
```python
peer_hash = hash(peer_id)
octet3 = (peer_hash >> 8) & 0xFF
octet4 = peer_hash & 0xFF

if octet4 <= 1:
    octet4 = 2  # Reserve .0 and .1

return f"10.66.{octet3}.{octet4}"
```

**Characteristics**:
- Deterministic (same peer ID → same IP)
- Distributed across subnet
- Avoids reserved addresses

##### `async def _monitor_connection(peer_id: str)`

Monitor connection health (background task).

**Parameters**:
- `peer_id`: Peer ID to monitor

**Monitoring**:
- Checks every 30 seconds
- Measures latency
- Detects connection failures
- Attempts reconnection (up to 3 times)
- Switches relay if latency high

**Reconnection Logic**:
```python
if latency is None:
    reconnect_attempts += 1
    if reconnect_attempts >= 3:
        connection.status = "failed"
    else:
        # Attempt reconnection
        await network.remove_peer(peer_key)
        await network.add_peer(peer_key, endpoint, allowed_ips)
```

**Relay Switching**:
```python
if latency > 200 and strategy == "relay":
    # Try to find better relay
    await _switch_relay(peer_id, connection)
```

##### `async def _switch_relay(peer_id: str, connection: PeerConnection)`

Switch to a better relay server.

**Parameters**:
- `peer_id`: Peer ID
- `connection`: Current connection object

**Process**:
1. Measure current latency
2. Discover alternative relays
3. Test new relay
4. Compare latencies
5. Switch if better, revert if worse

**Example Output**:
```
Current latency: 150ms
Found alternative relay: relay2.lanrage.io:51820
✓ Switched to better relay: 85ms (improved by 43.3%)
```

### Class: `PeerConnection`

Represents a connection to a peer.

**Attributes**:
- `peer_id` (str): Peer identifier
- `peer_info` (PeerInfo): Peer information
- `virtual_ip` (str): Assigned virtual IP
- `endpoint` (str): Connection endpoint (IP:port)
- `strategy` (str): "direct" or "relay"
- `connected_at` (datetime): Connection timestamp
- `status` (str): "connected", "degraded", or "failed"

**Example**:
```python
connection = PeerConnection(
    peer_id="peer456",
    peer_info=peer_info,
    virtual_ip="10.66.0.42",
    endpoint="203.0.113.42:51820",
    strategy="direct",
    connected_at=datetime.now()
)
```

### Exception: `ConnectionError`

Custom exception for connection errors.

**Usage**:
```python
try:
    await conn_manager.connect_to_peer(party_id, peer_id)
except ConnectionError as e:
    print(f"Connection failed: {e}")
```

## Connection Flow

### Full Connection Process

```
ConnectionManager          ConnectionCoordinator      Network
       │                           │                      │
       │──discover_peer()─────────>│                      │
       │                           │                      │
       │<──peer_info───────────────│                      │
       │                           │                      │
       │──coordinate_connection()─>│                      │
       │                           │                      │
       │                           │──detect_nat()───────>│
       │                           │                      │
       │                           │<──nat_type───────────│
       │                           │                      │
       │                           │──attempt_hole_punch()│
       │                           │                      │
       │<──strategy_result─────────│                      │
       │   (direct/relay)          │                      │
       │                           │                      │
       │──add_peer()──────────────────────────────────────>│
       │                           │                      │
       │<──peer_added──────────────────────────────────────│
       │                           │                      │
       │──start_monitoring()───────────────────────────────>│
       │                           │                      │
```

### Monitoring Loop

```
Monitor Task              Network                 ConnectionManager
     │                       │                           │
     │──measure_latency()───>│                           │
     │                       │                           │
     │<──latency─────────────│                           │
     │                       │                           │
     │──[if latency None]────────────────────────────────>│
     │                       │                           │
     │                       │<──reconnect_peer()────────│
     │                       │                           │
     │──[if latency > 200]───────────────────────────────>│
     │                       │                           │
     │                       │<──switch_relay()──────────│
     │                       │                           │
     │──sleep(30s)───────────────────────────────────────>│
     │                       │                           │
```

## Connection Strategies

### Direct P2P

**When**: Compatible NAT types  
**Latency**: <5ms overhead  
**Reliability**: 95% success rate

**Configuration**:
```python
endpoint = f"{peer_public_ip}:{peer_public_port}"
await network.add_peer(
    peer_public_key=peer_key,
    peer_endpoint=endpoint,
    allowed_ips=[f"{virtual_ip}/32"]
)
```

### Relayed

**When**: Symmetric NAT or hole punch fails  
**Latency**: 10-100ms overhead  
**Reliability**: 100% (always works)

**Configuration**:
```python
endpoint = "relay.lanrage.io:51820"
await network.add_peer(
    peer_public_key=peer_key,
    peer_endpoint=endpoint,
    allowed_ips=[f"{virtual_ip}/32"]
)
```

## Connection States

### "connected"

- Latency measured successfully
- Latency < 200ms
- Normal operation

### "degraded"

- Latency > 200ms
- Connection slow but working
- May trigger relay switch

### "failed"

- No latency measurement
- 3 reconnection attempts failed
- User should be notified

## Monitoring Behavior

### Health Checks

- **Frequency**: Every 30 seconds
- **Method**: ICMP ping to virtual IP
- **Timeout**: 1 second

### Reconnection

- **Trigger**: Latency measurement fails
- **Attempts**: Up to 3
- **Delay**: 5 seconds between attempts
- **Action**: Remove and re-add WireGuard peer

### Relay Switching

- **Trigger**: Latency > 200ms on relay connection
- **Process**: Discover better relay, test, compare
- **Threshold**: Switch if improvement > 0ms
- **Fallback**: Revert if new relay worse

## Performance

### Connection Time

- **Direct**: 1-2 seconds
- **Relay**: 2-3 seconds
- **With hole punch**: 2-4 seconds

### Monitoring Overhead

- **CPU**: <1% per peer
- **Network**: ~100 bytes/30s per peer
- **Memory**: ~1KB per peer

### Reconnection Time

- **Automatic**: 5-15 seconds
- **Manual**: Immediate

## Error Handling

### Peer Not Found

```python
try:
    await conn_manager.connect_to_peer(party_id, "invalid_peer")
except ConnectionError as e:
    print(f"Peer not found: {e}")
```

### Connection Failed

```python
# Handled internally
# Connection status updated to "failed"
# User notified via UI
```

### Relay Unavailable

```python
# Falls back to next available relay
# Or uses configured relay
# Or fails with error
```

## Testing

### Unit Tests

```bash
python -c "
from core.connection import ConnectionManager
from core.config import Config
from core.network import NetworkManager
from core.nat import NATTraversal
from core.control import LocalControlPlane
import asyncio

async def test():
    config = await Config.load()
    network = NetworkManager(config)
    await network.initialize()
    
    nat = NATTraversal(config)
    await nat.detect_nat()
    
    control = LocalControlPlane(config)
    await control.initialize()
    
    conn_manager = ConnectionManager(config, network, nat, control)
    
    print('✓ Connection manager initialized')
    
    await network.cleanup()

asyncio.run(test())
"
```

## Future Enhancements

- Connection pooling
- Multi-path connections
- Bandwidth optimization
- QoS prioritization
- Connection migration (roaming)
- IPv6 support
- Automatic relay discovery
- Load balancing across relays
