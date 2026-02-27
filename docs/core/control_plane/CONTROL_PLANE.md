# Control Plane

Control plane architecture and behavior for peer discovery, party state, signaling, and relay metadata.

## Scope

This doc covers:
- `core/control_plane/control.py` local and remote control-plane behavior
- `core/control_plane/control_client.py` HTTP control-plane client behavior
- `servers/control_server.py` centralized control-plane server behavior

Related docs:
- [Architecture](ARCHITECTURE.md)
- [Control Plane Server](/docs/servers/CONTROL_PLANE_SERVER.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Relay Server](/docs/servers/RELAY_SERVER.md)

Related diagrams:
- [Control Plane State Machine](diagrams/CONTROL_PLANE_STATE_MACHINE.md)
- [Signal Queue/Poll Sequence](diagrams/SIGNAL_QUEUE_POLL_SEQUENCE.md)
- [Party Lifecycle Sequence](diagrams/SEQUENCE_PARTY_LIFECYCLE.md)

## Responsibilities

The control plane is responsible for coordination, not packet transport.

Core responsibilities:
- Party registration and membership updates
- Peer metadata lookup for connection setup
- Heartbeat updates and stale-peer cleanup
- Pending signaling message queue and poll delivery
- Relay metadata registration and lookup (centralized mode)

Non-responsibilities:
- WireGuard interface manipulation (data plane)
- Packet forwarding (relay/data plane)

## Implementations

### ControlPlane (`core/control_plane/control.py`)

Base implementation with in-memory state and disk-backed persistence.

Key behavior:
- Stores parties and peers
- Persists state via write-behind batching
- Performs periodic cleanup of stale peers
- Supports signaling queue and polling APIs:
  - `signal_connection(...)`
  - `poll_signals(...)`

### LocalControlPlane (`core/control_plane/control.py`)

Extends base behavior with local discovery file support.

Use case:
- Simple local setups and fallback mode when remote control is unavailable

### RemoteControlPlane (`core/control_plane/control.py`)

Extends base behavior with remote server integration over WebSocket.

Current behavior:
- Connect/reconnect loop with bounded retries
- Token-aware auth handshake payload (`type: auth`, optional token)
- Message handler for updates/signals/errors
- Falls back to base/local behavior when remote connectivity fails

### RemoteControlPlaneClient (`core/control_plane/control_client.py`)

HTTP client for centralized control-plane server.

Current behavior:
- Registers peer and obtains auth token
- Sends Bearer token on protected endpoints
- Creates/joins/leaves parties
- Sends periodic heartbeat
- Lists relays and relays by region

## Data Model

### PeerInfo

Control-plane view of a peer identity and connection metadata.

Fields include:
- Peer identity (`peer_id`, `name`, `public_key`)
- NAT/public/local endpoint info (`nat_type`, public/local IP/port)
- Activity timestamp (`last_seen`)

### PartyInfo

Control-plane party state.

Fields include:
- Party identity (`party_id`, `name`)
- Host ownership (`host_id`)
- Membership map (`peers`)
- Timestamps (`created_at`)

## Lifecycle and State Semantics

### Party lifecycle

- Register party -> party created with host peer
- Join party -> peer added to membership map
- Leave party -> peer removed; party removed if host leaves or party is empty

### Heartbeat and cleanup

- Peers must refresh `last_seen` via heartbeat
- Cleanup loop removes stale peers and then empty parties
- Cleanup persists resulting state

### Persistence

Base control plane persists party/peer state to control-state file under config dir.

Persistence goals:
- Reduce write amplification (write-behind batching)
- Recover state after restart
- Avoid hard failure on corrupted persisted state (fresh start fallback)

## Signaling Queue/Poll Behavior

Signaling flow is explicit and queue-based:
- Sender enqueues envelope with `signal_connection(...)`
- Envelope is stored under target peer queue
- Target retrieves and clears queue via `poll_signals(...)`

Semantics:
- Queue is per target peer
- `poll_signals` returns all queued messages for that peer and clears them
- Signaling queue is control metadata only, not media/data transport

See [Signal Queue/Poll Sequence](diagrams/SIGNAL_QUEUE_POLL_SEQUENCE.md).

## Centralized Control Server Contract

`servers/control_server.py` exposes protected APIs (Bearer token required after peer registration).

Key endpoints:
- `POST /auth/register`
- `POST /parties`
- `POST /parties/{party_id}/join`
- `DELETE /parties/{party_id}/peers/{peer_id}`
- `GET /parties/{party_id}`
- `GET /parties/{party_id}/peers`
- `GET /parties/{party_id}/peers/{peer_id}`
- `POST /parties/{party_id}/peers/{peer_id}/heartbeat`
- `POST /relays`
- `GET /relays`
- `GET /relays/{region}`

Auth notes:
- Token issuance at register step
- Token verification on protected routes
- Expired token cleanup in server maintenance loop

## Failure Modes and Recovery

### Remote control unavailable

Behavior:
- Remote client retries connection with backoff bounds
- Local/base path remains available for continuity

### Heartbeat failures

Behavior:
- Logged and retried by heartbeat loop
- Does not immediately crash control-plane runtime

### Stale state

Behavior:
- Cleanup loop prunes stale peers and empty parties
- Persistence writes updated state after cleanup

### Signaling delivery gaps

Behavior:
- Poll-based delivery means peers receive pending envelopes on next poll
- Queue clear-on-poll semantics avoids duplicate replay from stale queue entries

## Operational Guidance

- Keep control-plane and relay responsibilities separated in deployment and troubleshooting.
- Monitor stale-peer churn and heartbeat failures for instability indicators.
- Treat control-plane auth token handling as mandatory in remote deployments.
- Validate party/peer invariants in tests whenever lifecycle logic changes.

## Testing Focus

Minimum regression scope for control-plane changes:
- Party register/join/leave invariants
- Stale cleanup behavior and timing assumptions
- Signaling queue/poll semantics
- Remote client auth bootstrap and protected endpoint calls
- Heartbeat loop behavior under transient server errors

## Acceptance Criteria

This doc is complete when:
- Lifecycle states and transitions are explicit.
- Signaling queue/poll semantics are documented and testable.
- Remote auth behavior reflects current implementation.
- Control-plane/server contract is clearly mapped to protected endpoints.
