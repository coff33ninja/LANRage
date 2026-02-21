# LANrage User Guide

**Version**: 1.3.1  
**Last Updated**: February 21, 2026

## Welcome to LANrage! 🎮

LANrage makes online gaming feel like a LAN party. If it runs on LAN, it runs on LANrage - with minimal latency and zero configuration.

## Quick Start (90 seconds)

### 1. Install LANrage

```bash
# Clone the repository
git clone https://github.com/coff33ninja/LANRage.git
cd lanrage

# Run setup (installs dependencies)
python setup.py

# Activate virtual environment
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac
```

### 2. Start LANrage

```bash
python lanrage.py
```

You'll see:
```
🎮 LANrage v1.3.1
🌐 Web UI: http://localhost:8666
🔗 Virtual IP: 10.66.0.1
✓ Ready to party!
```

### 3. Open Web UI

Open your browser to: **http://localhost:8666**

### 4. Create or Join a Party

**To Host:**
1. Click "Create Party"
2. Enter a party name
3. Share the Party ID with friends

**To Join:**
1. Click "Join Party"
2. Enter the Party ID from your friend
3. Click "Connect"

### 5. Start Gaming!

Once connected, launch your game. LANrage automatically:
- Detects the game
- Optimizes network settings
- Emulates LAN broadcasts
- Connects you to other players

## How It Works

### Virtual Network

LANrage creates a virtual network interface (`lanrage0`) that makes all connected players appear to be on the same LAN:

```
Your Computer          Friend's Computer
10.66.0.1      <--->   10.66.0.2
    |                      |
    +------Internet--------+
```

### Connection Types

**Direct P2P** (Best - <5ms overhead)
- When both players have open NATs
- Direct connection between computers
- Lowest latency possible

**Relayed** (Good - <15ms overhead)
- When NAT prevents direct connection
- Traffic goes through relay server
- Still very low latency

**Automatic Fallback**
- LANrage tries direct first
- Falls back to relay if needed
- You don't need to configure anything

## Features

### 🎮 Game Detection

LANrage automatically detects 27+ popular games:
- Minecraft
- Terraria
- Stardew Valley
- Age of Empires II
- And many more!

When detected, LANrage:
- Optimizes network settings
- Enables broadcast emulation
- Adjusts keepalive timers
- Sets appropriate MTU

### 🔍 Server Browser

Find and join game servers hosted by other LANrage users:

1. Click "Server Browser" in web UI
2. Filter by game, players, or tags
3. Click "Join" to connect
4. Launch your game

**Hosting a Server:**
1. Start your game server
2. Click "Host Server" in LANrage
3. Fill in server details
4. Your server appears in the browser

### 📊 Statistics Dashboard

Monitor your connection quality:
- **Latency**: Real-time ping to each peer
- **Bandwidth**: Upload/download usage
- **Network Quality**: Overall connection score
- **Game Sessions**: Track your gaming history

### 💬 Discord Integration (Optional)

