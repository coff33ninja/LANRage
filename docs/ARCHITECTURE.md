# LANrage Architecture

## Overview

LANrage is a mesh VPN optimized for gaming. It creates virtual LANs over the internet with minimal latency and zero configuration.

## Core Components

### 1. Control Plane (TODO)
- Peer discovery
- Key exchange
- Party management
- Relay coordination

**Not yet implemented** - currently using local-only mode.

### 2. Data Plane (WireGuard)
- Encrypted tunnels between peers
- Direct P2P when possible
- Relay fallback for NAT traversal
- UDP-first, always

### 3. Client Application
- Local API server (FastAPI)
- Web UI (HTML/JS)
- Network manager (WireGuard interface)
- Party manager (peer coordination)

### 4. Relay Nodes
- Stateless packet forwarders
- No decryption
- Minimal resources
- Anycast-ready

## Network Flow

```
┌─────────────┐         ┌─────────────┐
│   Client A  │◄───────►│   Client B  │  (Direct P2P - best case)
└─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client A  │◄───────►│    Relay    │◄───────►│   Client B  │  (Relayed - NAT hell)
└─────────────┘         └─────────────┘         └─────────────┘
```

## Connection Priority

1. **Direct P2P** (0ms overhead)
   - UDP hole punching
   - STUN for NAT detection
   - Best latency

2. **Same-Region Relay** (~5-10ms overhead)
   - Geographically close
   - Low latency penalty
   - High availability

3. **Nearest Relay** (~10-30ms overhead)
   - Anycast routing
   - Fallback option

4. **TCP Tunnel** (~50ms+ overhead)
   - Last resort
   - Shows warning to user
   - Better than nothing

## Virtual Network

- Subnet: `10.66.0.0/16`
- Interface: `lanrage0`
- MTU: 1420 (WireGuard overhead)
- Protocol: IPv4 (IPv6 later)

## Security Model

- **Encryption**: WireGuard (ChaCha20-Poly1305)
- **Key Exchange**: X25519
- **Authentication**: Public key cryptography
- **Trust Model**: Peer-to-peer (no central authority)

Relays:
- Never decrypt traffic
- No logging
- Stateless operation
- Can't MITM

## Game-Specific Features (TODO)

### Broadcast Emulation
- Capture UDP broadcasts
- Re-emit to party members
- Translate addresses

### Multicast Support
- mDNS forwarding
- SSDP emulation
- Custom multicast groups

### Game Profiles
- Per-game tuning
- Protocol detection
- Automatic optimization

## Performance Targets

- **Latency overhead**: <5ms (direct), <15ms (relayed)
- **Throughput**: Line speed (no bottleneck)
- **Connection time**: <2 seconds
- **CPU usage**: <5% idle, <15% active
- **Memory**: <100MB per client

## Platform Support

### Phase 1 (Current)
- Windows 10/11
- Linux (Ubuntu/Debian)

### Phase 2 (Future)
- macOS
- Android
- iOS (maybe)

### Never
- Consoles (locked down)
- Smart TVs (why?)

## Deployment

### Client
- Standalone executable
- Auto-updates
- Local web UI

### Relay
- Docker container
- Systemd service
- Minimal dependencies

## Monitoring

- Latency graphs
- Connection type
- Bandwidth usage
- Peer status

## Scalability

### Single Relay
- 50-100 concurrent connections
- 500 Mbps throughput
- 1 core / 1GB RAM

### Relay Pool
- Anycast routing
- Geographic distribution
- Auto-scaling

## Future Enhancements

1. **Voice Chat** (integrated)
2. **Screen Sharing** (for troubleshooting)
3. **Game Library Integration** (auto-detect games)
4. **Clan Servers** (persistent parties)
5. **Mobile Apps** (Android first)

## Technical Debt

- Control plane not implemented
- WireGuard setup is stubbed
- No actual NAT traversal yet
- Latency measurement is mocked
- No relay discovery

## Next Steps

1. Implement WireGuard interface creation
2. Add STUN/TURN for NAT traversal
3. Build control plane (peer discovery)
4. Test with real games
5. Deploy first relay node
