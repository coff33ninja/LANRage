# NAT Traversal Strategies

<cite>
**Referenced Files in This Document**
- [core/nat.py](file://core/nat.py)
- [core/connection.py](file://core/connection.py)
- [core/network.py](file://core/network.py)
- [core/control.py](file://core/control.py)
- [servers/relay_server.py](file://servers/relay_server.py)
- [docs/NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md)
- [tests/test_nat.py](file://tests/test_nat.py)
- [core/config.py](file://core/config.py)
- [core/settings.py](file://core/settings.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
This document explains LANrage’s multi-layered NAT traversal strategy for establishing direct P2P connections across diverse network topologies. It covers STUN-based NAT type detection, UDP hole punching, fallback to relay-based TCP tunneling, connection prioritization with latency-based decisions, timeout handling, graceful degradation, NAT type classification, and connection health monitoring with automatic failover.

## Project Structure
LANrage organizes NAT traversal logic primarily in core modules:
- NAT detection and hole punching: core/nat.py
- Connection orchestration: core/connection.py
- WireGuard network stack and keepalive: core/network.py
- Control plane for peer discovery and relay discovery: core/control.py
- Relay server implementation: servers/relay_server.py
- Documentation and tests: docs/NAT_TRAVERSAL.md, tests/test_nat.py
- Configuration and settings: core/config.py, core/settings.py

```mermaid
graph TB
subgraph "Client"
A["core/nat.py<br/>NATTraversal, ConnectionCoordinator"]
B["core/connection.py<br/>ConnectionManager"]
C["core/network.py<br/>NetworkManager"]
D["core/control.py<br/>ControlPlane"]
E["core/config.py<br/>Config"]
F["core/settings.py<br/>SettingsDatabase"]
end
subgraph "Relay"
R["servers/relay_server.py<br/>RelayServer"]
end
A --> B
B --> C
B --> D
B --> A
C --> R
E --> A
E --> C
F --> E
```

**Diagram sources**
- [core/nat.py](file://core/nat.py#L41-L328)
- [core/connection.py](file://core/connection.py#L18-L125)
- [core/network.py](file://core/network.py#L25-L160)
- [core/control.py](file://core/control.py#L187-L346)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L138)
- [core/config.py](file://core/config.py#L17-L114)
- [core/settings.py](file://core/settings.py#L20-L142)

**Section sources**
- [core/nat.py](file://core/nat.py#L1-L100)
- [core/connection.py](file://core/connection.py#L1-L50)
- [core/network.py](file://core/network.py#L1-L50)
- [core/control.py](file://core/control.py#L1-L50)
- [servers/relay_server.py](file://servers/relay_server.py#L1-L50)
- [core/config.py](file://core/config.py#L1-L50)
- [core/settings.py](file://core/settings.py#L1-L50)

## Core Components
- NATTraversal: Implements STUN-based NAT type detection, simplified NAT classification, and UDP hole punching.
- ConnectionCoordinator: Coordinates strategy selection (direct vs relay), attempts hole punching, and discovers/selects relay endpoints.
- ConnectionManager: Orchestrates peer connection lifecycle, WireGuard peer configuration, and connection health monitoring.
- NetworkManager: Manages WireGuard interface creation, peer addition/removal, and latency measurement.
- ControlPlane: Provides peer discovery and relay discovery hooks for strategy selection.
- RelayServer: Stateless UDP packet forwarder for relay fallback.

**Section sources**
- [core/nat.py](file://core/nat.py#L41-L328)
- [core/connection.py](file://core/connection.py#L18-L125)
- [core/network.py](file://core/network.py#L25-L160)
- [core/control.py](file://core/control.py#L187-L346)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L138)

## Architecture Overview
The NAT traversal pipeline integrates discovery, detection, strategy selection, and connection establishment:

```mermaid
sequenceDiagram
participant CM as "ConnectionManager"
participant CP as "ControlPlane"
participant NT as "NATTraversal"
participant CC as "ConnectionCoordinator"
participant NM as "NetworkManager"
participant RS as "RelayServer"
CM->>CP : discover_peer(party_id, peer_id)
CP-->>CM : PeerInfo(nat_type, public_ip, public_port, local_ip, local_port)
CM->>NT : detect_nat() (optional pre-check)
CM->>CC : coordinate_connection(peer_public_key, peer_nat_info)
alt can_direct_connect
CC->>NT : attempt_hole_punch(peer_public_ip, peer_public_port)
alt hole_punch success
CC-->>CM : strategy=direct, endpoint=peer_public_ip : peer_public_port
else hole_punch fail
CC->>CC : _get_relay_endpoint()
CC-->>CM : strategy=relay, endpoint=relay_ip : relay_port
end
else cannot direct connect
CC->>CC : _get_relay_endpoint()
CC-->>CM : strategy=relay, endpoint=relay_ip : relay_port
end
CM->>NM : add_peer(peer_public_key, endpoint, allowed_ips)
NM-->>CM : success
CM->>CM : start monitoring tasks
CM->>NM : measure_latency(virtual_ip)
NM-->>CM : latency_ms
alt latency ok
CM->>CM : status=connected
else latency degraded/high
CM->>CM : status=degraded
opt relay connection
CM->>CC : _switch_relay(peer_id, connection)
CC->>NM : remove_peer + add_peer(new_relay_endpoint)
NM-->>CC : latency result
CC-->>CM : update endpoint or revert
end
end
```

**Diagram sources**
- [core/connection.py](file://core/connection.py#L38-L125)
- [core/nat.py](file://core/nat.py#L330-L398)
- [core/network.py](file://core/network.py#L392-L443)

## Detailed Component Analysis

### NAT Detection and Classification
- STUN-based detection: Sends Binding Requests to multiple public STUN servers, parses XOR-MAPPED-ADDRESS, and determines NAT type.
- Simplified classification: Treats open (no NAT), full cone (easy), and port-restricted cone (requires coordinated hole punching) as compatible for direct P2P; symmetric NAT requires relay.
- Public STUN servers: Multiple Google STUN endpoints are used for robustness.

```mermaid
flowchart TD
Start(["detect_nat()"]) --> TryServers["Iterate STUN servers"]
TryServers --> Request["_stun_request(server)"]
Request --> Parse["Parse STUN response<br/>MAPPED/XOR-MAPPED-ADDRESS"]
Parse --> Classify["_determine_nat_type(local_ip, local_port, public_ip, public_port)"]
Classify --> Open{"public_ip == local_ip?"}
Open --> |Yes| SetOpen["NATType.OPEN"]
Open --> |No| PortsMatch{"public_port == local_port?"}
PortsMatch --> |Yes| SetFullCone["NATType.FULL_CONE"]
PortsMatch --> |No| SetPortRestricted["NATType.PORT_RESTRICTED_CONE"]
SetOpen --> Done(["Return STUNResponse"])
SetFullCone --> Done
SetPortRestricted --> Done
```

**Diagram sources**
- [core/nat.py](file://core/nat.py#L64-L106)
- [core/nat.py](file://core/nat.py#L107-L179)
- [core/nat.py](file://core/nat.py#L181-L226)
- [core/nat.py](file://core/nat.py#L228-L242)

**Section sources**
- [core/nat.py](file://core/nat.py#L19-L28)
- [core/nat.py](file://core/nat.py#L64-L106)
- [core/nat.py](file://core/nat.py#L107-L179)
- [core/nat.py](file://core/nat.py#L181-L242)
- [docs/NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L16-L27)

### UDP Hole Punching
- Simultaneous open technique: Both peers send UDP packets to each other’s public endpoints concurrently to create return-path holes in their respective NATs.
- Timing: Five packets sent over 500 ms with 100 ms intervals; 2-second ACK wait window.
- Acknowledgement: Expects a specific ACK payload to confirm successful hole punching.

```mermaid
sequenceDiagram
participant A as "Peer A"
participant B as "Peer B"
participant NATA as "NAT A"
participant NATB as "NAT B"
A->>NATA : sendto(public_B, port)
B->>NATB : sendto(public_A, port)
Note over A,B : Peers send simultaneously
NATA-->>B : allow inbound from public_A
NATB-->>A : allow inbound from public_B
A->>B : receive ACK (if successful)
B->>A : receive ACK (if successful)
A-->>A : success if ACK received
B-->>B : success if ACK received
```

**Diagram sources**
- [core/nat.py](file://core/nat.py#L244-L294)
- [docs/NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L380-L416)

**Section sources**
- [core/nat.py](file://core/nat.py#L244-L294)
- [docs/NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L380-L416)

### Strategy Selection and Fallback
- Direct P2P feasibility: Determined by compatibility matrix (open/open, full cone/full cone, restricted/restricted, port-restricted/port-restricted); symmetric NAT requires relay.
- Relay discovery: Attempts control plane discovery, falls back to configured relay, then default relay.
- Latency-based relay selection: Measures ping latency to each discovered relay and selects the best.

```mermaid
flowchart TD
Start(["coordinate_connection(peer_nat_info)"]) --> Strategy["get_connection_strategy(peer_nat_type)"]
Strategy --> CanDirect{"can_direct_connect(peer_nat_type)?"}
CanDirect --> |Yes| Punch["attempt_hole_punch(peer_public_ip, peer_public_port)"]
Punch --> Success{"hole_punch success?"}
Success --> |Yes| Direct["return strategy=direct, endpoint=peer_public_ip:peer_public_port"]
Success --> |No| Relay["get_relay_endpoint()"]
CanDirect --> |No| Relay
Relay --> Endpoint["endpoint = relay_ip:relay_port"]
Endpoint --> Result["return strategy=relay, endpoint"]
```

**Diagram sources**
- [core/nat.py](file://core/nat.py#L330-L369)
- [core/nat.py](file://core/nat.py#L371-L377)
- [core/nat.py](file://core/nat.py#L379-L455)
- [core/nat.py](file://core/nat.py#L457-L525)

**Section sources**
- [core/nat.py](file://core/nat.py#L295-L327)
- [core/nat.py](file://core/nat.py#L330-L369)
- [core/nat.py](file://core/nat.py#L379-L455)
- [core/nat.py](file://core/nat.py#L457-L525)

### Connection Orchestration and Health Monitoring
- ConnectionManager coordinates peer discovery, strategy selection, WireGuard peer configuration, and starts monitoring tasks.
- Health monitoring: Periodic latency checks; marks connections as connected/degraded/failed; attempts reconnection; switches relay if latency degrades.
- Automatic cleanup: Removes failed connections after a timeout threshold.

```mermaid
classDiagram
class ConnectionManager {
+connect_to_peer(party_id, peer_id) bool
+disconnect_from_peer(peer_id) void
+get_connection_status(peer_id) dict
-_monitor_connection(peer_id) void
-_cleanup_connection(peer_id) void
-_switch_relay(peer_id, connection) void
}
class PeerConnection {
+set_status(new_status) bool
+should_cleanup() bool
-status
-last_latency
-failed_at
-cleanup_timeout
}
ConnectionManager --> PeerConnection : "manages"
```

**Diagram sources**
- [core/connection.py](file://core/connection.py#L18-L125)
- [core/connection.py](file://core/connection.py#L439-L493)

**Section sources**
- [core/connection.py](file://core/connection.py#L38-L125)
- [core/connection.py](file://core/connection.py#L213-L333)
- [core/connection.py](file://core/connection.py#L334-L437)

### WireGuard Integration and Keepalive
- NetworkManager manages WireGuard interface creation, key generation, and peer configuration.
- Persistent keepalive is set to improve NAT traversal reliability and detect liveness.
- Latency measurement uses ICMP ping to assess connection health.

```mermaid
sequenceDiagram
participant CM as "ConnectionManager"
participant NM as "NetworkManager"
participant WG as "WireGuard Kernel/User-space"
CM->>NM : add_peer(peer_public_key, endpoint, allowed_ips)
NM->>WG : wg set interface_name peer ... persistent-keepalive=25
WG-->>NM : success
NM-->>CM : success
CM->>NM : measure_latency(virtual_ip)
NM->>NM : ping peer_ip
NM-->>CM : latency_ms or None
```

**Diagram sources**
- [core/network.py](file://core/network.py#L392-L443)
- [core/network.py](file://core/network.py#L340-L390)

**Section sources**
- [core/network.py](file://core/network.py#L25-L160)
- [core/network.py](file://core/network.py#L392-L443)
- [core/network.py](file://core/network.py#L340-L390)

### Relay Server Implementation
- Stateless UDP forwarder: Receives packets, identifies clients, and forwards to others without decrypting.
- Public key extraction from WireGuard handshake messages enables client tracking.
- Cleanup and statistics tasks manage stale clients and report metrics.

```mermaid
classDiagram
class RelayServer {
+start() void
+stop() void
+handle_packet(data, addr) void
-_extract_public_key(data) str
-_cleanup_task() void
-_stats_task() void
}
class RelayProtocol {
+connection_made(transport)
+datagram_received(data, addr)
}
RelayServer --> RelayProtocol : "uses"
```

**Diagram sources**
- [servers/relay_server.py](file://servers/relay_server.py#L30-L138)
- [servers/relay_server.py](file://servers/relay_server.py#L224-L256)

**Section sources**
- [servers/relay_server.py](file://servers/relay_server.py#L30-L138)
- [servers/relay_server.py](file://servers/relay_server.py#L224-L256)

### Control Plane Integration
- Peer discovery: ConnectionManager obtains peer NAT info via ControlPlane.
- Relay discovery: ConnectionCoordinator queries control plane for relay list and converts to internal format.
- Graceful fallback: If control plane is unavailable, uses configured or default relay.

**Section sources**
- [core/connection.py](file://core/connection.py#L53-L77)
- [core/control.py](file://core/control.py#L331-L345)
- [core/nat.py](file://core/nat.py#L399-L455)

## Dependency Analysis
Key dependencies and interactions:
- ConnectionManager depends on NATTraversal, ControlPlane, and NetworkManager.
- NATTraversal depends on Config and optionally ControlPlane for relay discovery.
- NetworkManager depends on Config and uses system commands to manage WireGuard.
- RelayServer is external to client runtime but participates in relay fallback.

```mermaid
graph LR
CM["ConnectionManager"] --> NT["NATTraversal"]
CM --> CP["ControlPlane"]
CM --> NM["NetworkManager"]
NT --> CFG["Config"]
CC["ConnectionCoordinator"] --> NT
CC --> CFG
NM --> CFG
RS["RelayServer"] -.-> NM
```

**Diagram sources**
- [core/connection.py](file://core/connection.py#L18-L33)
- [core/nat.py](file://core/nat.py#L53-L57)
- [core/network.py](file://core/network.py#L28-L35)
- [servers/relay_server.py](file://servers/relay_server.py#L38-L42)

**Section sources**
- [core/connection.py](file://core/connection.py#L18-L33)
- [core/nat.py](file://core/nat.py#L53-L57)
- [core/network.py](file://core/network.py#L28-L35)
- [servers/relay_server.py](file://servers/relay_server.py#L38-L42)

## Performance Considerations
- Direct P2P: Minimal latency overhead; high success rate for compatible NAT combinations.
- Hole-punched connections: Slightly higher latency due to timing and potential retries.
- Relay connections: Predictable overhead; latency dominated by geographic distance and relay load.
- Keepalive: Persistent keepalive improves NAT traversal stability and reduces false failures.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- NAT detection failures: Check firewall rules, test STUN connectivity, and try alternate networks.
- Hole punching failures: Expected for symmetric NAT; rely on automatic relay fallback.
- Slow relay connections: Switch to a closer relay, deploy more relays, or investigate network quality.

**Section sources**
- [docs/NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L486-L523)
- [tests/test_nat.py](file://tests/test_nat.py#L20-L100)

## Conclusion
LANrage’s NAT traversal strategy combines STUN-based detection, UDP hole punching, and relay fallback to maximize direct P2P connectivity while gracefully degrading to reliable relay tunnels. The system’s latency-aware relay selection, persistent keepalive, and continuous health monitoring ensure robust, adaptive connectivity across diverse network environments.