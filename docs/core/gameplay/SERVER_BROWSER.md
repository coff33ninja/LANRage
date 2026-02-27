# Server Browser

Game server advertisement, discovery, filtering, and join-assist behavior for LANrage.

## Scope

This document covers `core/gameplay/server_browser.py` behavior and related API/UI usage.

Related docs:
- [API](API.md)
- [Party Management](/docs/core/control_plane/PARTY.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)

## Responsibilities

Server browser responsibilities:
- register/update/unregister server entries
- maintain active server list and favorites
- provide filter/search/sort view logic
- run expiry cleanup for stale servers
- measure server latency and cache timing metadata

Non-responsibilities:
- hosting game-server process
- enforcing party membership security policy
- direct WireGuard peer configuration

## Data Model

`GameServer` entries include:
- identity and display metadata (`id`, `name`, `game`)
- host metadata (`host_peer_id`, `host_peer_name`, `host_ip`)
- capacity state (`current_players`, `max_players`, `is_full`)
- optional context (`map_name`, `game_mode`, `tags`, `password_protected`)
- liveness and quality (`last_heartbeat`, `latency_ms`)

## Lifecycle

### Register/update

- host advertises server with metadata
- existing entry is updated when same `server_id` re-registers
- heartbeat timestamp refreshed on update

### Heartbeat

- hosts should refresh heartbeat periodically
- stale entries are removed by cleanup loop

### Unregister

- removes server from active list
- used when host closes server/session

### Cleanup

- periodic cleanup removes entries beyond timeout window
- prevents stale listings and dead-join attempts

## Discovery and Filtering

`list_servers(...)` supports combined filters:
- by game
- hide full / hide empty / hide password-protected
- tag inclusion
- text search across server/game/host fields

Sort behavior emphasizes practical join targets (active/capacity-aware ordering).

## Favorites

Supports:
- add/remove/check favorite server ID
- return currently active favorite entries

Operational note:
- favorites are runtime/browser-managed and exposed through API endpoints

## Latency Measurement

`measure_latency(server_id)` updates per-server latency estimate.

Probe behavior:
- ICMP probe first
- fallback probes can be used when ICMP unavailable
- measurement interval caching avoids unnecessary repeated probes

This allows responsive UI while controlling probe noise.

## API Surface

Primary server-browser routes:
- `GET /api/servers`
- `POST /api/servers`
- `GET /api/servers/{server_id}`
- `DELETE /api/servers/{server_id}`
- `POST /api/servers/{server_id}/heartbeat`
- `POST /api/servers/{server_id}/players`
- `POST /api/servers/{server_id}/join`
- `POST /api/servers/{server_id}/favorite`
- `DELETE /api/servers/{server_id}/favorite`
- `GET /api/servers/{server_id}/latency`
- `GET /api/servers/stats`
- `GET /api/games`

See [API](API.md) for endpoint list and grouping.

## Failure Modes

Common issues:
- stale listings due to missing host heartbeat
- high-latency or unreachable server endpoints
- over-filtering leading to empty result sets

Recovery guidance:
- verify heartbeat cadence from host
- use latency endpoint to validate reachability
- adjust filter predicates incrementally

## Testing Focus

Minimum regression scope:
- register/update/unregister semantics
- filter/search combinations
- favorite add/remove/check semantics
- cleanup expiry behavior
- latency measurement and interval cache behavior

## Acceptance Criteria

This doc is complete when:
- lifecycle and filtering semantics are explicit
- latency behavior and probe constraints are explicit
- API integration paths are clearly mapped
- stale-server cleanup expectations are testable
