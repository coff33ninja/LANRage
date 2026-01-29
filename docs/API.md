# REST API Reference

The LANrage REST API (`api/server.py`) provides HTTP endpoints for controlling LANrage, monitoring metrics, managing Discord integration, browsing servers, and configuring settings.

## Overview

- **Framework**: FastAPI
- **Default Host**: `127.0.0.1` (localhost only)
- **Default Port**: `8666`
- **CORS**: Enabled for all origins (local web UI)
- **Static Files**: Served from `/static` directory
- **Documentation**: Auto-generated at `/docs` (Swagger UI)

---

## Base Endpoints

### GET /api

Health check endpoint.

**Response:**
```json
{
    "status": "ok",
    "service": "LANrage"
}
```

---

### GET /

Serve the web UI.

**Response:** HTML file (`static/index.html`)

---

## Party Management

### GET /status

Get current party status.

**Response:**
```json
{
    "party_id": "party-123",
    "party_name": "Friday Night Gaming",
    "host_peer_id": "peer-1",
    "peers": [
        {
            "id": "peer-1",
            "name": "Alice",
            "virtual_ip": "10.66.0.2",
            "status": "connected"
        }
    ],
    "created_at": 1706544000.0
}
```

---

### POST /party/create

Create a new party.

**Request Body:**
```json
{
    "name": "Friday Night Gaming"
}
```

**Response:**
```json
{
    "party_id": "party-123",
    "party": {
        "id": "party-123",
        "name": "Friday Night Gaming",
        "host_peer_id": "peer-1",
        "peers": {...},
        "created_at": 1706544000.0
    }
}
```

---

### POST /party/join

Join an existing party.

**Request Body:**
```json
{
    "party_id": "party-123",
    "peer_name": "Bob"
}
```

**Response:**
```json
{
    "party": {
        "id": "party-123",
        "name": "Friday Night Gaming",
        ...
    }
}
```

**Status Codes:**
- `200` - Success
- `501` - Not yet implemented

---

### POST /party/leave

Leave current party.

**Response:**
```json
{
    "status": "left"
}
```

---

## Metrics Endpoints

### GET /api/metrics/summary

Get overall metrics summary.

**Response:**
```json
{
    "peers": [
        {
            "peer_id": "peer-1",
            "peer_name": "Alice",
            "status": "connected",
            "latency": {
                "current": 45.2,
                "average": 48.5,
                "min": 42.1,
                "max": 67.3
            },
            "bandwidth": {
                "sent": 1048576,
                "received": 2097152
            },
            "packets": {
                "sent": 1024,
                "received": 2048
            },
            "uptime": 3600.0,
            "last_seen": 1706544000.0
        }
    ],
    "system": {
        "cpu": {
            "current": 15.2,
            "average": 12.8,
            "max": 45.6
        },
        "memory": {
            "current": 42.3,
            "average": 40.1,
            "max": 48.9
        },
        "network": {
            "sent_rate": 102400,
            "recv_rate": 204800,
            "total_sent": 3686400,
            "total_recv": 7372800
        }
    },
    "network_quality": 87.5
}
```

---

### GET /api/metrics/peers

Get metrics for all peers.

**Response:**
```json
{
    "peers": [...]  // Same format as /api/metrics/summary
}
```

---

### GET /api/metrics/peers/{peer_id}

Get metrics for a specific peer.

**Parameters:**
- `peer_id` (path): Peer identifier

**Response:**
```json
{
    "peer_id": "peer-1",
    "peer_name": "Alice",
    "status": "connected",
    "latency": {...},
    "bandwidth": {...},
    "packets": {...},
    "uptime": 3600.0,
    "last_seen": 1706544000.0
}
```

**Status Codes:**
- `200` - Success
- `404` - Peer not found

---

### GET /api/metrics/peers/{peer_id}/latency

Get latency history for a peer.

**Parameters:**
- `peer_id` (path): Peer identifier
- `duration` (query): Duration in seconds (default: 3600)

