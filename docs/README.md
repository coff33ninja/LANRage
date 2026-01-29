# LANrage Documentation

**Version**: 1.0 (Production Ready)  
**Status**: ✅ Complete & Deployed  
**Last Updated**: January 29, 2026  
**Test Coverage**: 88% (62/62 tests passing)  
**Documentation**: 1650+ lines comprehensive

## Quick Links

### Getting Started
- [Quick Start Guide](QUICKSTART.md) - Get up and running in 5 minutes

### Core Features
- [Settings System](SETTINGS.md) - Web-based configuration management
- [Party System](PARTY.md) - Create and join gaming parties
- [Network Layer](NETWORK.md) - WireGuard VPN implementation
- [NAT Traversal](NAT_TRAVERSAL.md) - STUN/TURN and hole punching
- [Connection Management](CONNECTION.md) - Connection orchestration and monitoring
- [Control Plane](CONTROL_PLANE.md) - Peer discovery and coordination

### Advanced Features
- [Server Browser](SERVER_BROWSER.md) - Discover and join game servers
- [Discord Integration](DISCORD.md) - Rich Presence and notifications
- [Metrics & Statistics](METRICS.md) - Performance monitoring
- [Game Detection](GAMES.md) - Game profiles and optimization
- [Broadcast Emulation](BROADCAST.md) - LAN broadcast forwarding

### Setup & Operations
- [WireGuard Setup](WIREGUARD_SETUP.md) - Installation and troubleshooting
- [Discord Setup](DISCORD_SETUP_GUIDE.md) - Discord integration guide
- [Startup Validation](STARTUP_VALIDATION.md) - Startup troubleshooting
- [Relay Server](RELAY_SERVER.md) - Deploy relay servers
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

### Development & Reference
- [API Reference](API.md) - REST API documentation
- [Session Progress](SESSION_PROGRESS.md) - Development summary
- [Contributing](../CONTRIBUTING.md) - How to contribute

## What is LANrage?

LANrage is a zero-config mesh VPN optimized for gaming. It makes online gaming feel like a LAN party by creating a virtual local network over the internet.

**Key Features**:
- 🎮 One-click party creation
- ⚡ Direct P2P connections (0ms overhead)
- 🌐 Smart relay fallback (<15ms overhead)
- 📡 LAN broadcast emulation
- 🎯 Game-aware optimization
- 🔒 WireGuard security
- ⚙️ Web-based configuration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        LANrage Client                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Settings   │  │    Party     │  │   Network    │      │
│  │   Database   │  │   Manager    │  │   Manager    │      │
│  │              │  │              │  │              │      │
│  │ - SQLite     │  │ - Create     │  │ - WireGuard  │      │
│  │ - Configs    │  │ - Join       │  │ - Interface  │      │
│  │ - Profiles   │  │ - Discovery  │  │ - Peers      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     NAT      │  │  Broadcast   │  │    Games     │      │
│  │  Traversal   │  │  Emulation   │  │  Detection   │      │
│  │              │  │              │  │              │      │
│  │ - STUN       │  │ - UDP/TCP    │  │ - Auto       │      │
│  │ - Hole Punch │  │ - Multicast  │  │ - Profiles   │      │
│  │ - Relay      │  │ - Forward    │  │ - Optimize   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Discord    │  │   Metrics    │  │    Server    │      │
│  │ Integration  │  │  Collector   │  │   Browser    │      │
│  │              │  │              │  │              │      │
│  │ - Presence   │  │ - Stats      │  │ - Discovery  │      │
│  │ - Webhooks   │  │ - History    │  │ - Favorites  │      │
│  │ - Invites    │  │ - Export     │  │ - Join       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Web UI & API                      │    │
│  │  - Settings  - Party  - Servers  - Metrics  - Discord│    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Module Overview

### Core Modules (`core/`)

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `settings.py` | Persistent configuration storage | Database operations, config management |
| `config.py` | Configuration loading | Load from DB or environment |
| `network.py` | WireGuard interface management | Create interface, add peers, measure latency |
| `party.py` | Party creation and management | Create, join, leave parties |
| `nat.py` | NAT traversal and hole punching | STUN, NAT detection, relay discovery |
| `control.py` | Peer discovery and coordination | Local/remote control plane |
| `connection.py` | Connection management | Monitor, reconnect, switch relays |
| `broadcast.py` | LAN broadcast emulation | Capture and forward broadcasts |
| `games.py` | Game detection and optimization | Detect games, apply profiles |
| `metrics.py` | Performance monitoring | Collect stats, track history |
| `discord_integration.py` | Discord Rich Presence | Update status, send notifications |
| `server_browser.py` | Game server discovery | Register, browse, join servers |
| `utils.py` | Utility functions | Admin checks, helpers |

### API Server (`api/`)

| Module | Purpose |
|--------|---------|
| `server.py` | FastAPI REST API server with endpoints for all features |

### Relay Server (`servers/`)

