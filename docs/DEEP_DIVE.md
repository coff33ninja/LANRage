# LANrage Deep Dive

Cross-cutting technical reference for architecture, runtime behavior, and operations.

## 1. End-to-End Runtime Narrative

LANrage runtime is intentionally ordered:

1. configuration/settings load
2. network layer readiness (WireGuard prerequisites, keys, interface lifecycle)
3. NAT traversal setup and endpoint characterization
4. control-plane initialization (local/remote mode)
5. party/connection orchestration readiness
6. API + UI exposure

Why it matters:
- party/join/connect paths rely on NAT and control context being ready
- exposing API too early creates partial-service behavior and ambiguous failure modes

See:
- [Architecture](ARCHITECTURE.md)
- [Startup Sequence](diagrams/STARTUP_SEQUENCE.md)

## 2. Planes and Boundaries

### Control plane

- identity and membership coordination
- signaling queue/poll delivery
- heartbeat and stale cleanup
- relay metadata registry/discovery

### Data plane

- encrypted WireGuard peer transport
- endpoint application (direct/relay) from coordinator decisions

### Application plane

- user workflows (create/join/leave)
- status/metrics/API endpoints
- operational diagnostics and management surface

Boundary rule:
- control metadata decisions must remain separate from packet transport responsibilities.

## 3. Control-Plane Behavior in Practice

Modes:
- local mode for simple/disconnected scenarios
- centralized server mode with token-protected HTTP APIs

Important semantics:
- queue-based signaling delivery (`signal_connection` + `poll_signals`)
- token issuance and bearer enforcement for protected operations
- periodic cleanup for stale peers/parties/tokens/relays

See:
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Control Plane Server](/docs/servers/CONTROL_PLANE_SERVER.md)
- [Control Plane State Machine](diagrams/CONTROL_PLANE_STATE_MACHINE.md)
- [Control Server Request Flow](diagrams/CONTROL_SERVER_REQUEST_FLOW.md)

## 4. Connection Strategy and Degradation Handling

Per peer, connection manager orchestrates:
1. peer metadata discovery
2. NAT strategy decision (direct vs relay)
3. endpoint application in WireGuard
4. health monitoring and lifecycle transitions
5. remediation (reconnect, relay switch) when degraded

Important distinction:
- NAT traversal relay selection follows NAT-specific discovery/selection logic.
- server-browser latency probing has its own probe fallback path and caching policy.

See:
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [Connection State Machine](diagrams/CONNECTION_STATE_MACHINE.md)
- [NAT Strategy Decision Tree](diagrams/NAT_STRATEGY_DECISION_TREE.md)

## 5. Party Orchestration Model

Party manager coordinates control + NAT + connection layers:
- host path: register and publish host identity
- join path: resolve party state and connect existing peers
- leave path: disconnect and clear local runtime state

Robustness behavior:
- join flow can lazily initialize missing prerequisites to reduce hard-failure cases

See:
- [Party Management](/docs/core/control_plane/PARTY.md)
- [Party Host/Join Lifecycle](diagrams/PARTY_HOST_JOIN_LIFECYCLE.md)

## 6. Relay Topology and Operational Scaling

Relay layer is stateless forwarding infrastructure:
- no payload decryption
- low state per active client
- periodic stale-client cleanup

Scaling patterns:
- single relay for small/private groups
- multi-region relay set for distributed players
- hosted control + regional relays for best balance of operability and latency

See:
- [Relay Server](/docs/servers/RELAY_SERVER.md)
- [Failure Domains and Fallbacks](diagrams/FAILURE_DOMAINS.md)

## 7. Observability and Operational Control

Observability surface:
- API/UI metrics summaries
- Prometheus-compatible endpoint support
- connection/quality and runtime status diagnostics

Operational use:
- detect degraded paths early
- validate behavior after release and infra changes
- correlate control-plane churn with relay/latency issues

See:
- [Metrics](/docs/core/observability/METRICS.md)
- [API](API.md)
- [Performance Profiling](/docs/core/observability/PERFORMANCE_PROFILING.md)

## 8. Security Posture Snapshot

Current baseline:
- WireGuard data-plane encryption
- control-server bearer-token auth model
- relay metadata visibility without payload decryption requirement

Operational security focus:
- protect token issuance/validation paths
- isolate relay/control blast radius via deployment boundaries
- treat metadata exposure and logs with least-privilege practices

See:
- [Security](../SECURITY.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Network Layer](/docs/core/networking/NETWORK.md)

## 9. Troubleshooting Mental Model

When investigating failures, follow this order:
1. control-plane reachability and auth
2. peer metadata validity and NAT classification
3. endpoint strategy selected (direct/relay)
4. WireGuard peer config success
5. monitor/remediation loop behavior over time

This ordering avoids chasing data-plane symptoms before control-plane root causes are eliminated.

## 10. Documentation Governance

Canonical source policy:
- `docs/` is the source of truth
- external research notes were used during expansion, then removed from repo

When extending system behavior:
1. update subsystem doc first
2. update this deep dive for cross-cutting impact
3. update relevant diagrams and docs index links
