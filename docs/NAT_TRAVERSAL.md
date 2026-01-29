# NAT Traversal Documentation

LANrage uses multiple strategies to establish peer-to-peer connections through NAT.

## Module: `core/nat.py`

### Overview

The NAT traversal system provides:
- STUN-based NAT type detection
- UDP hole punching for direct P2P
- Relay fallback for difficult NATs
- Connection strategy selection
- Relay discovery and selection

### Enum: `NATType`

NAT type classification for connection strategy.

**Values**:
- `UNKNOWN`: NAT type not yet detected
- `OPEN`: No NAT (direct internet connection)
- `FULL_CONE`: One-to-one mapping, easy to traverse
- `RESTRICTED_CONE`: Requires hole punching
- `PORT_RESTRICTED_CONE`: Requires coordinated hole punching
- `SYMMETRIC`: Very difficult, requires relay

### Class: `NATTraversal`

#### Initialization

```python
def __init__(self, config: Config):
    """
    Initialize NAT traversal
    
    Args:
        config: LANrage configuration
    """
```

**Attributes**:
- `config`: Configuration object
- `public_ip`: Detected public IP address
- `public_port`: Detected public port
- `nat_type`: Detected NAT type
- `local_ip`: Local IP address
- `local_port`: Local port
- `STUN_SERVERS`: List of public STUN servers

#### Core Methods

##### `async def detect_nat() -> STUNResponse`

Detect NAT type using STUN protocol.

**Process**:
1. Try multiple STUN servers in sequence
2. Send STUN Binding Request
3. Parse XOR-MAPPED-ADDRESS from response
4. Determine NAT type from mappings
5. Store public endpoint information

**Returns**: STUNResponse with NAT information

**Raises**: `NATError` if all STUN servers fail

**Example**:
```python
nat = NATTraversal(config)
response = await nat.detect_nat()
print(f"NAT Type: {response.nat_type.value}")
print(f"Public: {response.public_ip}:{response.public_port}")
print(f"Local: {response.local_ip}:{response.local_port}")
```

##### `async def attempt_hole_punch(peer_public_ip: str, peer_public_port: int, local_port: int = 51820) -> bool`

Attempt UDP hole punching with peer.

**Parameters**:
- `peer_public_ip`: Peer's public IP address
- `peer_public_port`: Peer's public port
- `local_port`: Local port to bind (default: 51820)

**Process**:
1. Bind to local WireGuard port
2. Send 5 punch packets over 500ms
3. Wait for ACK response
4. Return success/failure

**Returns**: True if hole punched successfully, False otherwise

**Example**:
```python
success = await nat.attempt_hole_punch("203.0.113.42", 51820)
if success:
    print("Hole punched! Direct P2P possible")
else:
    print("Hole punch failed, using relay")
```

##### `def can_direct_connect(peer_nat_type: NATType) -> bool`

Check if direct P2P connection is possible.

**Parameters**:
- `peer_nat_type`: Peer's NAT type

**Returns**: True if direct connection possible, False if relay needed

**Decision Matrix**:
| Your NAT | Peer NAT | Result |
|----------|----------|--------|
| Open | Any | Direct |
| Full Cone | Full Cone | Direct |
| Full Cone | Restricted | Direct |
| Restricted | Restricted | Direct |
| Port-Restricted | Port-Restricted | Direct |
| Symmetric | Any | Relay |
| Any | Symmetric | Relay |

**Example**:
```python
if nat.can_direct_connect(peer_nat_type):
    print("Direct P2P connection possible")
else:
    print("Relay required")
```

##### `def get_connection_strategy(peer_nat_type: NATType) -> str`

Determine best connection strategy.

**Parameters**:
- `peer_nat_type`: Peer's NAT type

**Returns**: "direct" or "relay"

**Example**:
```python
strategy = nat.get_connection_strategy(peer_nat_type)
print(f"Connection strategy: {strategy}")
```

#### Internal Methods

##### `async def _stun_request(stun_server: Tuple[str, int]) -> Optional[STUNResponse]`

Send STUN request to server.

**Parameters**:
- `stun_server`: Tuple of (hostname, port)

**Returns**: STUNResponse or None if failed

**STUN Protocol** (RFC 5389):
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|0 0|     STUN Message Type     |         Message Length        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Magic Cookie                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Transaction ID (96 bits)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

##### `def _parse_stun_attributes(data: bytes) -> Tuple[Optional[str], Optional[int]]`

Parse STUN attributes to extract mapped address.

**Parameters**:
- `data`: STUN response payload

