# Party Management

Party lifecycle orchestration across control, NAT, and connection subsystems.

## Scope

This document covers `core/control_plane/party.py` behavior.

Related docs:
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Network Layer](/docs/core/networking/NETWORK.md)

Related diagrams:
- [Party Host/Join Lifecycle](diagrams/PARTY_HOST_JOIN_LIFECYCLE.md)
- [Party Lifecycle Sequence](diagrams/SEQUENCE_PARTY_LIFECYCLE.md)

## Responsibilities

`PartyManager` is responsible for:
- initializing and wiring NAT/control/connection dependencies
- create/join/leave party flows
- converting control-plane party/peer metadata into local runtime models
- triggering peer connection attempts on join
- exposing party status summaries for API/UI

It is not responsible for:
- low-level relay selection internals
- WireGuard command execution
- control-server endpoint implementation

## Core Models

### Peer

Runtime party peer view includes:
- identity (id/name/public_key)
- virtual IP
- endpoint (if known)
- connection type/state
- optional latency and timestamps

### Party

Runtime party view includes:
- party identity and host identity
- peer map
- creation metadata

Compatibility helper behavior:
- supports NAT-type-based peer compatibility filtering for direct-path candidates

## Initialization Semantics

`PartyManager` supports staged setup:
- `initialize_nat()` sets NAT and coordinator
- `initialize_control()` sets control plane and connection manager

Join robustness behavior:
- join flow lazily initializes required NAT/control dependencies if missing
- avoids hard failure when initialization order is incomplete upstream

## Host Flow

Create flow:
1. ensure prerequisites are initialized
2. build host `PeerInfo`
3. register party in control plane
4. construct local `Party` model
5. set host connection state and set `current_party`

## Joiner Flow

Join flow:
1. ensure prerequisites (lazy init path if needed)
2. build joiner `PeerInfo` including NAT/public/local endpoint metadata
3. join party through control plane
4. transform returned party state into local runtime models
5. asynchronously connect to existing peers
6. set current party and update peer connection states

## Leave Flow

Leave behavior:
1. disconnect active peer connections
2. notify control plane of leave
3. clear local current-party state

Host leave implications:
- party may disband according to control-plane lifecycle rules

## Status and Synchronization

`get_party_status()` behavior:
- returns `no_party` or in-party payload
- includes peer count and peer summaries
- includes NAT/public endpoint summary when available
- refreshes peer latency observations where applicable

## Failure and Recovery Semantics

Common failure classes:
- invalid/missing party ID
- control-plane not initialized/unavailable
- peer connection setup failure for one or more peers

Behavior:
- join/create surface explicit errors to caller
- per-peer connect failures do not necessarily abort whole party state construction
- connection manager handles ongoing remediation for failed/degraded peers

## Persistence and Restart Caveats

Party runtime state is coordinated with control-plane persistence.

Operational caveat:
- local runtime model reconstruction on join depends on control-plane party/peer metadata fidelity.

## Testing Focus

Minimum regression scope:
- create/join/leave happy-paths
- lazy initialization branch on join
- host and non-host leave semantics
- peer compatibility filtering behavior
- status payload consistency with mixed peer states

## Acceptance Criteria

This doc is complete when:
- host/join/leave flows are explicit and code-aligned
- lazy initialization behavior is clearly documented
- sync boundaries between party manager and control/connection layers are explicit
- failure handling expectations are actionable