**Example:** `/api/metrics/peers/peer-1/latency?duration=1800`

**Response:**
```json
{
    "peer_id": "peer-1",
    "duration": 1800,
    "data": [
        {"timestamp": 1706544000.0, "value": 45.2},
        {"timestamp": 1706544010.0, "value": 46.1},
        ...
    ]
}
```

---

### GET /api/metrics/system

Get system metrics summary.

**Response:**
```json
{
    "cpu": {
        "current": 15.2,
        "average": 12.8,
        "max": 45.6
    },
    "memory": {
        "current": 42.3,
        "average": 40.1,
        "max": 48.9
    },
    "network": {
        "sent_rate": 102400,
        "recv_rate": 204800,
        "total_sent": 3686400,
        "total_recv": 7372800
    }
}
```

---

### GET /api/metrics/system/history

Get system metrics history.

**Parameters:**
- `duration` (query): Duration in seconds (default: 3600)

**Example:** `/api/metrics/system/history?duration=1800`

**Response:**
```json
{
    "duration": 1800,
    "data": {
        "cpu": [
            {"timestamp": 1706544000.0, "value": 15.2},
            ...
        ],
        "memory": [...],
        "network_sent": [...],
        "network_received": [...]
    }
}
```

---

### GET /api/metrics/sessions

Get recent game sessions.

**Parameters:**
- `limit` (query): Maximum sessions to return (default: 10)

**Example:** `/api/metrics/sessions?limit=5`

**Response:**
```json
{
    "sessions": [
        {
            "game_id": "minecraft-123",
            "game_name": "Minecraft",
            "started_at": 1706544000.0,
            "ended_at": 1706547600.0,
            "duration": 3600.0,
            "peers": ["peer-1", "peer-2", "peer-3"],
            "latency": {
                "average": 48.5,
                "min": 42.1,
                "max": 67.3
            }
        }
    ]
}
```

---

## Discord Integration

### POST /api/discord/webhook

Set Discord webhook URL.

**Request Body:**
```json
{
    "webhook_url": "https://discord.com/api/webhooks/123456789/abcdefg"
}
```

