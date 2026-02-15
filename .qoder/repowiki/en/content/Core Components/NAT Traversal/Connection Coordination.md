# Connection Coordination

<cite>
**Referenced Files in This Document**
- [connection.py](file://core/connection.py)
- [nat.py](file://core/nat.py)
- [network.py](file://core/network.py)
- [control.py](file://core/control.py)
- [control_client.py](file://core/control_client.py)
- [party.py](file://core/party.py)
- [ipam.py](file://core/ipam.py)
- [task_manager.py](file://core/task_manager.py)
- [config.py](file://core/config.py)
- [test_connection.py](file://tests/test_connection.py)
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
This document explains the ConnectionCoordinator class and the peer connection orchestration system. It covers how connection strategies are determined (direct vs relay) based on NAT types, the peer coordination workflow from initial connection through fallback mechanisms, the relay discovery process integrating with the control plane, latency measurement and best relay selection, endpoint negotiation, strategy validation, and connection result reporting. It also documents the integration with the control plane for relay server discovery, the fallback hierarchy from control plane to configured relays to default servers, latency measurement techniques using ICMP ping, error handling for network failures, performance optimization strategies, coordination between multiple peers, connection state management, and graceful degradation when optimal connections cannot be established.

## Project Structure
The connection orchestration spans several modules:
- Connection orchestration and state management
- NAT traversal and strategy determination
- Network management (WireGuard)
- Control plane integration (peer discovery, relay listing)
- IP address management for virtual network
- Background task management

```mermaid
graph TB
subgraph "Core Modules"
CM["ConnectionManager<br/>core/connection.py"]
CC["ConnectionCoordinator<br/>core/nat.py"]
NT["NATTraversal<br/>core/nat.py"]
NM["NetworkManager<br/>core/network.py"]
CP["ControlPlane<br/>core/control.py"]
CPC["RemoteControlPlaneClient<br/>core/control_client.py"]
PM["PartyManager<br/>core/party.py"]
IPAM["IPAddressPool<br/>core/ipam.py"]
TM["TaskManager<br/>core/task_manager.py"]
CFG["Config<br/>core/config.py"]
end
PM --> CM
CM --> CC
CC --> NT
CM --> NM
CM --> CP
CC --> CPC
CM --> IPAM
CM --> TM
CM --> CFG
```

**Diagram sources**
- [connection.py](file://core/connection.py#L18-L125)
- [nat.py](file://core/nat.py#L330-L525)
- [network.py](file://core/network.py#L25-L515)
- [control.py](file://core/control.py#L187-L456)
- [control_client.py](file://core/control_client.py#L23-L438)
- [party.py](file://core/party.py#L102-L157)
- [ipam.py](file://core/ipam.py#L10-L183)
- [task_manager.py](file://core/task_manager.py#L11-L167)
- [config.py](file://core/config.py#L17-L114)

**Section sources**
- [connection.py](file://core/connection.py#L1-L125)
- [nat.py](file://core/nat.py#L1-L120)
- [network.py](file://core/network.py#L1-L120)
- [control.py](file://core/control.py#L1-L120)
- [control_client.py](file://core/control_client.py#L1-L120)
- [party.py](file://core/party.py#L1-L120)
- [ipam.py](file://core/ipam.py#L1-L120)
- [task_manager.py](file://core/task_manager.py#L1-L120)
- [config.py](file://core/config.py#L1-L120)

## Core Components
- ConnectionManager: Orchestrates peer connection lifecycle, strategy selection, WireGuard configuration, and monitoring.
- ConnectionCoordinator: Determines strategy (direct or relay), performs hole punching, and selects relay endpoints.
- NATTraversal: Detects NAT type, decides compatibility, and performs UDP hole punching.
- NetworkManager: Manages WireGuard interface, adds/removes peers, measures latency via ICMP ping.
- ControlPlane and RemoteControlPlaneClient: Peer discovery and relay server listing.
- IPAddressPool: Allocates virtual IPs for peers in the virtual network.
- TaskManager: Background task lifecycle management for monitoring and cleanup.
- Config: Provides runtime configuration including relay settings and control server URL.

**Section sources**
- [connection.py](file://core/connection.py#L18-L125)
- [nat.py](file://core/nat.py#L330-L525)
- [network.py](file://core/network.py#L25-L515)
- [control.py](file://core/control.py#L187-L456)
- [control_client.py](file://core/control_client.py#L23-L438)
- [ipam.py](file://core/ipam.py#L10-L183)
- [task_manager.py](file://core/task_manager.py#L11-L167)
- [config.py](file://core/config.py#L17-L114)

## Architecture Overview
The system integrates NAT detection, strategy determination, control plane discovery, and WireGuard configuration to establish peer-to-peer or relayed connections. The ConnectionManager coordinates the end-to-end flow, delegating strategy decisions to ConnectionCoordinator and NATTraversal, and managing WireGuard peer configuration and monitoring.

```mermaid
sequenceDiagram
participant PM as "PartyManager"
participant CM as "ConnectionManager"
participant CP as "ControlPlane"
participant CC as "ConnectionCoordinator"
participant NT as "NATTraversal"
participant NM as "NetworkManager"
PM->>CM : "connect_to_peer(party_id, peer_id)"
CM->>CP : "discover_peer(party_id, peer_id)"
CP-->>CM : "PeerInfo"
CM->>CC : "coordinate_connection(public_key, nat_info)"
CC->>NT : "get_connection_strategy(peer_nat_type)"
alt "Direct strategy"
CC->>NT : "attempt_hole_punch()"
NT-->>CC : "success/failure"
alt "Hole punch succeeds"
CC-->>CM : "{strategy : direct, endpoint}"
else "Hole punch fails"
CC-->>CM : "{strategy : relay}"
end
else "Relay strategy"
CC-->>CM : "{strategy : relay}"
end
CM->>NM : "add_peer(peer_public_key, endpoint, allowed_ips)"
CM-->>PM : "connection established"
```

**Diagram sources**
- [connection.py](file://core/connection.py#L38-L125)
- [nat.py](file://core/nat.py#L337-L369)
- [nat.py](file://core/nat.py#L371-L377)
- [nat.py](file://core/nat.py#L323-L327)

## Detailed Component Analysis

### ConnectionCoordinator
The ConnectionCoordinator encapsulates strategy determination and relay endpoint selection. It evaluates NAT compatibility and decides whether to attempt direct P2P with hole punching or fall back to relay. It discovers relays from the control plane, measures latency, and selects the best relay endpoint.

Key responsibilities:
- Strategy determination: Direct vs relay based on NAT compatibility.
- Direct connection attempt: Hole punching with NATTraversal.
- Relay discovery: Control plane integration, configured relay, default server fallback.
- Best relay selection: Latency measurement via ICMP ping.
- Endpoint negotiation: Returns endpoint string for NetworkManager.

```mermaid
classDiagram
class ConnectionCoordinator {
+coordinate_connection(peer_public_key, peer_nat_info) dict
+_attempt_direct_connection(peer_nat_info) bool
+_get_relay_endpoint() str
+_discover_relays() list
+_select_best_relay(relays) dict
+_measure_relay_latency(relay_ip) float
-config Config
-nat NATTraversal
}
class NATTraversal {
+detect_nat() STUNResponse
+attempt_hole_punch(peer_public_ip, peer_public_port, local_port) bool
+get_connection_strategy(peer_nat_type) str
+can_direct_connect(peer_nat_type) bool
}
ConnectionCoordinator --> NATTraversal : "uses"
```

**Diagram sources**
- [nat.py](file://core/nat.py#L330-L525)
- [nat.py](file://core/nat.py#L41-L106)
- [nat.py](file://core/nat.py#L244-L294)
- [nat.py](file://core/nat.py#L323-L327)

**Section sources**
- [nat.py](file://core/nat.py#L330-L525)

### ConnectionManager
The ConnectionManager orchestrates the end-to-end connection process:
- Discovers peer via ControlPlane.
- Coordinates strategy via ConnectionCoordinator.
- Configures WireGuard peer with negotiated endpoint.
- Allocates virtual IP via IPAM.
- Starts monitoring and cleanup tasks.
- Monitors connection health, handles reconnection, and switches relays when latency is high.
- Reports connection status including latency and strategy.

```mermaid
flowchart TD
Start(["connect_to_peer"]) --> Discover["discover_peer via ControlPlane"]
Discover --> Strategy["coordinate_connection via ConnectionCoordinator"]
Strategy --> Decision{"strategy == direct?"}
Decision --> |Yes| Direct["attempt_hole_punch"]
Direct --> DirectOK{"success?"}
DirectOK --> |Yes| Configure["add_peer to NetworkManager"]
DirectOK --> |No| Relay["use relay endpoint"]
Decision --> |No| Relay
Relay --> Configure
Configure --> IP["allocate virtual IP via IPAM"]
IP --> Record["create PeerConnection record"]
Record --> Monitor["start monitoring task"]
Monitor --> Health{"latency ok?"}
Health --> |No| Reconnect["reconnect attempts"]
Health --> |Yes| Degraded{"latency > 200ms?"}
Degraded --> |Yes| Switch["switch relay if strategy==relay"]
Degraded --> |No| Stable["keep connection"]
Reconnect --> Health
Switch --> Health
```

**Diagram sources**
- [connection.py](file://core/connection.py#L38-L125)
- [connection.py](file://core/connection.py#L213-L305)
- [connection.py](file://core/connection.py#L334-L437)

**Section sources**
- [connection.py](file://core/connection.py#L18-L125)
- [connection.py](file://core/connection.py#L213-L305)
- [connection.py](file://core/connection.py#L334-L437)

### NAT Traversal and Strategy Determination
NATTraversal detects NAT type using STUN and determines compatibility for direct P2P. It also performs UDP hole punching to attempt direct connections. The strategy is derived from compatibility checks.

```mermaid
flowchart TD
Detect["detect_nat via STUN"] --> Type["determine NATType"]
Type --> Compatibility["can_direct_connect(peer_nat_type)"]
Compatibility --> |Yes| Direct["get_connection_strategy -> direct"]
Compatibility --> |No| Relay["get_connection_strategy -> relay"]
```

**Diagram sources**
- [nat.py](file://core/nat.py#L64-L106)
- [nat.py](file://core/nat.py#L295-L327)

**Section sources**
- [nat.py](file://core/nat.py#L41-L106)
- [nat.py](file://core/nat.py#L295-L327)

### Relay Discovery and Best Relay Selection
Relay discovery follows a strict hierarchy:
1. Control plane: RemoteControlPlaneClient.list_relays().
2. Configured relay: Config.relay_public_ip/port.
3. Default server: relay.lanrage.io:51820.

Best relay selection measures latency to each candidate using ICMP ping and picks the lowest-latency option. If latency measurement fails, it falls back to the first available relay.

```mermaid
flowchart TD
Discover["discover_relays()"] --> CP{"control_client available?"}
CP --> |Yes| CPList["list_relays()"]
CP --> |No| ConfigCheck{"configured relay?"}
CPList --> Relays["relays[]"]
ConfigCheck --> |Yes| AddConfig["append configured relay"]
ConfigCheck --> |No| Default["append default relay"]
AddConfig --> Relays
Default --> Relays
Relays --> Select["_select_best_relay()"]
Select --> Measure["_measure_relay_latency()"]
Measure --> Best{"lowest latency?"}
Best --> |Yes| Endpoint["return best endpoint"]
Best --> |No| First["fallback to first relay"]
```

**Diagram sources**
- [nat.py](file://core/nat.py#L399-L455)
- [nat.py](file://core/nat.py#L457-L479)
- [nat.py](file://core/nat.py#L481-L525)
- [control_client.py](file://core/control_client.py#L373-L402)

**Section sources**
- [nat.py](file://core/nat.py#L399-L455)
- [nat.py](file://core/nat.py#L457-L479)
- [nat.py](file://core/nat.py#L481-L525)
- [control_client.py](file://core/control_client.py#L373-L402)

### Endpoint Negotiation and Validation
Endpoint negotiation occurs after strategy selection:
- Direct strategy: Endpoint is the peer’s public endpoint.
- Relay strategy: Endpoint is the best relay endpoint chosen by ConnectionCoordinator.

Validation includes:
- Strategy validation against NAT compatibility.
- Endpoint existence and reachability (via ICMP ping).
- WireGuard peer configuration success.

**Section sources**
- [nat.py](file://core/nat.py#L337-L369)
- [connection.py](file://core/connection.py#L89-L114)
- [network.py](file://core/network.py#L392-L420)

### Connection Result Reporting
ConnectionManager reports:
- Peer ID, virtual IP, endpoint, strategy, latency, connected time, and status.
- Status transitions: connecting → connected/degraded/failed/cleanup.
- Auto-cleanup after a timeout when connection fails.

**Section sources**
- [connection.py](file://core/connection.py#L152-L179)
- [connection.py](file://core/connection.py#L439-L493)

### Coordination Between Multiple Peers
PartyManager initializes NAT, control plane, and connection manager, then connects to all existing peers upon joining a party. It updates peer statuses based on connection outcomes.

```mermaid
sequenceDiagram
participant PM as "PartyManager"
participant CP as "ControlPlane"
participant CM as "ConnectionManager"
participant NM as "NetworkManager"
PM->>CP : "join_party(party_id, peer_info)"
CP-->>PM : "PartyInfo"
PM->>CM : "connect_to_peer(party_id, peer_id)"
CM->>NM : "add_peer(...)"
CM-->>PM : "success/failure"
PM->>PM : "update peer.connection_type"
```

**Diagram sources**
- [party.py](file://core/party.py#L198-L247)
- [connection.py](file://core/connection.py#L38-L125)

**Section sources**
- [party.py](file://core/party.py#L198-L247)
- [connection.py](file://core/connection.py#L38-L125)

## Dependency Analysis
The ConnectionCoordinator depends on NATTraversal for strategy and hole punching, and optionally on RemoteControlPlaneClient for relay discovery. ConnectionManager depends on ConnectionCoordinator, NetworkManager, ControlPlane, IPAM, and TaskManager. The control plane integration is optional but enables dynamic relay discovery.

```mermaid
graph LR
CC["ConnectionCoordinator"] --> NT["NATTraversal"]
CC --> CPC["RemoteControlPlaneClient"]
CM["ConnectionManager"] --> CC
CM --> NM["NetworkManager"]
CM --> CP["ControlPlane"]
CM --> IPAM["IPAddressPool"]
CM --> TM["TaskManager"]
CM --> CFG["Config"]
```

**Diagram sources**
- [nat.py](file://core/nat.py#L330-L525)
- [connection.py](file://core/connection.py#L18-L125)
- [control_client.py](file://core/control_client.py#L23-L438)

**Section sources**
- [nat.py](file://core/nat.py#L330-L525)
- [connection.py](file://core/connection.py#L18-L125)
- [control_client.py](file://core/control_client.py#L23-L438)

## Performance Considerations
- Latency measurement: ICMP ping is used for both peer latency and relay selection. On Windows and Unix, the command-line ping is executed asynchronously with timeouts.
- Keepalive: Persistent keepalive is enabled for WireGuard peers to improve NAT traversal reliability.
- Monitoring intervals: Connection monitoring runs every 30 seconds to balance responsiveness and resource usage.
- Fallback hierarchy: Control plane discovery, configured relay, and default server ensure resilience when upstream services are unavailable.
- IPAM scalability: Subnet expansion allows allocation across multiple /24 subnets within the base /16.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- NAT detection failures: Check firewall settings, test STUN connectivity, and try different networks.
- Hole punching failures: Symmetric NAT or strict firewalls require relay fallback.
- Relay connection slowness: Use a closer relay or deploy more relays; check network quality.
- Control plane unavailability: Falls back to configured or default relay; ensure configuration is correct.
- Connection monitoring false positives: Reconnection attempts are limited; high latency triggers relay switching for relay strategies.

**Section sources**
- [nat.py](file://core/nat.py#L64-L106)
- [nat.py](file://core/nat.py#L244-L294)
- [nat.py](file://core/nat.py#L481-L525)
- [connection.py](file://core/connection.py#L213-L305)
- [connection.py](file://core/connection.py#L334-L437)

## Conclusion
The ConnectionCoordinator and ConnectionManager implement a robust, layered approach to peer connection orchestration. Strategy selection is grounded in NAT compatibility, with automatic fallback to relay when direct connections are not feasible. Control plane integration enables dynamic relay discovery, while latency measurement and periodic monitoring ensure optimal performance and graceful degradation. The system balances simplicity with resilience, enabling reliable peer-to-peer or relayed connections across diverse network environments.