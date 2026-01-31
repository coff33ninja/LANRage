# Network Layer Documentation

The network layer manages WireGuard interfaces and provides the foundation for LANrage's virtual LAN functionality.

## Module: `core/network.py`

### Overview

The `NetworkManager` class handles all WireGuard interface operations, including:
- Interface creation and configuration
- Key generation and management
- Peer addition and removal
- Latency measurement
- Platform-specific implementations (Windows/Linux)

### Class: `NetworkManager`

#### Initialization

```python
def __init__(self, config: Config):
    """
    Initialize network manager
    
    Args:
        config: LANrage configuration object
    """
```

**Attributes**:
- `config`: Configuration object
- `interface_name`: WireGuard interface name (default: "lanrage0")
- `private_key`: Raw private key bytes
- `public_key`: Raw public key bytes
- `private_key_b64`: Base64-encoded private key
- `public_key_b64`: Base64-encoded public key
- `is_windows`: Platform detection flag
- `is_linux`: Platform detection flag
- `interface_created`: Interface creation status
- `log_file`: Path to network operations log

#### Core Methods

##### `async def initialize()`

Initialize the network interface.

**Process**:
1. Check if WireGuard is installed
2. Generate or load WireGuard keypair
3. Create WireGuard interface (platform-specific)
4. Set interface status flag

**Raises**:
- `WireGuardError`: If WireGuard not found or interface creation fails

**Example**:
```python
network = NetworkManager(config)
await network.initialize()
print(f"Public key: {network.public_key_b64}")
```

##### `async def add_peer(peer_public_key: str, peer_endpoint: Optional[str], allowed_ips: list[str])`

Add a WireGuard peer to the interface.

**Parameters**:
- `peer_public_key`: Base64-encoded WireGuard public key
- `peer_endpoint`: Peer's public endpoint (IP:port) or None for dynamic
- `allowed_ips`: List of IP ranges allowed for this peer (e.g., ["10.66.0.2/32"])

**Features**:
- Configures persistent keepalive (25 seconds) for NAT traversal
- Supports dynamic endpoints (peer-initiated connections)
- Handles both direct and relayed connections

**Example**:
```python
await network.add_peer(
    peer_public_key="base64_key_here",
    peer_endpoint="203.0.113.42:51820",
    allowed_ips=["10.66.0.2/32"]
)
```

##### `async def remove_peer(peer_public_key: str)`

Remove a WireGuard peer from the interface.

**Parameters**:
- `peer_public_key`: Base64-encoded WireGuard public key

**Example**:
```python
await network.remove_peer("base64_key_here")
```

##### `async def measure_latency(peer_ip: str) -> float`

Measure latency to a peer using ICMP ping.

**Parameters**:
- `peer_ip`: Virtual IP address of the peer

**Returns**:
- Latency in milliseconds, or None if unreachable

**Platform Support**:
- Windows: Uses `ping -n 1 -w 1000`
- Linux: Uses `ping -c 1 -W 1`

**Example**:
```python
latency = await network.measure_latency("10.66.0.2")
if latency:
    print(f"Latency: {latency}ms")
else:
    print("Peer unreachable")
```

##### `async def get_interface_status() -> dict`

Get current WireGuard interface status.

**Returns**:
Dictionary with:
- `status`: "active", "not_created", or "error"
- `interface`: Interface name
- `public_key`: Base64-encoded public key
- `output`: Raw `wg show` output (if active)
- `error`: Error message (if error)

**Example**:
```python
status = await network.get_interface_status()
print(f"Interface: {status['interface']}")
print(f"Status: {status['status']}")
```

##### `async def cleanup()`

Cleanup WireGuard interface on shutdown.

**Platform Behavior**:
- Windows: Uninstalls tunnel service
- Linux: Deletes interface

**Example**:
```python
await network.cleanup()
```

#### Internal Methods

##### `async def _check_wireguard() -> bool`

Check if WireGuard is installed and accessible.

**Returns**: True if WireGuard is available, False otherwise

##### `async def _ensure_keys()`

Generate or load WireGuard keypair.

**Behavior**:
- Checks for existing keys in `~/.lanrage/keys/`
- Generates new Curve25519 keypair if not found
- Saves keys to disk with secure permissions (Unix)
- Converts keys to base64 for WireGuard

**Key Storage**:
- Private key: `~/.lanrage/keys/private.key`
- Public key: `~/.lanrage/keys/public.key`
- Permissions: 0600 (Unix only)

##### `async def _create_interface()`

Create WireGuard interface (platform dispatcher).

Calls platform-specific implementation:
- Windows: `_create_interface_windows()`
- Linux: `_create_interface_linux()`

##### `async def _create_interface_windows()`

Create WireGuard interface on Windows.

**Process**:
1. Generate WireGuard config file
2. Check if tunnel service already exists
3. Install tunnel service if needed
4. Handle service reuse for existing tunnels

**Config File**: `~/.lanrage/lanrage0.conf`

**Service Name**: `WireGuardTunnel$lanrage0`

**Timeout**: 30 seconds for installation

##### `async def _create_interface_linux()`

Create WireGuard interface on Linux.

**Process**:
1. Check for root/sudo access
2. Create interface with `ip link add`
3. Set private key with `wg set`
4. Assign IP address (10.66.0.1/16)
5. Set MTU to 1420 (WireGuard overhead)
6. Bring interface up

**Requirements**:
- Root or sudo access
- WireGuard kernel module loaded
- `ip` and `wg` commands available

