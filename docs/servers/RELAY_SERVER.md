# Relay Server

Stateless UDP forwarding service used when direct peer paths are unavailable or degraded.

## Scope

This document covers `servers/relay_server.py` behavior and operational deployment guidance.

Related docs:
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [Control Plane Server](/docs/servers/CONTROL_PLANE_SERVER.md)
- [Architecture](ARCHITECTURE.md)

Related diagrams:
- [Data Plane Paths](diagrams/DATA_PLANE_PATHS.md)
- [Failure Domains and Fallbacks](diagrams/FAILURE_DOMAINS.md)

## Responsibilities

Relay server responsibilities:
- receive encrypted WireGuard UDP packets
- forward packets between active relay clients
- maintain lightweight client activity map
- cleanup stale client entries
- expose operational stats through logs

Relay server non-responsibilities:
- packet decryption
- party membership authority
- NAT strategy selection

## Runtime Behavior

Core flow:
1. packet arrives from source address
2. source is tracked/refreshed in client map
3. packet is forwarded to other active relay clients
4. counters/stats updated

Background loops:
- stale-client cleanup loop
- periodic stats loop

## Client Tracking Model

Tracked per client:
- identity hint (public key when extractable from handshake)
- source UDP address
- last activity timestamp
- bytes relayed counters

Cleanup policy:
- remove clients inactive beyond timeout window
- keeps active set compact and avoids stale forwarding paths

## Integration with Control Plane

Relay service can be registered/discovered via control-plane server endpoints.

Client-side connection coordinator behavior:
- discovers relay candidates via control-plane API
- chooses candidate endpoint based on selection logic
- updates peer endpoint in WireGuard config

Operationally, relay and control services can be deployed independently.

## Deployment Topologies

### Single relay

- simplest deployment
- suitable for small/private groups
- single fault domain

### Multi-region relays

- deploy relays near major player clusters
- reduce path RTT for fallback traffic
- improve resilience when one region degrades

### Hosted control + relay mesh

- centralized control-plane registry
- multiple relay nodes with region metadata
- coordinator selects best available relay at connection time

## Capacity and Sizing Guidance

Practical considerations:
- primary bottleneck is network I/O, then CPU under high packet rates
- memory usage scales with number of active clients
- keep UDP buffers and host networking tuned for sustained traffic

Sizing strategy:
- start with one modest node per region
- scale horizontally when sustained utilization or latency increases
- validate with load tests that resemble target packet patterns

## Security Posture

- relay forwards encrypted payloads without decrypting content
- relay visibility is metadata-level (address/timing/volume), not plaintext game data
- abuse mitigation should be handled with network controls and policy (firewall/rate controls)

## Failure Modes

### Relay unavailable

Effect:
- relay path connect attempts fail

Recovery:
- connection logic falls back to alternate relay candidates/defaults where available

### Relay overloaded or distant

Effect:
- increased relay path latency/jitter

Recovery:
- endpoint re-selection and relay-switch logic from connection layer
- deploy/add relays closer to users

### Stale client map growth

Effect:
- inefficient forwarding attempts

Recovery:
- verify cleanup loop cadence and timeout configuration

## Operations and Monitoring

Track at minimum:
- active relay client count
- packet and byte forwarding rates
- stale-client cleanup counts
- host CPU/network saturation indicators

Operational checks:
- UDP listen port reachable externally
- relay public endpoint matches advertised/discovered metadata
- cleanup and stats loops running

## Testing Focus

Minimum regression scope:
- datagram receive/forward behavior
- stale client cleanup semantics
- stats counter correctness
- resilience under malformed or unexpected packets

## Acceptance Criteria

This doc is complete when:
- relay responsibilities and boundaries are explicit
- topology and scaling guidance is actionable
- failover expectations with control/connection layers are explicit
- operational metrics/checks are defined
