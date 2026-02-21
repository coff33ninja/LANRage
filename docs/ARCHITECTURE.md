# LANrage Architecture

## Overview

LANrage is a mesh VPN optimized for gaming. It creates virtual LANs over the internet with minimal latency and zero configuration.

## Core Components

### 1. Control Plane (SQLite-based)
- Peer discovery and registration
- Party management
- Relay coordination
- Authentication tokens
- Automatic cleanup of stale data

**Implementation**: SQLite database via aiosqlite  
**Status**: Production ready (v1.3.1)  
**Future**: Phase 6 agent/orchestrator and extended web server integration

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
- Game detection and optimization

### 4. Relay Nodes
- Stateless packet forwarders
- No decryption
- Minimal resources
- SQLite-based state management

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

## Game-Specific Features

### Broadcast Emulation ✅
- Capture UDP broadcasts on configured ports
- Re-emit to all party members
- Translate addresses to virtual IPs
- Multi-protocol support (UDP/TCP)

**Status**: Production ready

### Multicast Support ✅
- mDNS forwarding (port 5353)
- SSDP emulation (port 1900)
- Custom multicast groups
- Automatic detection and forwarding

**Status**: Production ready

### Game Profiles ✅
- Per-game tuning (21 built-in profiles supported + custom profiles)
- Protocol detection
- Automatic optimization
- Custom JSON profiles
- QoS implementation (iptables/netsh/tc)

**Status**: Production ready

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

## Future Enhancements (v1.1+)

1. **Remote Control Plane** - WebSocket-based peer discovery
2. **IPv6 Support** - Dual-stack networking
3. **Enhanced UI** - React/Vue rewrite
4. **Mobile Apps** - iOS/Android clients
5. **Voice Chat** - Integrated communication
6. **Plugin System** - Extensibility framework

## Implementation Status

### ✅ Completed (v1.3.1)
- WireGuard interface creation and management
- STUN/TURN for NAT traversal
- Control plane (SQLite-based local)
- Game detection and optimization (21 built-in profiles + custom profiles)
- Broadcast/multicast emulation
- Relay server with database
- QoS implementation
- Discord integration
- Server browser
- Comprehensive testing (88% coverage)

### 🔄 In Progress (v1.1)
- Remote control plane (WebSocket)
- IPv6 support
- Enhanced web UI

### 📋 Planned (v2.0+)
- Mobile apps
- Voice chat
- Screen sharing
- Tournament mode