**Response:**
```json
{
    "status": "ok",
    "message": "Discord webhook configured"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid webhook URL format

---

### POST /api/discord/invite

Set Discord invite URL.

**Request Body:**
```json
{
    "invite_url": "https://discord.gg/abc123"
}
```

**Response:**
```json
{
    "status": "ok",
    "message": "Discord invite configured"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid invite URL format

---

### GET /api/discord/status

Get Discord integration status.

**Response:**
```json
{
    "webhook_configured": true,
    "invite_configured": true,
    "invite_url": "https://discord.gg/abc123",
    "rich_presence": true
}
```

---

### GET /api/discord/instructions

Get setup instructions.

**Response:**
```json
{
    "webhook": "To set up Discord notifications:\n\n1. Open your Discord server...",
    "invite": "To set up Discord voice chat:\n\n1. Open your Discord server..."
}
```

---

### POST /api/discord/test

Send test notification.

**Response:**
```json
{
    "status": "ok",
    "message": "Test notification sent"
}
```

**Status Codes:**
- `200` - Success
- `400` - Webhook not configured

---

## Server Browser

### GET /api/servers

List all game servers with optional filtering.

**Parameters:**
- `game` (query): Filter by game name
- `hide_full` (query): Hide full servers (boolean)
- `hide_empty` (query): Hide empty servers (boolean)
- `hide_password` (query): Hide password-protected servers (boolean)
- `tags` (query): Filter by tags (comma-separated)
- `search` (query): Search in server name/game/host

**Example:** `/api/servers?game=Minecraft&hide_full=true&tags=Vanilla,PvE`

**Response:**
```json
{
    "servers": [
        {
            "id": "server-1",
            "name": "Alice's Server",
            "game": "Minecraft",
            "host_peer_id": "peer-1",
            "host_peer_name": "Alice",
            "host_ip": "10.66.0.2",
            "max_players": 10,
            "current_players": 5,
            "map_name": "World 1",
            "game_mode": "Survival",
            "password_protected": false,
            "tags": ["Vanilla", "PvE"],
            "created_at": 1706544000.0,
            "last_heartbeat": 1706544030.0,
            "latency_ms": 45.2,
            "is_full": false,
            "age_seconds": 30.0
        }
    ],
    "count": 1,
    "stats": {
        "total_servers": 15,
        "total_players": 42,
        "unique_games": 5,
        "games": ["Minecraft", "Terraria", ...],
        "favorites": 3
    }
}
```

---

### POST /api/servers

Register a new game server.

**Request Body:**
```json
{
    "server_id": "my-server-1",
    "name": "My Awesome Server",
    "game": "Minecraft",
    "max_players": 10,
    "current_players": 2,
    "map_name": "World 1",
    "game_mode": "Survival",
    "password_protected": false,
    "tags": ["Vanilla", "PvE"]
}
```

**Response:**
```json
{
    "status": "ok",
    "server": {...}  // Full server object
}
```

**Status Codes:**
- `200` - Success
- `400` - Must be in a party to register server

---

### GET /api/servers/{server_id}

Get details for a specific server.

**Parameters:**
- `server_id` (path): Server identifier

**Response:**
```json
{
    "id": "server-1",
    "name": "Alice's Server",
    ...
}
```

**Status Codes:**
- `200` - Success
- `404` - Server not found

---

### DELETE /api/servers/{server_id}

Unregister a game server.

**Parameters:**
- `server_id` (path): Server identifier

**Response:**
```json
{
    "status": "ok",
    "message": "Server unregistered"
}
```

**Status Codes:**
- `200` - Success
- `404` - Server not found

---

### POST /api/servers/{server_id}/heartbeat

Update server heartbeat.

**Parameters:**
- `server_id` (path): Server identifier

**Response:**
```json
{
    "status": "ok",
    "message": "Heartbeat updated"
}
```

**Status Codes:**
- `200` - Success
- `404` - Server not found

---

### POST /api/servers/{server_id}/players

Update server player count.

**Parameters:**
- `server_id` (path): Server identifier

**Request Body:**
```json
{
    "current_players": 7
}
```

**Response:**
```json
{
    "status": "ok",
    "message": "Player count updated"
}
```

**Status Codes:**
- `200` - Success
- `404` - Server not found

---

### POST /api/servers/{server_id}/join

Join a game server.

**Parameters:**
- `server_id` (path): Server identifier

**Response:**
```json
{
    "status": "ok",
    "message": "Join server by connecting to host",
    "server": {...},
    "host_ip": "10.66.0.2"
}
```

**Status Codes:**
- `200` - Success
- `400` - Server is full
- `404` - Server not found

---

### POST /api/servers/{server_id}/favorite

Add server to favorites.

**Parameters:**
- `server_id` (path): Server identifier

**Response:**
```json
{
    "status": "ok",
    "message": "Server added to favorites"
}
```

**Status Codes:**
- `200` - Success
- `404` - Server not found

---

### DELETE /api/servers/{server_id}/favorite

Remove server from favorites.

**Parameters:**
- `server_id` (path): Server identifier

**Response:**
```json
{
    "status": "ok",
    "message": "Server removed from favorites"
}
```

---

### GET /api/servers/{server_id}/latency

Measure latency to a server.

**Parameters:**
- `server_id` (path): Server identifier

**Response:**
```json
{
    "server_id": "server-1",
    "latency_ms": 45.2
}
```

**Status Codes:**
- `200` - Success
- `500` - Failed to measure latency

---

### GET /api/servers/stats

Get server browser statistics.

**Response:**
```json
{
    "total_servers": 15,
    "total_players": 42,
    "unique_games": 5,
    "games": ["Minecraft", "Terraria", "Valheim", ...],
    "favorites": 3
}
```

---

### GET /api/games

Get list of games with active servers.

**Response:**
```json
{
    "games": ["Minecraft", "Terraria", "Valheim", ...],
    "count": 5
}
```

---

## Settings Management

### GET /api/settings

Get all settings.

**Response:**
```json
{
    "mode": "client",
    "peer_name": "Alice",
    "interface_name": "lanrage0",
    "virtual_subnet": "10.66.0.0/16",
    "wireguard_keepalive": 25,
    "auto_optimize_games": true,
    "enable_broadcast": true,
    "enable_discord": false,
    "enable_metrics": true,
    "relay_public_ip": null,
    "relay_port": 51820,
    "max_clients": 100,
    "api_host": "127.0.0.1",
    "api_port": 8666,
    "control_server": "https://control.lanrage.dev"
}
```

---

### POST /api/settings

Update settings.

**Request Body:**
```json
{
    "mode": "client",
    "peer_name": "Bob",
    "enable_discord": true,
    "wireguard_keepalive": 30
}
```

**Response:**
```json
{
    "status": "ok",
    "message": "Settings updated",
    "updated": ["mode", "peer_name", "enable_discord", "wireguard_keepalive"]
}
```

---

### POST /api/settings/reset

Reset settings to defaults.

**Response:**
```json
{
    "status": "ok",
    "message": "Settings reset to defaults"
}
```

---

### GET /api/settings/configs

Get all saved configurations.

**Response:**
```json
[
    {
        "id": 1,
        "name": "Home Server",
        "mode": "relay",
        "config": {...},
        "is_active": true,
        "created_at": 1706544000.0
    }
]
```

---

### POST /api/settings/configs

Save a new configuration.

**Request Body:**
```json
{
    "name": "Home Server",
    "mode": "relay",
    "config": {
        "relay_port": 51820,
        "max_clients": 50
    }
}
```

**Response:**
```json
{
    "status": "ok",
    "message": "Configuration saved",
    "id": 1
}
```

---

### POST /api/settings/configs/{config_id}/activate

Activate a saved configuration.

**Parameters:**
- `config_id` (path): Configuration ID

**Response:**
```json
{
    "status": "ok",
    "message": "Configuration activated"
}
```

**Status Codes:**
- `200` - Success
- `404` - Configuration not found

---

### DELETE /api/settings/configs/{config_id}

Delete a saved configuration.

**Parameters:**
- `config_id` (path): Configuration ID

**Response:**
```json
{
    "status": "ok",
    "message": "Configuration deleted"
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
    "detail": "Error message"
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
- `501` - Not Implemented

---

## Starting the API Server

The API server is started automatically by `lanrage.py`:

```python
from core.config import Config
from core.party import PartyManager
from core.network import NetworkManager
from api.server import start_api_server

config = Config.load()
party = PartyManager(config)
network = NetworkManager(config)

# Start API server
await start_api_server(
    config=config,
    party=party,
    network=network,
    metrics=metrics_collector,
    discord=discord_integration,
    browser=server_browser
)
```

---

## CORS Configuration

CORS is enabled for all origins to support local web UI:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Security Note:** This is safe for localhost-only API. For public APIs, restrict origins.

---

## Auto-Generated Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8666/docs
- **ReDoc**: http://localhost:8666/redoc
- **OpenAPI JSON**: http://localhost:8666/openapi.json

---

## Future Enhancements

1. **Authentication**: API keys or JWT tokens
2. **Rate Limiting**: Prevent API abuse
3. **WebSocket**: Real-time updates
4. **Pagination**: For large result sets
5. **Filtering**: Advanced query syntax
6. **Caching**: Redis for frequently accessed data
7. **Versioning**: API version in URL (e.g., `/api/v1/`)
8. **GraphQL**: Alternative to REST
9. **gRPC**: High-performance RPC
10. **Metrics Export**: Prometheus endpoint
