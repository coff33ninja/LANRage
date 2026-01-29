# LANrage Product Overview

LANrage is a zero-config mesh VPN optimized for gaming that makes online gaming feel like a LAN party.

## Core Value Proposition

"If it runs on LAN, it runs on LANrage" - enables LAN games to work over the internet with minimal latency and zero configuration.

## Target Users

Gamers who want to play LAN games online without dealing with port forwarding, NAT traversal, or complex VPN setup.

## Key Features

- 🎮 **One-click party creation and joining** - No config files, no terminal commands
- ⚡ **Direct P2P connections** - <3ms overhead (exceeds <5ms target)
- 🔄 **Smart relay fallback** - <12ms overhead (exceeds <15ms target)
- 📡 **LAN broadcast emulation** - Old games just work
- 🎯 **Game-aware profiles** - Auto-optimization for 27 games
- 🔒 **WireGuard-based security** - Military-grade encryption
- 🌐 **Web UI** - Dashboard, settings, server browser, Discord setup
- 💬 **Discord integration** - Webhooks and Rich Presence
- 📊 **Statistics dashboard** - Real-time metrics and performance tracking
- 🎮 **Server browser** - Discover and host game servers
- 🚀 **Production ready** - 88% test coverage, 96% specific error handling
- 💾 **SQLite persistence** - Settings and control plane state management

## Design Philosophy

1. **Gamers first** - Not enterprises or developers
2. **Latency obsessed** - Every millisecond matters
3. **Zero config** - If it takes >90 seconds, it's broken
4. **Open source** - No vendor lock-in
5. **Honest** - No marketing BS

## Current Status

**v1.0 - PRODUCTION READY** (Released January 29, 2026)

All core features implemented, tested (88% coverage), and documented (1650+ lines). Ready for public release and real-world use. Features include WireGuard interface management, NAT traversal, control plane with SQLite persistence, broadcast/multicast emulation, game detection (27 games), relay server, multi-peer mesh networking, Discord integration, server browser, QoS implementation, and comprehensive error handling (96% specific exceptions).

## Network Architecture

- Virtual subnet: 10.66.0.0/16
- Interface: lanrage0
- Protocol: WireGuard (UDP-first)
- Connection priority: Direct P2P → Same-region relay → Nearest relay → TCP tunnel (last resort)
- Control plane: SQLite-based local (v1.0), WebSocket remote (v1.1+)
- State persistence: SQLite for settings and control plane

## Supported Games (27)

### Strategy/RTS (4)
- Minecraft Java Edition
- Terraria
- Age of Empires II
- Warcraft III

### Survival/Crafting (7)
- Rust
- ARK: Survival Evolved
- 7 Days to Die
- Satisfactory
- The Forest
- Valheim
- Factorio

### Co-op/Action (6)
- Deep Rock Galactic
- Risk of Rain 2
- Payday 2
- Killing Floor 2
- Vermintide 2
- Left 4 Dead 2

### Party/Casual (7)
- Phasmophobia
- Among Us
- Fall Guys
- Gang Beasts
- Pummel Party
- Stardew Valley
- Don't Starve Together

### Competitive (3)
- Counter-Strike: Global Offensive
- Rocket League
- Brawlhalla

Plus support for custom game profiles via JSON!
