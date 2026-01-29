# LANrage Product Overview

LANrage is a zero-config mesh VPN optimized for gaming that makes online gaming feel like a LAN party.

## Core Value Proposition

"If it runs on LAN, it runs on LANrage" - enables LAN games to work over the internet with minimal latency and zero configuration.

## Target Users

Gamers who want to play LAN games online without dealing with port forwarding, NAT traversal, or complex VPN setup.

## Key Features

- One-click party creation and joining
- Direct P2P connections when possible (0ms overhead)
- Smart relay fallback for difficult NATs (<15ms overhead)
- LAN broadcast emulation for old games
- Game-aware profiles for auto-optimization
- WireGuard-based security
- Web UI for simple control

## Design Philosophy

1. **Gamers first** - Not enterprises or developers
2. **Latency obsessed** - Every millisecond matters
3. **Zero config** - If it takes >90 seconds, it's broken
4. **Open source** - No vendor lock-in
5. **Honest** - No marketing BS

## Current Status

Phase 3 complete - core networking features implemented and tested. Working features include WireGuard interface management, NAT traversal, control plane, broadcast emulation, game detection, relay server, and multi-peer mesh networking.

## Network Architecture

- Virtual subnet: 10.66.0.0/16
- Interface: lanrage0
- Protocol: WireGuard (UDP-first)
- Connection priority: Direct P2P → Same-region relay → Nearest relay → TCP tunnel (last resort)