**Returns**: Tuple of (public_ip, public_port) or (None, None)

**Attributes Parsed**:
- `0x0001`: MAPPED-ADDRESS
- `0x0020`: XOR-MAPPED-ADDRESS (preferred)

##### `def _determine_nat_type(local_ip: str, local_port: int, public_ip: str, public_port: int) -> NATType`

Determine NAT type from address mappings.

**Parameters**:
- `local_ip`: Local IP address
- `local_port`: Local port
- `public_ip`: Public IP address
- `public_port`: Public port

**Returns**: Detected NATType

**Logic**:
- If public IP == local IP → OPEN
- If public port == local port → FULL_CONE
- Otherwise → PORT_RESTRICTED_CONE (simplified)

### Class: `ConnectionCoordinator`

Coordinates peer connections with NAT traversal.

#### Initialization

```python
def __init__(self, config: Config, nat: NATTraversal):
    """
    Initialize connection coordinator
    
    Args:
        config: LANrage configuration
        nat: NAT traversal instance
    """
```

#### Core Methods

##### `async def coordinate_connection(peer_public_key: str, peer_nat_info: dict) -> dict`

Coordinate connection with peer.

**Parameters**:
- `peer_public_key`: Peer's WireGuard public key
- `peer_nat_info`: Peer's NAT information dict

**Returns**: Connection result dict with:
- `strategy`: "direct", "relay", or "failed"
- `endpoint`: Connection endpoint (IP:port)
- `success`: Boolean success flag
- `error`: Error message (if failed)

**Process**:
1. Determine connection strategy
2. Attempt direct connection if possible
3. Fall back to relay if needed
4. Return connection details

**Example**:
```python
coordinator = ConnectionCoordinator(config, nat)
result = await coordinator.coordinate_connection(
    peer_public_key="base64_key",
    peer_nat_info={
        "nat_type": "full_cone",
        "public_ip": "203.0.113.42",
        "public_port": 51820
    }
)
print(f"Strategy: {result['strategy']}")
print(f"Endpoint: {result['endpoint']}")
```

##### `async def _attempt_direct_connection(peer_nat_info: dict) -> bool`

Attempt direct P2P connection.

**Parameters**:
- `peer_nat_info`: Peer's NAT information

**Returns**: True if successful, False otherwise

##### `async def _get_relay_endpoint() -> str`

Get relay server endpoint with discovery and latency measurement.

**Process**:
1. Discover available relays from control plane
2. Measure latency to each relay
3. Select relay with lowest latency
4. Return relay endpoint

**Returns**: Relay endpoint string (IP:port)

**Fallback**: Uses configured relay or default relay.lanrage.io:51820

##### `async def _discover_relays() -> list`

Discover available relay servers from control plane.

**Returns**: List of relay dicts with:
- `ip`: Relay IP address
- `port`: Relay port
- `region`: Geographic region
- `relay_id`: Relay identifier

**Process**:
1. Query control plane for relay list (if available)
2. Convert control plane format to internal format
3. Fall back to configured relay if control plane unavailable
4. Fall back to default relay.lanrage.io:51820 as final option

**Control Plane Integration**:
- Uses `control_client.list_relays()` to fetch relay list
- Automatically discovers all registered relays
- Supports multi-region relay selection
- Graceful fallback on control plane failure

**Example Response**:
```python
[
    {
        "ip": "relay1.lanrage.io",
        "port": 51820,
        "region": "us-west",
        "relay_id": "relay-us-west-1"
    },
    {
        "ip": "relay2.lanrage.io",
        "port": 51820,
        "region": "eu-central",
        "relay_id": "relay-eu-central-1"
    }
]
```

##### `async def _select_best_relay(relays: list) -> Optional[dict]`

Select relay with lowest latency.

**Parameters**:
- `relays`: List of relay dicts

**Returns**: Best relay dict or None

**Process**:
1. Measure latency to each relay
2. Select relay with lowest latency
3. Log selection

##### `async def _measure_relay_latency(relay_ip: str) -> Optional[float]`

Measure latency to relay server using ICMP ping.

**Parameters**:
- `relay_ip`: Relay IP address

**Returns**: Latency in milliseconds or None

### Exception: `NATError`

Custom exception for NAT traversal errors.

**Usage**:
```python
try:
    await nat.detect_nat()
except NATError as e:
    print(f"NAT detection failed: {e}")
```

## STUN Protocol

### Public STUN Servers

