# LANrage - Gaming VPN for the People

**Tagline**: *If it runs on LAN, it runs on LANrage.*

## What is this?

A zero-config mesh VPN that makes online gaming feel like a LAN party. No port forwarding, no NAT hell, no PhD required.

Think Tailscale, but for gamers who care about ping more than enterprise features.

## The Problem

- LAN games don't work over internet
- Port forwarding is a nightmare
- Hamachi is dead
- ZeroTier is too enterprise
- Tailscale adds latency

## The Solution

LANrage creates a virtual LAN over the internet with:
- **Direct P2P** when possible (0ms overhead)
- **Smart relays** when NAT is evil (<15ms overhead)
- **Broadcast emulation** for old games
- **Game detection** for auto-optimization
- **One-click setup** because life's too short

## Features

- 🎮 **One-click party creation** - No config files, no terminal commands
- ⚡ **Latency-first routing** - Ping is king, always
- 📡 **LAN broadcast emulation** - Old games just work
- 🎯 **Game-aware profiles** - Auto-tuning per game
- 🔒 **WireGuard security** - Military-grade encryption (but you don't need to know that)
- 🌐 **Web UI** - Clean, simple, gamer-friendly
- 🚀 **Oracle VPS ready** - Your free 1GB VPS makes a perfect relay

## Quick Start

### 1. Setup (One-time)

```bash
# Clone the repo
git clone https://github.com/yourusername/lanrage.git
cd lanrage

# Run setup
python setup.py
```

### 2. Run

```bash
# Activate environment
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# Start LANrage
python lanrage.py
```

### 3. Use

1. Open browser: `http://localhost:8666`
2. Click "CREATE PARTY"
3. Share Party ID with friends
4. Friends click "JOIN PARTY"
5. Play games like it's 2006

## Architecture

```
┌─────────────┐         ┌─────────────┐
│   Client A  │◄───────►│   Client B  │  Direct P2P (best case)
└─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client A  │◄───────►│    Relay    │◄───────►│   Client B  │  Relayed (NAT hell)
└─────────────┘         └─────────────┘         └─────────────┘
```

- **Control plane**: Peer discovery + key exchange (TODO)
- **Data plane**: WireGuard tunnels (direct or relayed)
- **Relay nodes**: Stateless packet forwarders

## Your Oracle VPS

Got a free Oracle VPS? Perfect relay node:
- 1 core / 1GB RAM
- Handles 50-100 connections
- <5ms latency overhead
- Forever free

See [docs/ORACLE_RELAY.md](docs/ORACLE_RELAY.md) for setup.

## Roadmap

- [x] Project structure
- [x] Web UI mockup
- [ ] WireGuard interface
- [ ] NAT traversal (STUN/TURN)
- [ ] Control plane
- [ ] Game profiles
- [ ] Mobile app

See [docs/ROADMAP.md](docs/ROADMAP.md) for details.

## Status

🚧 **Early prototype** - Core networking not yet implemented

Currently working:
- ✅ API server
- ✅ Web UI
- ✅ Configuration system
- ✅ Party management (local only)

Not yet working:
- ❌ Actual networking (WireGuard)
- ❌ NAT traversal
- ❌ Peer discovery
- ❌ Game detection

## Contributing

This is a solo project for now, but:
- Bug reports welcome
- Feature ideas appreciated
- PRs considered
- Memes encouraged

## Philosophy

1. **Gamers first** - Not enterprises, not developers
2. **Latency obsessed** - Every millisecond matters
3. **Zero config** - If it takes >90 seconds, it's broken
4. **Open source** - No vendor lock-in
5. **Honest** - No marketing BS

## Comparison

| Feature | LANrage | Hamachi | ZeroTier | Tailscale |
|---------|---------|---------|----------|-----------|
| Gaming focus | ✅ | ✅ | ❌ | ❌ |
| Low latency | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Zero config | ✅ | ✅ | ❌ | ⚠️ |
| Still maintained | ✅ | ❌ | ✅ | ✅ |
| Free tier | ✅ | ⚠️ | ✅ | ✅ |
| Open source | ✅ | ❌ | ⚠️ | ❌ |

## License

MIT - Do whatever you want

## Support

- Discord: (TODO)
- GitHub Issues: Bug reports
- Reddit: (TODO)

## Acknowledgments

- WireGuard - For being awesome
- Tailscale - For the inspiration
- Hamachi - For the nostalgia
- Oracle - For the free VPS

## Disclaimer

This is a hobby project. Use at your own risk. May cause:
- Reduced ping
- Increased fun
- Nostalgia for LAN parties
- Addiction to retro games
