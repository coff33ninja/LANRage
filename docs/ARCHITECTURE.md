# LANrage Architecture

This document defines the system architecture, runtime boundaries, and deployment patterns for LANrage.

## Scope and Audience

- Contributors: understand subsystem responsibilities and interfaces.
- Operators: understand deployment topology, failure domains, and scaling behavior.
- Advanced users: understand why connection strategy and fallback behavior work as they do.

Related diagrams:
- [System Context](diagrams/SYSTEM_CONTEXT.md)
- [System Flow Overview](diagrams/SYSTEM_FLOW.md)
- [Runtime Control Loops](diagrams/RUNTIME_CONTROL_LOOPS.md)
- [Failure Domains and Fallbacks](diagrams/FAILURE_DOMAINS.md)
- [Startup Sequence](diagrams/STARTUP_SEQUENCE.md)

## Architectural Boundaries

LANrage is split into three runtime planes.

1. Control plane
- Party registration and membership state
- Peer metadata propagation
- Signaling delivery and heartbeats
- Relay metadata discovery

2. Data plane
- WireGuard tunnel establishment
- Peer endpoint selection (direct or relayed)
- Virtual IP assignment and peer route updates

3. Application plane
- Local API and web UI
- Metrics collection and reporting
- Server browser, Discord integration, and user workflows

## Runtime Components

Primary modules and responsibilities:

- `core/control_plane/party.py`: party lifecycle orchestration and peer coordination
- `core/control_plane/control.py`: local/remote control-plane behavior and signaling paths
- `core/networking/connection.py`: connection lifecycle, monitoring, and recovery
- `core/networking/nat.py`: NAT detection, hole punching, relay fallback strategy
- `core/networking/network.py`: WireGuard interface and peer management
- `core/networking/ipam.py`: virtual IP allocation and consistency
- `core/observability/metrics.py`: system and peer quality metrics
- `core/gameplay/server_browser.py`: game server registration/discovery and latency probes
- `api/server.py`: FastAPI endpoints and UI integration
- `servers/control_server.py`: centralized control-plane server
- `servers/relay_server.py`: stateless relay forwarding service

## Runtime Lifecycle and Initialization Order

LANrage uses strict startup ordering to avoid partially initialized states:

1. Initialize settings store and load effective configuration.
2. Initialize network manager and validate WireGuard prerequisites.
3. Initialize NAT traversal and detect local NAT characteristics.
4. Initialize control plane (local, and remote integration when configured).
5. Initialize party manager and connection orchestration.
6. Start metrics and integration services.
7. Start API server and UI endpoints.

This ordering ensures party join/connect paths have control and NAT state ready before user-triggered operations.

## Connection Strategy Model

For each peer path, LANrage selects the best available strategy.

1. Direct P2P (preferred)
- Detect NAT profile
- Attempt hole punching
- Establish WireGuard peer directly

2. Relay fallback
- Discover relay candidates
- Score/select relay endpoint
- Establish peer via relay endpoint

3. Degradation handling
- Monitor latency and quality trend
- Re-evaluate endpoint strategy on sustained degradation
- Recover via reconnect or relay switch

For detailed behavior, see:
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [Relay Server](/docs/servers/RELAY_SERVER.md)

## Deployment Topologies

### Topology A: Small private group

- Local control behavior with optional remote integration disabled
- One relay configured as fallback
- Suitable for small trusted groups

### Topology B: Hosted control + single region relay

- Central control server for peer/session coordination
- One relay near primary player region
- Suitable for stable medium-size communities

### Topology C: Hosted control + multi-region relays

- Central control server
- Multiple relays by region
- Relay selection weighted by latency and load
- Suitable for geographically distributed groups

## Failure Domains and Recovery

Key failure domains:

- Local host failures (client process/network/WireGuard)
- Control-plane server unavailability
- Relay endpoint unavailability or overload
- Regional network degradation

Recovery principles:

- Keep data plane independent from control-plane round trips after tunnel setup.
- Degrade to relay path when direct path cannot be maintained.
- Prefer local continuity and reconnection over full-session teardown.

See [Failure Domains and Fallbacks](diagrams/FAILURE_DOMAINS.md).

## Security Model Summary

- Data plane encryption uses WireGuard primitives.
- Control-plane APIs use token-based protection for protected paths.
- Relay nodes forward encrypted packets and do not require payload decryption.
- Peer identity is tied to key material and control-plane metadata.

Security details:
- [Network](/docs/core/networking/NETWORK.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Security](../SECURITY.md)

## Performance and Capacity Baseline

Architecture-level targets:

- Prioritize direct low-latency peer paths.
- Keep relay overhead bounded and observable.
- Minimize client runtime overhead under idle and active states.
- Keep startup and reconnect paths deterministic and debuggable.

Operational observability:
- [Metrics](/docs/core/observability/METRICS.md)
- [Performance Profiling](/docs/core/observability/PERFORMANCE_PROFILING.md)

## Compatibility and Evolution

Current baseline:
- Windows and Linux are active targets.
- IPv4 virtual network is primary.

Planned evolution:
- Dual-stack/IPv6 support
- Extended remote control-plane policy options
- Additional deployment automation and runtime tuning

Roadmap details:
- [Roadmap](project/ROADMAP.md)

## Acceptance Criteria for This Document

This architecture document is complete when:

- Subsystem boundaries are explicit and non-overlapping.
- Startup order is documented and references runtime behavior.
- Topology and failure-domain guidance are operationally actionable.
- Cross-links to subsystem docs and diagrams are present and coherent.

