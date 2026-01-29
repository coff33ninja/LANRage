# LANrage Project Structure

## Directory Layout

```
lanrage/
├── api/              # FastAPI REST API server
├── core/             # Core networking and party management
├── servers/          # Relay server implementation
├── static/           # Web UI (HTML/CSS/JS)
├── tests/            # Test suites
├── docs/             # Documentation
├── .kiro/            # Kiro AI assistant configuration
├── lanrage.py        # Main entry point
├── setup.py          # Setup script
└── requirements.txt  # Python dependencies
```

## Core Modules

### `core/`
Core networking and party management logic.

- `config.py` - Configuration management using Pydantic
- `network.py` - WireGuard interface and network stack management
- `party.py` - Party creation, joining, peer management
- `nat.py` - NAT traversal (STUN/TURN)
- `control.py` - Control plane for peer discovery
- `broadcast.py` - LAN broadcast emulation
- `games.py` - Game detection and profiles
- `connection.py` - Connection management and routing
- `utils.py` - Utility functions

### `api/`
FastAPI REST API for local control.

- `server.py` - API endpoints and server initialization

### `servers/`
Relay server for NAT traversal.

- `relay_server.py` - Stateless packet forwarding relay

### `static/`
Web UI for user interaction.

- `index.html` - Single-page web interface

### `tests/`
Test suites for various components.

- `test_all.py` - Comprehensive test suite
- `test_nat.py` - NAT traversal tests
- `test_wireguard.py` - WireGuard interface tests
- `test_multi_peer.py` - Multi-peer mesh tests

### `docs/`
Project documentation.

- `ARCHITECTURE.md` - System architecture overview
- `QUICKSTART.md` - Getting started guide
- `TESTING.md` - Testing procedures and benchmarks
- `NAT_TRAVERSAL.md` - NAT traversal implementation
- `CONTROL_PLANE.md` - Control plane design
- `ORACLE_RELAY.md` - Oracle VPS relay setup
- `WIREGUARD_SETUP.md` - WireGuard configuration
- `ROADMAP.md` - Development roadmap
- `COMPARISON.md` - Comparison with alternatives

## Key Files

- `lanrage.py` - Main entry point, initializes all components
- `setup.py` - One-time setup script for dependencies
- `requirements.txt` - Python package dependencies
- `.env.example` - Example environment configuration
- `CONTRIBUTING.md` - Contribution guidelines
- `README.md` - Project overview and quick start

## Module Responsibilities

### Network Layer (`core/network.py`)
- WireGuard interface creation and management
- Platform-specific implementations (Windows/Linux)
- Key generation and management
- Peer addition/removal
- Latency measurement

### Party Management (`core/party.py`)
- Party creation and joining
- Peer discovery and coordination
- Connection state management
- Status reporting

### NAT Traversal (`core/nat.py`)
- STUN for NAT type detection
- ICE for connection establishment
- Relay coordination

### API Server (`api/server.py`)
- REST endpoints for party operations
- Status reporting
- Web UI serving
- CORS configuration

## Configuration Files

- `.env` - Environment variables (not in git)
- `.env.example` - Template for environment configuration
- `~/.lanrage/` - User configuration directory
- `~/.lanrage/keys/` - WireGuard keypair storage
- `~/.lanrage/network.log` - Network operation logs

## Coding Conventions

### Async/Await
All I/O operations use async/await pattern. Network operations, API endpoints, and party management are all async.

### Error Handling
Custom exceptions for domain-specific errors:
- `WireGuardError` - WireGuard-related failures
- `NetworkError` - General network failures

### Logging
Operations logged to `~/.lanrage/network.log` for debugging.

### Platform Detection
Use `platform.system()` for OS-specific code:
- `is_windows` - Windows-specific paths
- `is_linux` - Linux-specific commands

### Type Hints
Required for all function signatures. Use `Optional[T]`, `list[T]`, `dict[K, V]` syntax.

### Pydantic Models
Use Pydantic for configuration and data validation. All config classes inherit from `BaseModel`.
