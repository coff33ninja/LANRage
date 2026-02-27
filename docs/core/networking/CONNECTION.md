# Connection Management

Peer connection orchestration between control-plane metadata and WireGuard data-plane configuration.

## Scope

This document covers `core/networking/connection.py` behavior and its integration with NAT and network layers.

Related docs:
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Network Layer](/docs/core/networking/NETWORK.md)
- [Party](/docs/core/control_plane/PARTY.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)

Related diagrams:
- [Connection State Machine](diagrams/CONNECTION_STATE_MACHINE.md)
- [Connection Fallback Sequence](diagrams/SEQUENCE_CONNECTION_FALLBACK.md)

## Responsibilities

`ConnectionManager` is responsible for:
- peer discovery lookup before connect
- strategy coordination via NAT/relay logic
- WireGuard peer add/remove operations
- per-peer lifecycle state tracking
- health monitoring, reconnect, and relay-switch remediation

It is not responsible for:
- NAT detection internals
- control-plane membership persistence
- interface creation/teardown

## Connection Lifecycle

High-level connect flow:
1. discover peer metadata from control plane
2. request strategy/endpoint from coordinator
3. configure WireGuard peer for endpoint/allowed IPs
4. record connection state and start monitor task

High-level disconnect flow:
1. remove WireGuard peer
2. release virtual IP allocation
3. remove local connection record

## State Model

Common runtime states:
- `connecting`
- `connected`
- `degraded`
- `failed`
- `disconnected`

State transitions are driven by probe outcomes and remediation results.

See [Connection State Machine](diagrams/CONNECTION_STATE_MACHINE.md).

## Health Monitoring and Recovery

Monitor behavior:
- periodic latency checks
- status update based on threshold/availability
- reconnect attempts on failures
- relay switch attempts on sustained degradation for relay paths

Recovery behavior:
- on temporary failure, attempt reconnect within bounded retries
- on persistent failure, mark failed and allow upper-layer handling
- on relay path degradation, attempt better relay and revert if worse

## Virtual IP and Peer Identity Handling

Connection records include:
- peer identity
- assigned virtual IP
- endpoint and strategy
- timestamps and last measured latency
- current lifecycle status

IP allocation is deterministic through IPAM integration and must remain stable for active connection records.

## Error and Failure Semantics

Typical failure classes:
- peer not found in control plane
- strategy resolution failure
- WireGuard add/remove command failure
- monitor probe failures and endpoint instability

Operational behavior:
- errors are surfaced with explicit connection-context logging
- monitor loop isolates per-peer failures to avoid global manager crash
- cleanup paths avoid stale records for failed connections

## Relay-Switch Semantics

Relay-switch path is conditional:
- only relevant when active strategy uses relay
- evaluate candidate relay endpoint quality
- switch only when measured improvement justifies update
- revert if candidate path is worse or unstable

## Observability and Diagnostics

For each connection, track:
- current state
- strategy (`direct` or `relay`)
- endpoint
- last latency
- reconnect/switch actions taken

Diagnostics priority:
1. control-plane peer discoverability
2. endpoint strategy returned by coordinator
3. WireGuard peer configuration success
4. monitor probe outcomes over time

## Testing Focus

Minimum regression scope:
- connect/disconnect happy-path behavior
- state transitions under failed probes
- bounded reconnect attempts
- relay-switch branch behavior
- stale connection cleanup behavior

## Acceptance Criteria

This doc is complete when:
- lifecycle stages and states are explicit
- remediation behavior is testable from docs
- control/NAT/network boundaries are clear
- state transitions align with current manager behavior

