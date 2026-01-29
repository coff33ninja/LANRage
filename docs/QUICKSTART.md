# LANrage Quick Start Guide

## For the Impatient

```bash
python setup.py
.venv\Scripts\activate.bat
python lanrage.py
# Open http://localhost:8666
```

Done. Now read the rest if you want details.

## Prerequisites

- **Python 3.12+** (not 3.11, not 3.10, 3.12+)
- **uv** (Python package manager)
- **Windows 10/11** or **Linux** (Ubuntu/Debian)
- **Admin rights** (for network interface creation)

### Installing uv

**Windows (PowerShell)**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/Mac**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/lanrage.git
cd lanrage
```

### 2. Run Setup

```bash
python setup.py
```

This will:
- Create virtual environment
- Install dependencies
- Generate config files
- Create WireGuard keys

### 3. Activate Environment

**Windows (CMD)**:
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell)**:
```powershell
.venv\Scripts\Activate.ps1
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

You should see:
```
🔥 LANrage - If it runs on LAN, it runs on LANrage
============================================================
✓ Config loaded (mode: client)
✓ Network initialized (interface: lanrage0)
✓ Party manager ready
✓ Starting API server on 127.0.0.1:8666
```

### Open the UI

Open your browser to: `http://localhost:8666`

## Creating a Party

1. Click **"CREATE PARTY"**
2. Enter a party name (e.g., "Gaming Session")
3. Note the **Party ID** (e.g., `a3f7c2`)
4. Share this ID with friends

## Joining a Party

1. Click **"JOIN PARTY"**
2. Enter the **Party ID** from your friend
3. Enter your name
4. Click **"JOIN"**

## Playing Games

Once in a party:
1. Launch your game
2. Look for LAN/Local multiplayer
3. Your friends should appear as "local" players
4. Play!

## Troubleshooting

### "Permission denied" on startup

**Windows**: Run as Administrator
**Linux**: Use `sudo` or add user to `netdev` group

### "Port 8666 already in use"

Change the port in `.env`:
```
LANRAGE_API_PORT=8667
```

### "WireGuard not found"

**Windows**: Install from https://www.wireguard.com/install/
**Linux**: `sudo apt install wireguard`

### Friends can't join party

- Check firewall (allow UDP 51820)
- Verify Party ID is correct
- Ensure both running same LANrage version

### High latency

- Check connection type in UI
- If "relayed", your NAT is being difficult
- Try different network (mobile hotspot, etc.)

### Game doesn't see other players

- Some games need specific ports
- Check game documentation
- Try game profile (TODO)

## Advanced Usage

### Custom Configuration

Edit `.env`:
```bash
# Change API port
LANRAGE_API_PORT=9000

# Change virtual subnet
LANRAGE_VIRTUAL_SUBNET=10.99.0.0/16

# Use custom relay
LANRAGE_RELAY_IP=your.relay.ip
```

### Running as Service

**Windows** (TODO):
```powershell
# Install as service
python lanrage.py --install-service
```

**Linux**:
```bash
# Copy systemd unit
sudo cp docs/lanrage.service /etc/systemd/system/
sudo systemctl enable lanrage
sudo systemctl start lanrage
```

### Monitoring

Check status:
```bash
curl http://localhost:8666/status
```

View logs:
```bash
tail -f ~/.lanrage/logs/lanrage.log
```

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [ROADMAP.md](ROADMAP.md) for upcoming features
- Set up a relay: [ORACLE_RELAY.md](ORACLE_RELAY.md)

## Getting Help

- GitHub Issues: Bug reports
- Discord: (TODO)
- Reddit: (TODO)

## Tips

- Lower ping = better experience
- Direct P2P is always best
- Relays add ~10-15ms latency
- Close other network apps
- Use wired connection if possible
- Some ISPs hate UDP (switch ISP)

## Known Limitations

- No mobile support yet
- No game profiles yet
- Control plane not implemented
- NAT traversal is basic
- Windows only tested on 10/11

## Performance Expectations

**Good**:
- Direct P2P: <5ms overhead
- Same-region relay: <15ms overhead
- 50+ FPS in most games

**Bad**:
- Cross-continent relay: 50ms+ overhead
- Cellular connection: Variable
- Strict NAT: May need relay

## Security Notes

- All traffic encrypted (WireGuard)
- Keys stored locally
- No central authority
- Relays can't decrypt
- No logging by default

## Uninstalling

```bash
# Stop service
# (Ctrl+C if running in terminal)

# Remove files
rm -rf ~/.lanrage
rm -rf .venv

# Remove repo
cd ..
rm -rf lanrage
```

## FAQ

**Q: Is this legal?**
A: Yes. It's just a VPN.

**Q: Will I get banned?**
A: Depends on game. Most don't care about VPNs.

**Q: Does it work with [game]?**
A: Probably. Try it and report back.

**Q: Why not just use Hamachi?**
A: Hamachi is dead. Long live LANrage.

**Q: Can I use this for non-gaming?**
A: Sure, but Tailscale is better for that.

**Q: How much does it cost?**
A: Free (for now). Paid tier later.

**Q: Can I self-host everything?**
A: Yes! That's the point.

**Q: Is my data safe?**
A: Yes. WireGuard encryption + no logging.

**Q: Why Python?**
A: Fast prototyping. May rewrite in Rust later.

**Q: Can I contribute?**
A: Not yet. Solo project for now.