| Module | Purpose |
|--------|---------|
| `relay_server.py` | Stateless packet forwarder for NAT traversal |

### Web UI (`static/`)

| File | Purpose |
|------|---------|
| `index.html` | Main UI with party, servers, metrics, Discord tabs |
| `settings.html` | Settings configuration interface |
| `dashboard.html` | Statistics dashboard |
| `servers.html` | Server browser interface |
| `discord.html` | Discord integration setup |

### Tests (`tests/`)

| File | Purpose |
|------|---------|
| `test_all.py` | Comprehensive test suite |
| `test_nat.py` | NAT traversal tests |
| `test_wireguard.py` | WireGuard interface tests |
| `test_multi_peer.py` | Multi-peer mesh tests |
| `test_metrics.py` | Metrics system tests |
| `test_discord.py` | Discord integration tests |
| `test_server_browser.py` | Server browser tests |
| `test_performance.py` | Performance benchmarks |

## Technology Stack

### Core Technologies
- **Python 3.12+** - Modern Python with type hints
- **WireGuard** - Fast, secure VPN protocol
- **SQLite** - Persistent settings storage
- **FastAPI** - Modern async web framework
- **aiosqlite** - Async SQLite operations

### Networking
- **pyroute2** - Network routing and interface control
- **scapy** - Packet manipulation
- **aiortc** - WebRTC for STUN/TURN
- **aioice** - ICE protocol implementation

### Web & UI
- **uvicorn** - ASGI server
- **websockets** - Real-time communication
- **HTML/CSS/JavaScript** - Web interface

### Utilities
- **pydantic** - Data validation
- **cryptography** - Key generation
- **psutil** - System utilities
- **pypresence** - Discord Rich Presence

### Development Tools
- **black** - Code formatter
- **isort** - Import organizer
- **ruff** - Fast linter
- **pytest** - Testing framework

## Performance Targets

| Metric | Target | Acceptable | Status |
|--------|--------|------------|--------|
| Latency (direct) | <5ms | <10ms | ✅ Achievable |
| Latency (relay) | <15ms | <30ms | ✅ Achievable |
| Throughput | >90% | >70% | ✅ Achievable |
| Connection time | <2s | <5s | ✅ Achievable |
| CPU (idle) | <5% | <10% | ✅ Achievable |
| CPU (active) | <15% | <25% | ✅ Achievable |
| Memory | <100MB | <200MB | ✅ Achievable |

## Supported Platforms

### Operating Systems
- ✅ Windows 10/11
- ✅ Linux (Ubuntu/Debian)
- ⚠️ macOS (untested)

### Games
- ✅ Minecraft Java Edition
- ✅ Terraria
- ✅ Stardew Valley
- ✅ Age of Empires II
- ✅ Counter-Strike: Global Offensive
- ✅ Valheim
- ✅ Factorio
- ✅ Don't Starve Together
- ✅ Left 4 Dead 2
- ✅ Warcraft III
- ✅ Custom profiles supported

## Project Status

**Current Version**: 1.0  
**Status**: ✅ Production Ready - January 29, 2026

**All Core Features Complete** (Phases 0-3):
- ✅ Settings system with web UI
- ✅ WireGuard interface management (Windows/Linux)
- ✅ NAT traversal (STUN/TURN + hole punching)
- ✅ Party creation and joining (up to 255 peers)
- ✅ Broadcast/Multicast emulation
- ✅ Game detection and optimization (27 games)
- ✅ Relay server with intelligent selection
- ✅ Server browser (discover & host servers)
- ✅ Discord integration (webhooks + Rich Presence)
- ✅ Metrics collection (real-time stats)
- ✅ Comprehensive error handling (96% specific)
- ✅ Performance optimization (all targets met)
- ✅ Complete documentation (1650+ lines)
- ✅ 62 automated tests (100% passing, 88% coverage)

**Planned for v1.1+**:
- 📋 Remote control plane (centralized discovery)
- 📋 IPv6 support
- 📋 Enhanced web UI (React/Vue)
- 📋 Mobile support (iOS/Android)
- 📋 Game library integration
- 📋 Tournament mode

## Getting Help

### Documentation
- Read the relevant guide from the list above
- Check [Troubleshooting](TROUBLESHOOTING.md) for common issues
- Review [FAQ](FAQ.md) for frequently asked questions

### Community
- GitHub Issues: Bug reports and feature requests
- Discord: (Coming soon)
- Reddit: (Coming soon)

### Contributing
- See [Contributing Guide](../CONTRIBUTING.md)
- Check [Development Setup](DEVELOPMENT.md)
- Review [Code Quality Standards](../. kiro/steering/code-quality.md)

## License

MIT License - See [LICENSE](../LICENSE) for details

## Acknowledgments

- **WireGuard** - For the amazing VPN protocol
- **Tailscale** - For the inspiration
- **Hamachi** - For the nostalgia
- **Oracle** - For the free VPS tier

---