Connect LANrage to Discord for:
- Rich Presence (show what you're playing)
- Party invites via Discord
- Notifications when friends join

**Setup:**
1. Click "Settings" → "Discord"
2. Enter webhook URL (optional)
3. Enter invite link (optional)
4. Save

## Common Scenarios

### Scenario 1: Playing Minecraft with Friends

1. **Host starts LANrage**
   ```bash
   python lanrage.py
   ```

2. **Host creates party**
   - Open http://localhost:8666
   - Click "Create Party"
   - Name: "Minecraft Night"
   - Share Party ID: `abc123xyz`

3. **Friends join**
   - Each friend starts LANrage
   - Click "Join Party"
   - Enter Party ID: `abc123xyz`

4. **Start Minecraft**
   - Host: Start LAN world
   - Friends: See host's world in multiplayer list
   - Join and play!

### Scenario 2: Age of Empires II Tournament

1. **All players start LANrage and join same party**

2. **Host creates lobby in AoE2**
   - Set to "LAN" mode
   - Create game

3. **Players see lobby**
   - Appears in LAN game list
   - Join normally

4. **Play!**
   - LANrage handles all networking
   - Feels like true LAN

### Scenario 3: Terraria Server

1. **Host starts dedicated Terraria server**

2. **Host registers in LANrage Server Browser**
   - Click "Host Server"
   - Game: Terraria
   - Name: "My Awesome World"
   - Max Players: 8

3. **Friends find server**
   - Open Server Browser
   - Filter: Terraria
   - Click "Join"

4. **Connect in Terraria**
   - Use virtual IP shown in LANrage
   - Connect normally

## Troubleshooting

### "WireGuard not found"

**Problem**: WireGuard is not installed

**Solution**:
- **Windows**: Download from https://www.wireguard.com/install/
- **Linux**: `sudo apt install wireguard` (Ubuntu/Debian)
- **Mac**: `brew install wireguard-tools`

### "Permission denied"

**Problem**: LANrage needs admin/root privileges

**Solution**:
- **Windows**: Right-click → "Run as Administrator"
- **Linux/Mac**: `sudo python lanrage.py`

### "Cannot connect to peer"

**Problem**: NAT traversal failed

**Possible Causes**:
1. **Firewall blocking**: Allow LANrage through firewall
2. **Symmetric NAT**: Both players have difficult NATs
3. **No relay available**: Relay server is down

**Solutions**:
1. Check firewall settings
2. Try different network (mobile hotspot, etc.)
3. Wait for relay to come back online

### "High latency"

**Problem**: Connection is slow

**Check**:
1. **Connection type**: Direct or relayed?
   - Direct should be <5ms overhead
   - Relayed should be <15ms overhead

2. **Base latency**: What's your ping to friend normally?
   - LANrage adds minimal overhead
   - If base ping is 100ms, LANrage will be ~105ms

3. **Network congestion**: Other downloads/uploads?
   - Pause other network activity
   - Check bandwidth usage in LANrage stats

### "Game not detected"

**Problem**: LANrage doesn't recognize your game

**Solution**:
1. Check if game is in supported list
2. Manually configure game profile:
   ```bash
   # Edit ~/.lanrage/custom_profiles.json
   ```
3. Or request game support on GitHub

### "Party ID not working"

**Problem**: Cannot join party with ID

**Check**:
1. **Correct ID**: Double-check the Party ID
2. **Host online**: Is the host still running LANrage?
3. **Network**: Can you reach the internet?

**Solution**:
- Have host recreate party
- Try joining again
- Check control plane status

## Advanced Usage

### Custom Game Profiles

Create custom profiles for unsupported games:

```json
{
  "MyGame": {
    "name": "My Custom Game",
    "process_names": ["mygame.exe"],
    "broadcast_ports": [7777],
    "multicast_groups": [],
    "keepalive": 25,
    "mtu": 1420,
    "packet_priority": "high"
  }
}
```

Save to: `~/.lanrage/custom_profiles.json`

### Environment Variables

Configure LANrage via `.env` file:

```bash
# Mode: client or relay
LANRAGE_MODE=client

# API settings
LANRAGE_API_HOST=127.0.0.1
LANRAGE_API_PORT=8666

# Relay settings (for relay mode)
LANRAGE_RELAY_IP=your.public.ip
```

### Command Line Options

```bash
# Start in relay mode
python lanrage.py --mode relay

# Custom API port
python lanrage.py --port 9000

# Verbose logging
python lanrage.py --verbose

# Show version
python lanrage.py --version
```

## Best Practices

### For Best Performance

1. **Use wired connection** when possible
2. **Close bandwidth-heavy apps** (downloads, streaming)
3. **Check connection type** (prefer direct over relayed)
4. **Monitor latency** in statistics dashboard
5. **Update LANrage** regularly for improvements

### For Hosting Parties

1. **Stable connection** required
2. **Keep LANrage running** while others play
3. **Share Party ID** securely with friends only
4. **Monitor connections** in web UI
5. **Check server browser** if hosting public games

### For Security

1. **Only join trusted parties** (Party IDs are like passwords)
2. **Use firewall** to block unwanted connections
3. **Keep WireGuard updated** for security patches
4. **Don't share Party IDs publicly** unless hosting public games
5. **Monitor connected peers** in web UI

## Getting Help

### Documentation

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Testing**: [TESTING.md](TESTING.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API Reference**: [API.md](API.md)

### Community

- **GitHub Issues**: Report bugs and request features
- **Discord**: Join our community (link in README)
- **Reddit**: r/lanrage for discussions

### Support

- **GitHub Discussions**: Ask questions
- **Email**: support@lanrage.dev
- **Documentation**: https://docs.lanrage.dev

## FAQ

### Is LANrage free?

Yes! LANrage is open source and completely free.

### Does it work with all games?

LANrage works with any game that supports LAN multiplayer. We have optimized profiles for 27+ popular games, and you can create custom profiles for others.

### Is it safe?

Yes! LANrage uses WireGuard, a modern and secure VPN protocol. All traffic is encrypted end-to-end.

### What's the latency?

- Direct P2P: <5ms overhead
- Relayed: <15ms overhead
- Your base ping to friends + LANrage overhead = total latency

### How many players can join?

LANrage supports up to 255 players in a single party (10.66.0.1 - 10.66.0.255). Most games limit this further.

### Can I host a dedicated server?

Yes! Start your game's dedicated server, then register it in LANrage's Server Browser so others can find it.

### Does it work on mobile?

Not yet. LANrage currently supports Windows, Linux, and Mac. Mobile support is planned.

### Can I use it for non-gaming purposes?

Yes! LANrage creates a virtual LAN, so any LAN-based application will work (file sharing, development, etc.).

## What's Next?

Now that you know the basics:

1. **Try it out**: Create a party and test with friends
2. **Explore features**: Server browser, statistics, Discord integration
3. **Join community**: Share feedback and help others
4. **Contribute**: LANrage is open source!

Happy gaming! 🎮

---

**Need more help?** Check out [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions to common problems.
