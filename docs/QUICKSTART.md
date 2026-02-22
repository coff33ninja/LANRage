# LANrage Quick Start Guide

Get LANrage v1.4.0 running in under 5 minutes.

## What You're Getting

LANrage v1.4.0 is production-ready with:
- ✅ Direct P2P connections (<5ms overhead)
- ✅ Smart relay fallback (<15ms overhead)
- ✅ Built-in and custom game profiles with auto-optimization
- ✅ Broadcast/multicast emulation
- ✅ Discord integration
- ✅ Game server browser
- ✅ Real-time statistics
- ✅ Latest full suite passing (463/463)

## Prerequisites

- **Python 3.12+** (required)
- **uv** package manager
- **Windows 10/11** or **Linux** (Ubuntu/Debian)
- **Admin/root privileges** (for network interface creation)
- **WireGuard** installed

## Installation

### 1. Install uv

**Windows (PowerShell)**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/Mac**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install WireGuard

**Windows**: Download from https://www.wireguard.com/install/  
**Linux**: `sudo apt install wireguard`

### 3. Clone and Setup

```bash
git clone https://github.com/coff33ninja/LANRage.git
cd lanrage
python setup.py
```

The setup script will:
- Create `.venv` virtual environment
- Install all dependencies via uv
- Initialize SQLite settings database
- Generate WireGuard keys

### 4. Activate Virtual Environment

**Windows (CMD)**:
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac**:
```bash
source .venv/bin/activate
```

## Running LANrage

### Start the Service

```bash
python lanrage.py
```

Expected output:
```
🔥 LANrage - If it runs on LAN, it runs on LANrage
============================================================
✓ Settings database initialized
✓ Config loaded (mode: client)
✓ Network initialized (interface: lanrage0)
✓ NAT traversal initialized (type: Port-Restricted Cone)
✓ Control plane ready (SQLite-based)
✓ Party manager ready
✓ Server browser started
✓ Discord integration ready
✓ Metrics collector started
✓ API server running on http://127.0.0.1:8666
============================================================
LANrage v1.4.0 - Production Ready
```

### Access the Web UI

Open your browser to: **http://localhost:8666**

## Creating a Party

1. Click **"CREATE PARTY"** button
2. Enter a party name (e.g., "Gaming Night")
3. Note the **Party ID** (e.g., `a3f7c2`)
4. Share this ID with friends

## Joining a Party

1. Click **"JOIN PARTY"** button
2. Enter the **Party ID** from your friend
3. Enter your display name
4. Click **"JOIN"**

LANrage will automatically:
- Detect your NAT type
- Attempt direct P2P connection
- Fall back to relay if needed
- Configure WireGuard interface
- Measure latency to peers

## Playing Games

Once in a party:
1. Launch your game
2. Look for **LAN/Local multiplayer** option
3. Your friends should appear as "local" players
4. Start playing!

## Configuration

### Settings UI

Access settings at: **http://localhost:8666/settings.html**

Configure:
- **Mode**: Client or Relay server
- **Peer Name**: Your display name
- **Network Settings**: Virtual subnet, interface name
- **API Settings**: Host and port
- **WireGuard**: Keepalive interval
- **Control Server**: Discovery endpoint
- **Relay Settings**: Public IP and port (for relay mode)

Settings are stored in SQLite database at `~/.lanrage/settings.db`

### Configuration Storage

LANrage uses a database-first configuration model. Manage settings through:
- Web UI: `http://localhost:8666/settings.html`
- SQLite DB: `~/.lanrage/config.db`

## Troubleshooting

### "Permission denied" on startup

**Windows**: Run as Administrator  
**Linux**: Use `sudo` or add user to `netdev` group

### "WireGuard not found"

Install WireGuard:
- **Windows**: https://www.wireguard.com/install/
- **Linux**: `sudo apt install wireguard`

### "Port 8666 already in use"

Change port in Settings UI (`/settings.html`).

### Friends can't join party

- Check firewall (allow UDP 51820)
- Verify Party ID is correct
- Ensure both running same LANrage version
- Check NAT type (symmetric NATs need relay)

### High latency

- Check connection type in UI (direct vs relayed)
- If relayed, your NAT type may be difficult
- Try different network (mobile hotspot, etc.)
- Use wired connection instead of WiFi

### Game doesn't see other players

- Verify all players are in the same party
- Check that WireGuard interface is active
- Some games need specific ports (check game docs)
- Try game profile optimization (if available)

## Next Steps

- **Server Browser**: Browse and join game servers at `/servers.html`
- **Statistics**: View metrics and performance at `/dashboard.html`
- **Discord Integration**: Connect Discord bot at `/discord.html`
- **Settings**: Customize configuration at `/settings.html`

## Advanced Usage

### Running Tests

```bash
# All tests
.venv\Scripts\python.exe -m pytest tests/

# Specific test
.venv\Scripts\python.exe tests/test_nat.py
```

### Code Quality Checks

```bash
# Sort imports
.venv\Scripts\python.exe -m isort .

# Format code
.venv\Scripts\python.exe -m black .

# Lint
.venv\Scripts\python.exe -m ruff check --fix .
```

### Viewing Logs

```bash
# Network operations
type %USERPROFILE%\.lanrage\network.log

# Application logs
# (Currently logged to console)
```

## Getting Help

- **Documentation**: See `docs/` directory
- **GitHub Issues**: Report bugs and request features
- **Discord**: (Coming soon)

## Performance Tips

- Use wired connection for best latency
- Close bandwidth-heavy applications
- Direct P2P is always faster than relay
- Some ISPs throttle UDP traffic
- Geographic distance affects relay latency

## Security Notes

- All traffic encrypted with WireGuard
- Keys stored locally in `~/.lanrage/keys/`
- No central authority required
- Relays cannot decrypt traffic
- Party IDs are random and unguessable
