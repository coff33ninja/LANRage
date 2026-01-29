# LANrage Technical Stack

## Language & Version

- Python 3.12+ (required)
- Type hints required everywhere
- Async/await for all I/O operations

## Core Dependencies

### Networking
- `wireguard-tools` - WireGuard interface management
- `pyroute2` - Network routing and interface control
- `scapy` - Packet manipulation and broadcast emulation

### NAT Traversal
- `aiortc` - WebRTC for STUN/TURN
- `aioice` - ICE protocol implementation

### Web Framework
- `fastapi` - REST API server (20+ endpoints)
- `uvicorn` - ASGI server
- `websockets` - Real-time communication
- `httpx` - Async HTTP client for control plane

### Database & Persistence
- `aiosqlite` - Async SQLite for settings and control plane

### Utilities
- `pydantic` - Data validation and settings
- `cryptography` - Key generation and encryption
- `python-dotenv` - Environment configuration
- `psutil` - System and process utilities
- `aiohttp` - Async HTTP for Discord webhooks

### Optional
- `pypresence` - Discord Rich Presence integration

### Code Quality
- `black` - Code formatter
- `isort` - Import sorter
- `ruff` - Fast Python linter

### Testing
- `pytest` - Test framework
- `pytest-asyncio` - Async test support

## Build System

Uses `uv` (modern Python package manager) for dependency management and virtual environments.

### Setup Commands

```bash
# Initial setup (one-time)
python setup.py

# Activate virtual environment
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# Install dependencies
uv pip install -r requirements.txt
```

### Running

```bash
# Start LANrage
python lanrage.py

# Access web UI
http://localhost:8666
```

### Testing

```bash
# Run all tests
python tests/test_all.py

# Run specific test suites
python tests/test_nat.py
python tests/test_wireguard.py
python tests/test_multi_peer.py
```

## Code Style

- **Formatting**: Black (when contributions open)
- **Import sorting**: isort
- **Linting**: Ruff
- **Type checking**: Type hints required for all public APIs
- **Docstrings**: Required for public functions and classes

### Example Code Pattern

```python
async def measure_latency(peer_ip: str, count: int = 10) -> float:
    """
    Measure latency to a peer.
    
    Args:
        peer_ip: Virtual IP of the peer
        count: Number of pings to average
        
    Returns:
        Average latency in milliseconds
        
    Raises:
        NetworkError: If peer is unreachable
    """
    # Implementation
    pass
```

### Code Quality Validation

Before committing, always run:

```bash
# Use venv Python for all commands
.venv\Scripts\python.exe -m isort .              # Windows
.venv/bin/python -m isort .                      # Linux/Mac

.venv\Scripts\python.exe -m black .              # Windows
.venv/bin/python -m black .                      # Linux/Mac

.venv\Scripts\python.exe -m ruff check --fix .   # Windows
.venv/bin/python -m ruff check --fix .           # Linux/Mac

.venv\Scripts\python.exe -m pytest tests/        # Windows
.venv/bin/python -m pytest tests/                # Linux/Mac
```

## Platform Support

### Current
- Windows 10/11
- Linux (Ubuntu/Debian)

### Requirements
- WireGuard installed
- Admin/root privileges for interface creation
- Python 3.12+
- uv package manager

## Configuration

- Environment variables via `.env` file
- Config class in `core/config.py` using Pydantic
- Default config directory: `~/.lanrage/`
- Keys stored in: `~/.lanrage/keys/`

## API Server

- FastAPI REST API on localhost:8666
- CORS enabled for local web UI
- Static files served from `/static`
- WebSocket support for real-time updates

## Performance Targets

**All targets met or exceeded in v1.0:**

- Latency overhead: <3ms (direct) ✅ Target: <5ms
- Latency overhead: <12ms (relayed) ✅ Target: <15ms
- Throughput: >95% of baseline ✅ Target: >90%
- Connection time: ~1.5s ✅ Target: <2s
- CPU usage: ~3% idle, ~12% active ✅ Target: <5% idle, <15% active
- Memory: ~80MB per client ✅ Target: <100MB
- Test coverage: 88% ✅ Target: 85%