LANrage uses Google's public STUN servers:
- stun.l.google.com:19302
- stun1.l.google.com:19302
- stun2.l.google.com:19302
- stun3.l.google.com:19302
- stun4.l.google.com:19302

### STUN Request Format

**Message Type**: 0x0001 (Binding Request)  
**Magic Cookie**: 0x2112A442  
**Transaction ID**: 12 random bytes

### STUN Response Parsing

**Message Type**: 0x0101 (Binding Response)  
**Attributes**:
- XOR-MAPPED-ADDRESS (0x0020): Public endpoint
- MAPPED-ADDRESS (0x0001): Fallback

**XOR Decoding**:
- Port: XOR with 0x2112
- IP: XOR with magic cookie (0x2112A442)

## UDP Hole Punching

### How It Works

1. **Both peers send simultaneously**:
   - Peer A → Peer B's public endpoint
   - Peer B → Peer A's public endpoint

2. **NAT creates mappings**:
   - NAT sees outbound packet
   - Opens hole for return traffic

3. **Packets cross in transit**:
   - Each NAT now allows other's packets
   - Direct P2P connection established

### Implementation

```python
# Send punch packets
for _ in range(5):
    sock.sendto(b"LANRAGE_PUNCH", (peer_ip, peer_port))
    await asyncio.sleep(0.1)

# Wait for ACK
data, addr = sock.recvfrom(1024)
if data == b"LANRAGE_PUNCH_ACK":
    return True  # Success
```

### Timing

- Send 5 packets over 500ms
- Increases chance of crossing
- Handles packet loss
- 2-second timeout for ACK

## Connection Strategies

### Direct P2P

**When**: Compatible NAT types  
**Latency**: <1ms overhead  
**Success Rate**: 95% for cone NATs

**Configuration**:
```python
endpoint = f"{peer_public_ip}:{peer_public_port}"
await network.add_peer(peer_key, endpoint, allowed_ips)
```

### Relayed

**When**: Symmetric NAT or hole punch fails  
**Latency**: 10-100ms overhead  
**Success Rate**: 100% (always works)

**Configuration**:
```python
endpoint = "relay.lanrage.io:51820"
await network.add_peer(peer_key, endpoint, allowed_ips)
```

## Performance

### Latency Impact

| Connection Type | Added Latency |
|----------------|---------------|
| Direct | <1ms |
| Hole Punched | <5ms |
| Same-Region Relay | 10-20ms |
| Cross-Region Relay | 30-100ms |

### Success Rates

| NAT Combination | Success Rate |
|----------------|--------------|
| Open ↔ Any | 100% |
| Cone ↔ Cone | 95% |
| Cone ↔ Symmetric | 0% (relay) |
| Symmetric ↔ Symmetric | 0% (relay) |

## Security

### STUN Security

- No authentication required
- Only reveals public endpoint
- Cannot be used for attacks
- Safe to use public servers

### Hole Punching Security

- Packets encrypted by WireGuard
- Only authenticated peers accepted
- No plaintext leaks
- Timing-based only

### Relay Security

- End-to-end encryption maintained
- Relay cannot decrypt
- No logging
- Authenticated forwarding

## Troubleshooting

### "Failed to detect NAT type"

**Causes**:
- Firewall blocking UDP
- STUN servers unreachable
- Network issues

**Solutions**:
- Check firewall settings
- Test STUN manually: `nc -u stun.l.google.com 19302`
- Try different network

### "Hole punching failed"

**Causes**:
- Symmetric NAT
- Strict firewall
- Timing issues

**Solutions**:
- Use relay fallback (automatic)
- Try different network
- Check router settings

### "Relay connection slow"

**Causes**:
- Geographic distance
- Relay overloaded
- Network congestion

**Solutions**:
- Use closer relay
- Deploy more relays
- Check network quality

## Testing

### Test NAT Detection

```bash
python tests/test_nat.py
```

Expected output:
```
🔥 LANrage NAT Traversal Test
============================================================

1. Detecting NAT type...
   ✓ NAT detected
   - Type: Port-Restricted Cone
   - Public IP: 203.0.113.42
   - Public Port: 51820

2. Testing STUN servers...
   ✓ stun.l.google.com:19302 - OK (45ms)

3. Connection strategy analysis...
   - vs Open NAT: Direct ✓
   - vs Symmetric: Relay ⚠

============================================================
✅ NAT traversal test complete!
```

## Future Enhancements

- Full ICE implementation
- Multiple STUN servers simultaneously
- Better NAT detection (multiple requests)
- Automatic retry logic
- TURN server implementation
- IPv6 support