##### `async def _check_root() -> bool`

Check if we have root/sudo access (Linux only).

**Returns**: True if sudo is available, False otherwise

##### `async def _cleanup_interface_linux()`

Cleanup Linux interface on error or shutdown.

Deletes interface with `ip link delete`

##### `def _log(message: str)`

Log network operations to file.

**Log File**: `~/.lanrage/network.log`

**Format**: `[timestamp] message`

**Error Handling**: Falls back to stderr if file logging fails

##### `async def _run_command(cmd: list[str], check: bool = True, timeout: float = 30.0) -> subprocess.CompletedProcess`

Run a command asynchronously with timeout.

**Parameters**:
- `cmd`: Command and arguments as list
- `check`: Raise exception on non-zero exit code
- `timeout`: Command timeout in seconds

**Returns**: CompletedProcess with stdout/stderr

**Raises**:
- `subprocess.TimeoutExpired`: If command times out
- `subprocess.CalledProcessError`: If command fails and check=True

### Exception: `WireGuardError`

Custom exception for WireGuard-related errors.

**Usage**:
```python
try:
    await network.initialize()
except WireGuardError as e:
    print(f"WireGuard error: {e}")
```

## Virtual Network Configuration

### Subnet

- **Range**: 10.66.0.0/16
- **Host IP**: 10.66.0.1
- **Peer IPs**: 10.66.0.2-255, 10.66.1.0-255, etc.
- **Total Capacity**: 65,534 peers

### Interface

- **Name**: lanrage0
- **MTU**: 1420 bytes (accounts for WireGuard overhead)
- **Protocol**: IPv4 (IPv6 support planned)

### WireGuard Settings

- **Keepalive**: 25 seconds (for NAT traversal)
- **Port**: 51820 (default)
- **Encryption**: ChaCha20-Poly1305
- **Key Exchange**: Curve25519

## Platform-Specific Details

### Windows

**Requirements**:
- WireGuard for Windows installed
- Administrator privileges
- `wireguard.exe` in PATH

**Interface Management**:
- Uses Windows service (`WireGuardTunnel$lanrage0`)
- Config file-based configuration
- Service persists across reboots

**Limitations**:
- Cannot dynamically update config
- Service must be reinstalled for key changes
- Requires elevated privileges

### Linux

**Requirements**:
- WireGuard kernel module or wireguard-go
- Root or sudo access
- `ip` and `wg` commands available

**Interface Management**:
- Uses `ip link` for interface creation
- Uses `wg` for peer configuration
- Dynamic configuration updates

**Advantages**:
- Full control over interface
- Dynamic peer updates
- No service management needed

## Performance

### Latency Overhead

- **Direct P2P**: <1ms
- **Same-region relay**: 5-15ms
- **Cross-region relay**: 30-100ms

### Throughput

- **WireGuard overhead**: ~60 bytes per packet
- **MTU**: 1420 bytes (1500 - 80 overhead)
- **Line speed**: No artificial throttling

### CPU Usage

- **Idle**: <1%
- **Active gaming**: 2-5%
- **High throughput**: 5-15%

### Memory Usage

- **Base**: ~10MB
- **Per peer**: ~1MB
- **Total**: <100MB for typical party

## Security

### Encryption

- **Algorithm**: ChaCha20-Poly1305
- **Key Size**: 256-bit
- **Authentication**: Poly1305 MAC

### Key Management

- **Generation**: Cryptographically secure random
- **Storage**: Local filesystem only
- **Permissions**: 0600 (Unix)
- **Rotation**: Manual (not yet implemented)

### Attack Resistance

- **Man-in-the-middle**: Prevented by public key authentication
- **Replay attacks**: Prevented by WireGuard's anti-replay
- **Traffic analysis**: Encrypted packet headers
- **DDoS**: Rate limiting at WireGuard level

## Troubleshooting

### "WireGuard not found"

**Cause**: WireGuard not installed or not in PATH

**Solution**:
- Windows: Install from https://www.wireguard.com/install/
- Linux: `sudo apt install wireguard`

### "Permission denied"

**Cause**: Insufficient privileges for interface creation

**Solution**:
- Windows: Run as Administrator
- Linux: Use `sudo` or add user to `netdev` group

### "Interface creation failed"

**Cause**: Various (port in use, kernel module missing, etc.)

**Solution**:
- Check logs in `~/.lanrage/network.log`
- Verify WireGuard is properly installed
- Check for conflicting interfaces
- Ensure port 51820 is available

### "Peer unreachable"

**Cause**: Network connectivity issue or incorrect endpoint

**Solution**:
- Verify peer endpoint is correct
- Check firewall allows UDP 51820
- Test with manual ping
- Check NAT traversal status

## Testing

### Unit Tests

```bash
python tests/test_wireguard.py
```

### Manual Testing

```python
from core.config import Config
from core.network import NetworkManager
import asyncio

async def test():
    config = await Config.load()
    network = NetworkManager(config)
    
    # Initialize
    await network.initialize()
    print(f"Interface created: {network.interface_name}")
    print(f"Public key: {network.public_key_b64}")
    
    # Check status
    status = await network.get_interface_status()
    print(f"Status: {status}")
    
    # Cleanup
    await network.cleanup()

asyncio.run(test())
```

## Future Enhancements

- IPv6 support
- Dynamic MTU discovery
- Automatic key rotation
- Interface migration (roaming)
- Multi-interface support
- QoS and traffic shaping
