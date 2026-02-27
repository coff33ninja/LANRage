# Control Plane Server

Centralized coordination service for LANrage parties, peers, and relay metadata.

## Scope

This document covers `servers/control_server.py` and how clients (`core/control_plane/control_client.py`) interact with it.

Related docs:
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Architecture](ARCHITECTURE.md)
- [Relay Server](/docs/servers/RELAY_SERVER.md)
- [API](API.md)

Related diagrams:
- [Control Server Request Flow](diagrams/CONTROL_SERVER_REQUEST_FLOW.md)
- [Control Server Cleanup Loop](diagrams/CONTROL_SERVER_CLEANUP_LOOP.md)

## Responsibilities

The control server provides:
- Peer registration and token issuance
- Party lifecycle endpoints (create/join/leave/get/list peers/discover peer)
- Peer heartbeat handling
- Relay registration and lookup
- Background cleanup for stale and expired state

The control server does not carry game traffic payloads.

## Runtime Model

- Framework: FastAPI
- Storage: SQLite via `aiosqlite`
- Auth model: Bearer tokens stored in `auth_tokens`
- Startup/shutdown: lifespan-managed startup init and background cleanup task

## Database Schema

Primary tables:
- `parties`
- `peers`
- `relay_servers`
- `auth_tokens`

Indexing and lifecycle:
- Peer lookup paths optimized by party/peer key usage
- Token expiration cleanup runs in background loop
- Stale peers and stale relays are pruned periodically

## Authentication and Authorization

Registration flow:
1. Client calls `POST /auth/register?peer_id=...`
2. Server creates token and expiry entry
3. Client stores token and sends `Authorization: Bearer <token>` on protected endpoints

Protected endpoint behavior:
- Missing header -> `401 Missing authorization header`
- Invalid format -> `401 Invalid authorization format`
- Invalid/expired token -> `401 Invalid or expired token`

## API Surface

Public endpoint:
- `GET /` health/status summary

Auth endpoint:
- `POST /auth/register`

Protected party endpoints:
- `POST /parties`
- `POST /parties/{party_id}/join`
- `DELETE /parties/{party_id}/peers/{peer_id}`
- `GET /parties/{party_id}`
- `GET /parties/{party_id}/peers`
- `GET /parties/{party_id}/peers/{peer_id}`
- `POST /parties/{party_id}/peers/{peer_id}/heartbeat`

Protected relay endpoints:
- `POST /relays`
- `GET /relays`
- `GET /relays/{region}`

## Request Handling Semantics

### Party create

- Host identity is validated against auth peer identity.
- Party and host peer are persisted in a single request lifecycle.

### Party join

- Party must exist.
- Joining peer identity must match authenticated peer identity.
- Peer row is inserted/upserted and `last_seen` refreshed.

### Party leave

- Caller can remove only its own peer identity unless authorized otherwise by server rules.
- Party removal occurs when host leaves or party becomes empty.

### Heartbeat

- Refreshes peer `last_seen`.
- Missing party/peer yields not-found behavior.

### Relay registration

- Relay metadata upserted by relay ID.
- `last_seen` refreshed on registration/heartbeat-like updates.

## Cleanup and Consistency Loop

Background cleanup removes:
- stale peers (`last_seen` threshold)
- empty parties
- expired auth tokens
- stale relays

Consistency goals:
- prevent unbounded growth of stale state
- keep list/discovery endpoints representative of active topology

See [Control Server Cleanup Loop](diagrams/CONTROL_SERVER_CLEANUP_LOOP.md).

## Operational Deployment Guidance

Single-instance baseline:
- SQLite-backed server is sufficient for many small/medium deployments.
- Keep DB path on reliable local disk.

When to evolve storage:
- Multi-instance write concurrency
- need for stronger cross-instance consistency
- central HA requirements

In those scenarios, migrate persistence backend while preserving endpoint contract.

## Failure Modes

### Auth failures

Symptoms:
- frequent 401 responses

Checks:
- token issuance path
- client bearer header injection
- token expiry and clock skew assumptions

### State drift/stale entries

Symptoms:
- peers shown but unreachable

Checks:
- heartbeat cadence
- cleanup loop health
- app-side reconnect/leave behavior

### DB lock/contention issues

Symptoms:
- delayed or failed writes under load

Checks:
- request concurrency model
- SQLite file placement and I/O constraints

## Observability Recommendations

- Track counts of active parties/peers/relays from health endpoint.
- Monitor 4xx/5xx rates on protected endpoints.
- Track cleanup loop outcomes (how many stale items removed per run).
- Correlate heartbeat failures with peer churn.

## Testing Focus

Minimum server regression coverage:
- auth register and token enforcement
- party lifecycle endpoint behavior
- heartbeat path behavior
- relay registration/list/region filters
- cleanup behavior for stale peers/tokens/relays

## Acceptance Criteria

This document is complete when:
- Protected endpoint/auth behavior is explicitly documented.
- Cleanup loop semantics and stale-state policy are explicit.
- Persistence model and migration boundary are clear.
- Client/server contract is aligned with current implementation.
