# WireGuard Setup Guide

## What Just Got Implemented

LANrage now has full WireGuard interface management:

- ✅ Automatic key generation (Curve25519)
- ✅ Interface creation (Windows & Linux)
- ✅ Peer management (add/remove)
- ✅ Latency measurement
- ✅ Platform detection
- ✅ Error handling

## Prerequisites

### Windows

1. **Install WireGuard**:
   - Download from: https://www.wireguard.com/install/
   - Run installer
   - Verify: `wg --version`

2. **Run as Administrator**:
   - Right-click LANrage
   - "Run as Administrator"

### Linux

1. **Install WireGuard**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install wireguard wireguard-tools
   
   # Fedora
   sudo dnf install wireguard-tools
   
   # Arch
   sudo pacman -S wireguard-tools
   ```

2. **Verify installation**:
   ```bash
   wg --version
   ```

3. **Setup sudo** (if needed):
   ```bash
   # Add your user to sudoers
   sudo usermod -aG sudo $USER
   
   # Or configure passwordless sudo for wg commands
   echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/ip" | sudo tee /etc/sudoers.d/lanrage
   ```

## Testing

Run the test script to verify everything works:

```bash
# Activate venv
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux

# Run test
python -m pytest tests/test_wireguard.py -v
```

Expected output:
```
🔥 LANrage WireGuard Test
============================================================

1. Checking admin/root privileges...
   ✓ Running with admin/root privileges

2. Loading configuration...
   ✓ Config loaded
   - Mode: client
   - Interface: lanrage0
   - Subnet: 10.66.0.0/16

3. Initializing network manager...
   ✓ Network manager initialized
   - Public key: AbCdEfGhIjKlMnOpQr...
   - Interface created: True

4. Checking interface status...
   ✓ Interface is active
   - Interface: lanrage0
   - Public key: AbCdEfGhIjKlMnOpQr...

5. Testing latency measurement...
   ✓ Latency to 8.8.8.8: 15.2ms

6. Cleaning up...
   ✓ Cleanup complete

============================================================
✅ WireGuard test complete!
```

## How It Works

### Key Generation

LANrage uses Curve25519 (X25519) for WireGuard keys:

```python
# Generate keypair
private_key = x25519.X25519PrivateKey.generate()
public_key = private_key.public_key()

# Convert to base64 for WireGuard
private_key_b64 = base64.b64encode(private_key_bytes)
public_key_b64 = base64.b64encode(public_key_bytes)
```

Keys are stored in `~/.lanrage/keys/`:
- `private.key` (600 permissions on Unix)
- `public.key`

### Interface Creation

**Windows**:
1. Generate WireGuard config file
2. Use `wireguard.exe /installtunnelservice`
3. Interface appears in WireGuard GUI

**Linux**:
1. Create interface: `ip link add dev lanrage0 type wireguard`
2. Set private key: `wg set lanrage0 private-key /dev/stdin`
3. Assign IP: `ip address add dev lanrage0 10.66.0.1/16`
4. Set MTU: `ip link set mtu 1420 up dev lanrage0`
5. Bring up: `ip link set up dev lanrage0`

### Peer Management

Add a peer:
```python
await network.add_peer(
    peer_public_key="base64_encoded_key",
    peer_endpoint="1.2.3.4:51820",  # Optional
    allowed_ips=["10.66.0.2/32"]
)
```

This runs:
```bash
wg set lanrage0 \
  peer <public_key> \
  endpoint <ip:port> \
  allowed-ips <ips> \
  persistent-keepalive 25
```

### Latency Measurement

Uses platform-specific ping:

**Windows**: `ping -n 1 -w 1000 <ip>`
**Linux**: `ping -c 1 -W 1 <ip>`

Parses output for time value.

## Troubleshooting

### "WireGuard not found"

**Windows**:
- Install from https://www.wireguard.com/install/
- Add to PATH if needed

**Linux**:
```bash
sudo apt install wireguard wireguard-tools
```

### "Permission denied"

**Windows**:
- Run as Administrator

**Linux**:
```bash
# Run with sudo
sudo python lanrage.py

# Or setup passwordless sudo
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/ip" | sudo tee /etc/sudoers.d/lanrage
```

### "Interface already exists"

Cleanup old interface:

**Windows**:
```cmd
wireguard /uninstalltunnelservice lanrage0
```

**Linux**:
```bash
sudo ip link delete dev lanrage0
```

### "Cannot create interface"

**Windows**:
- Check WireGuard service is running
- Verify admin rights
- Check Windows Firewall

**Linux**:
- Check kernel modules: `lsmod | grep wireguard`
- Load module: `sudo modprobe wireguard`
- Check permissions

### "Latency measurement fails"

- Check firewall (allow ICMP)
- Verify network connectivity
- Try different target IP

## Security Notes

### Key Storage

- Private keys stored in `~/.lanrage/keys/`
- 600 permissions on Unix (owner read/write only)
- Never share private keys
- Public keys are safe to share

### Interface Security

- All traffic encrypted (ChaCha20-Poly1305)
- Perfect forward secrecy
- No plaintext leaks
- Authenticated encryption

### Peer Authentication

- Peers identified by public key
- No passwords or tokens
- Cryptographic authentication
- Man-in-the-middle resistant

## Performance

### Overhead

- WireGuard: ~100 bytes per packet
- MTU: 1420 (1500 - 80 overhead)
- Latency: <1ms added (direct)
- CPU: Minimal (hardware accelerated)

### Throughput

- Line speed on modern hardware
- No artificial limits
- Scales with CPU cores
- Hardware crypto acceleration

## Next Steps

Now that WireGuard is working:

1. Validate NAT behavior with `python -m pytest tests/test_nat.py -v`
2. Validate connection orchestration with `python -m pytest tests/test_connection.py -v`
3. Validate control-plane behavior with `python -m pytest tests/test_control_server.py -v`
4. Validate broadcast/game integration with `python -m pytest tests/test_broadcast.py tests/test_games.py -v`

## References

- WireGuard: https://www.wireguard.com/
- Protocol: https://www.wireguard.com/protocol/
- Cryptography: https://www.wireguard.com/papers/wireguard.pdf
- Installation: https://www.wireguard.com/install/
