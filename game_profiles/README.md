# LANrage Game Profiles

Game profiles are organized by genre in JSON files. Each profile defines how LANrage optimizes for a specific game.

## Directory Structure

```
game_profiles/
├── README.md                    # This file
├── sandbox.json                 # Sandbox/Crafting games
├── survival.json                # Survival games
├── coop.json                    # Co-op action games
├── party.json                   # Party/Casual games
├── competitive.json             # Competitive games
├── strategy.json                # Strategy/RTS games
├── fps.json                     # First-person shooter games
├── racing.json                  # Racing/Driving games
├── rpg.json                     # Role-playing games
├── moba.json                    # MOBA games
├── sports.json                  # Sports games
├── horror.json                  # Horror games
└── custom/                      # User-added custom profiles
    ├── call_of_duty.json
    ├── far_cry.json
    ├── need_for_speed.json
    └── example.json
```

## Profile Format

Each JSON file contains game profiles with the following structure:

```json
{
  "game_id": {
    "name": "Game Name",
    "executable": "game.exe",
    "ports": [7777, 7778],
    "protocol": "udp",
    "broadcast": true,
    "multicast": false,
    "keepalive": 15,
    "mtu": 1420,
    "description": "Game description",
    "low_latency": true,
    "high_bandwidth": false,
    "packet_priority": "high"
  }
}
```

## Field Descriptions

- **name**: Display name of the game
- **executable**: Process name (e.g., "game.exe" on Windows)
- **ports**: List of ports used by the game
- **protocol**: "udp", "tcp", or "both"
- **broadcast**: Whether game uses LAN broadcast discovery
- **multicast**: Whether game uses multicast discovery
- **keepalive**: WireGuard keepalive interval in seconds (10-30)
- **mtu**: Optimal MTU size (usually 1420)
- **description**: Brief description of the game
- **low_latency**: Whether game requires low latency (FPS, racing, etc.)
- **high_bandwidth**: Whether game uses high bandwidth (streaming, large worlds)
- **packet_priority**: "low", "medium", or "high" for QoS

## Adding Custom Games

1. Create a JSON file in `game_profiles/custom/`
2. Use the format above
3. Restart LANrage to load the profile

Example: `game_profiles/custom/my_game.json`

```json
{
  "my_game": {
    "name": "My Awesome Game",
    "executable": "MyGame.exe",
    "ports": [12345],
    "protocol": "udp",
    "broadcast": true,
    "multicast": false,
    "keepalive": 20,
    "mtu": 1420,
    "description": "My custom game profile",
    "low_latency": false,
    "high_bandwidth": false,
    "packet_priority": "medium"
  }
}
```

## Genre Guidelines

### Sandbox/Crafting
- **Latency**: Medium (not critical)
- **Bandwidth**: Low to Medium
- **Priority**: Medium
- **Examples**: Minecraft, Terraria, Factorio

### Survival
- **Latency**: Medium
- **Bandwidth**: Medium to High
- **Priority**: Medium
- **Examples**: Rust, ARK, 7 Days to Die

### Co-op Action
- **Latency**: High (critical for combat)
- **Bandwidth**: Medium
- **Priority**: High
- **Examples**: Deep Rock Galactic, Left 4 Dead 2

### Party/Casual
- **Latency**: Low to Medium
- **Bandwidth**: Low
- **Priority**: Medium
- **Examples**: Among Us, Fall Guys, Gang Beasts

### Competitive
- **Latency**: Critical (every ms counts)
- **Bandwidth**: Medium to High
- **Priority**: High
- **Examples**: CS:GO, Rocket League, Brawlhalla

### Strategy/RTS
- **Latency**: High (important for real-time)
- **Bandwidth**: Low
- **Priority**: High
- **Examples**: Age of Empires II, Warcraft III

### FPS (First-Person Shooter)
- **Latency**: Critical (every ms counts)
- **Bandwidth**: High
- **Priority**: High
- **Examples**: Valorant, Apex Legends, COD Warzone, Battlefield, Halo Infinite, Overwatch

### Racing
- **Latency**: Critical (precision timing)
- **Bandwidth**: High
- **Priority**: High
- **Examples**: Forza Horizon, Gran Turismo, Assetto Corsa, iRacing, Trackmania

### RPG (Role-Playing Games)
- **Latency**: Medium
- **Bandwidth**: Medium to High
- **Priority**: Medium
- **Examples**: Diablo IV, Path of Exile, Divinity: Original Sin 2, Baldur's Gate 3, Monster Hunter

### MOBA (Multiplayer Online Battle Arena)
- **Latency**: Critical (competitive gameplay)
- **Bandwidth**: High
- **Priority**: High
- **Examples**: League of Legends, Dota 2, Smite

### Sports
- **Latency**: High (timing matters)
- **Bandwidth**: High
- **Priority**: High
- **Examples**: EA Sports FC (FIFA), NBA 2K, Madden NFL

### Horror
- **Latency**: Medium to High
- **Bandwidth**: Low to Medium
- **Priority**: Medium to High
- **Examples**: Dead by Daylight, The Forest, Lethal Company, Content Warning

## Tips

- **Keepalive**: Lower for fast-paced games (10s), higher for turn-based (25s)
- **MTU**: Keep at 1420 unless you know the game needs different
- **Broadcast**: Enable if game has LAN discovery feature
- **Protocol**: Check game documentation or use Wireshark to determine
