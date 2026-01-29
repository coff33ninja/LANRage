# LANrage Project Structure

## Directory Layout

```
lanrage/
├── api/              # FastAPI REST API server
├── core/             # Core networking and party management
├── servers/          # Control plane and relay server implementation
├── static/           # Web UI (HTML/CSS/JS)
├── tests/            # Test suites (62 tests, 88% coverage)
├── docs/             # Documentation (1650+ lines)
├── game_profiles/    # Game detection profiles (27 games)
├── .kiro/            # Kiro AI assistant configuration
├── lanrage.py        # Main entry point
├── setup.py          # Setup script
└── requirements.txt  # Python dependencies
```

## Core Modules

### `core/`
Core networking and party management logic.

- `config.py` - Configuration management using Pydantic + SQLite
- `network.py` - WireGuard interface and network stack management
- `party.py` - Party creation, joining, peer management
- `nat.py` - NAT traversal (STUN + hole punching)
- `control.py` - Control plane for peer discovery (SQLite-based)
- `control_client.py` - Control plane client with retry logic
- `broadcast.py` - LAN broadcast emulation
- `games.py` - Game detection and profiles (27 games)
- `connection.py` - Connection management and routing
- `ipam.py` - IP address management for virtual network
- `metrics.py` - Statistics collection and monitoring
- `discord_integration.py` - Discord webhooks and Rich Presence
- `server_browser.py` - Game server discovery and hosting
- `settings.py` - Settings database management (SQLite)
- `task_manager.py` - Background task management
- `exceptions.py` - Custom exception types
- `utils.py` - Utility functions

### `api/`
FastAPI REST API for local control.

- `server.py` - API endpoints and server initialization

### `servers/`
Control plane and relay server for NAT traversal.

- `control_server.py` - Control plane server with SQLite persistence
- `relay_server.py` - Stateless packet forwarding relay with database

### `static/`
Web UI for user interaction.

- `index.html` - Main dashboard
- `dashboard.html` - Statistics and metrics
- `settings.html` - Configuration management
- `servers.html` - Game server browser
- `discord.html` - Discord integration setup

### `tests/`
Test suites for various components (62 tests, 88% coverage).

- `test_all.py` - Comprehensive test suite
- `test_nat.py` - NAT traversal tests
- `test_wireguard.py` - WireGuard interface tests
- `test_multi_peer.py` - Multi-peer mesh tests
- `test_metrics.py` - Metrics collector tests (19 tests)
- `test_server_browser.py` - Server browser tests (17 tests)
- `test_discord.py` - Discord integration tests (10 tests)
- `test_performance.py` - Performance benchmarks (6 tests)
- `test_ipam.py` - IP address management tests
- `test_party.py` - Party management tests
- `check_db.py` - Database integrity checker

### `docs/`
Project documentation (1650+ lines).

- `ARCHITECTURE.md` - System architecture overview
- `QUICKSTART.md` - Getting started guide (90 seconds)
- `USER_GUIDE.md` - Complete user manual (400+ lines)
- `TROUBLESHOOTING.md` - Solutions to common problems (600+ lines)
- `TESTING.md` - Testing procedures and benchmarks
- `PRODUCTION_READY.md` - Production deployment checklist
- `PERFORMANCE_OPTIMIZATION.md` - Performance tuning guide
- `SESSION_PROGRESS.md` - Development summary
- `NAT_TRAVERSAL.md` - NAT traversal implementation
- `CONTROL_PLANE.md` - Control plane design
- `CONTROL_PLANE_SERVER.md` - Control server implementation
- `RELAY_SERVER.md` - Relay server setup
- `WIREGUARD_SETUP.md` - WireGuard configuration
- `DISCORD.md` - Discord integration details
- `DISCORD_SETUP_GUIDE.md` - Discord integration guide
- `DISCORD_APP_SETUP.md` - Discord app configuration
- `DISCORD_INTEGRATION_RATIONALE.md` - Why Discord integration
- `GAMES.md` - Game profiles and detection
- `SERVER_BROWSER.md` - Game server discovery
- `METRICS.md` - Statistics and monitoring
- `PARTY.md` - Party management
- `NETWORK.md` - Network layer details
- `BROADCAST.md` - Broadcast emulation
- `CONNECTION.md` - Connection management
- `SETTINGS.md` - Settings management
- `STARTUP_VALIDATION.md` - Troubleshooting startup issues
- `API.md` - REST API documentation
- `ROADMAP.md` - Development roadmap
- `README.md` - Documentation index

## Key Files

- `lanrage.py` - Main entry point, initializes all components
- `setup.py` - One-time setup script for dependencies
- `requirements.txt` - Python package dependencies (includes code quality tools)
- `.env.example` - Example environment configuration
- `CONTRIBUTING.md` - Contribution guidelines
- `README.md` - Project overview and quick start
- `LICENSE` - MIT License

### `game_profiles/`
Game detection and optimization profiles.

- `competitive.json` - Competitive games profile
- `coop.json` - Co-op games profile
- `party.json` - Party games profile
- `sandbox.json` - Sandbox games profile
- `strategy.json` - Strategy games profile
- `survival.json` - Survival games profile
- `custom/` - Custom game profiles (user-defined)
  - `call_of_duty.json` - Call of Duty profile
  - `far_cry.json` - Far Cry profile
  - `need_for_speed.json` - Need for Speed profile
  - `example.json` - Template for custom profiles
- `README.md` - Game profiles documentation

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
