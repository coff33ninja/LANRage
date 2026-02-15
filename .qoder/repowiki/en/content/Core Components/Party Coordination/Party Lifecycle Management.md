# Party Lifecycle Management

<cite>
**Referenced Files in This Document**
- [party.py](file://core/party.py)
- [control.py](file://core/control.py)
- [control_client.py](file://core/control_client.py)
- [connection.py](file://core/connection.py)
- [nat.py](file://core/nat.py)
- [network.py](file://core/network.py)
- [ipam.py](file://core/ipam.py)
- [exceptions.py](file://core/exceptions.py)
- [config.py](file://core/config.py)
- [PARTY.md](file://docs/PARTY.md)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md)
- [test_party.py](file://tests/test_party.py)
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
10. [Appendices](#appendices)

## Introduction
This document provides a comprehensive guide to party lifecycle management in LANrage, focusing on the end-to-end processes for creating, joining, leaving, and dissolving parties. It documents the PartyManager.create_party() method, the join_party() workflow, the leave_party() process, and the underlying mechanisms for state persistence, session timeout handling, and automatic cleanup. It also covers error handling for network failures, control plane unavailability, and peer disconnections, and includes practical examples and troubleshooting guidance.

## Project Structure
The party lifecycle is orchestrated by several core modules:
- Party management and orchestration: core/party.py
- Control plane (peer discovery/signaling): core/control.py and core/control_client.py
- Connection orchestration and NAT traversal: core/connection.py and core/nat.py
- Network/WireGuard integration: core/network.py
- IP address management: core/ipam.py
- Configuration and exceptions: core/config.py and core/exceptions.py

```mermaid
graph TB
PM["PartyManager<br/>core/party.py"] --> CTRL["ControlPlane<br/>core/control.py"]
PM --> CONN["ConnectionManager<br/>core/connection.py"]
PM --> NET["NetworkManager<br/>core/network.py"]
PM --> NAT["NATTraversal<br/>core/nat.py"]
CONN --> IPAM["IPAddressPool<br/>core/ipam.py"]
CTRL --> CTRL_CLI["RemoteControlPlaneClient<br/>core/control_client.py"]
```

**Diagram sources**
- [party.py](file://core/party.py#L102-L304)
- [control.py](file://core/control.py#L187-L456)
- [connection.py](file://core/connection.py#L18-L493)
- [nat.py](file://core/nat.py#L41-L525)
- [network.py](file://core/network.py#L25-L515)
- [ipam.py](file://core/ipam.py#L10-L183)
- [control_client.py](file://core/control_client.py#L23-L438)

**Section sources**
- [party.py](file://core/party.py#L1-L304)
- [control.py](file://core/control.py#L1-L880)
- [connection.py](file://core/connection.py#L1-L493)
- [nat.py](file://core/nat.py#L1-L525)
- [network.py](file://core/network.py#L1-L515)
- [ipam.py](file://core/ipam.py#L1-L183)
- [control_client.py](file://core/control_client.py#L1-L438)

## Core Components
- PartyManager: Central orchestrator for party lifecycle, NAT initialization, control plane initialization, and peer connection management.
- ControlPlane: Local or remote control plane for peer discovery, signaling, and state persistence.
- ConnectionManager: Coordinates NAT traversal strategies, establishes WireGuard peers, monitors connections, and handles reconnection and cleanup.
- NATTraversal and ConnectionCoordinator: Determine connectivity strategies (direct vs relay), perform STUN-based NAT detection, and manage relay selection.
- NetworkManager: Manages WireGuard interface creation, key management, and latency measurement.
- IPAddressPool: Allocates and releases virtual IPs deterministically within a subnet.
- RemoteControlPlaneClient: HTTP client for centralized control plane server with heartbeat and retry logic.

**Section sources**
- [party.py](file://core/party.py#L102-L304)
- [control.py](file://core/control.py#L187-L456)
- [connection.py](file://core/connection.py#L18-L493)
- [nat.py](file://core/nat.py#L41-L525)
- [network.py](file://core/network.py#L25-L515)
- [ipam.py](file://core/ipam.py#L10-L183)
- [control_client.py](file://core/control_client.py#L23-L438)

## Architecture Overview
The party lifecycle integrates control plane registration, NAT traversal, and WireGuard peer configuration. The following sequence diagrams illustrate the key workflows.

```mermaid
sequenceDiagram
participant User as "User"
participant PM as "PartyManager"
participant CTRL as "ControlPlane"
participant NET as "NetworkManager"
participant NAT as "NATTraversal"
participant CONN as "ConnectionManager"
User->>PM : create_party(name)
PM->>PM : generate party_id and my_peer_id
PM->>NET : get public_key_b64
PM->>NAT : detect_nat() (optional)
PM->>CTRL : register_party(party_id, name, my_peer_info)
CTRL-->>PM : PartyInfo
PM->>PM : add self as host peer
PM-->>User : Party object
```

**Diagram sources**
- [party.py](file://core/party.py#L159-L196)
- [control.py](file://core/control.py#L228-L249)
- [network.py](file://core/network.py#L158-L160)
- [nat.py](file://core/nat.py#L64-L105)

```mermaid
sequenceDiagram
participant User as "User"
participant PM as "PartyManager"
participant CTRL as "ControlPlane"
participant CONN as "ConnectionManager"
participant PEER as "Peer"
User->>PM : join_party(party_id, peer_name)
PM->>PM : build PeerInfo with NAT details
PM->>CTRL : join_party(party_id, peer_info)
CTRL-->>PM : PartyInfo with peers
PM->>PM : convert to local Party format
PM->>CONN : connect_to_peer(party_id, peer_id) for each peer
CONN-->>PM : success/failure per peer
PM-->>User : Party object
```

**Diagram sources**
- [party.py](file://core/party.py#L198-L247)
- [control.py](file://core/control.py#L251-L267)
- [connection.py](file://core/connection.py#L38-L124)

```mermaid
sequenceDiagram
participant User as "User"
participant PM as "PartyManager"
participant CONN as "ConnectionManager"
participant CTRL as "ControlPlane"
User->>PM : leave_party()
PM->>CONN : disconnect_from_peer(peer_id) for each connection
PM->>CTRL : leave_party(party_id, my_peer_id)
PM-->>User : None (cleared current_party)
```

**Diagram sources**
- [party.py](file://core/party.py#L249-L261)
- [connection.py](file://core/connection.py#L126-L150)
- [control.py](file://core/control.py#L269-L293)

## Detailed Component Analysis

### PartyManager.create_party()
Party creation involves:
- Generating a unique party ID and a local peer ID.
- Building a PeerInfo object with NAT details (public/private IPs, ports, NAT type).
- Registering the party with the control plane.
- Adding the host as the first peer and setting current_party.

Key behaviors:
- Party ID generation uses a secure random token.
- NAT type is captured from NATTraversal if available.
- Control plane registration persists the party and host information.
- The host peer is assigned a fixed virtual IP (10.66.0.1).

```mermaid
flowchart TD
Start([create_party]) --> GenIDs["Generate party_id and my_peer_id"]
GenIDs --> BuildPeerInfo["Build PeerInfo with NAT details"]
BuildPeerInfo --> RegCtrl["Register with ControlPlane"]
RegCtrl --> AddHost["Add self as host peer"]
AddHost --> SetCurParty["Set current_party"]
SetCurParty --> End([Return Party])
```

**Diagram sources**
- [party.py](file://core/party.py#L159-L196)

**Section sources**
- [party.py](file://core/party.py#L159-L196)
- [control.py](file://core/control.py#L228-L249)
- [nat.py](file://core/nat.py#L64-L105)

### join_party() Workflow
Joining a party includes:
- Validating control plane and NAT availability.
- Constructing PeerInfo with NAT details.
- Joining via control plane and receiving the updated PartyInfo.
- Converting to local Party format and adding peers.
- Initiating asynchronous connections to existing peers.
- Updating peer connection_type upon success or failure.

```mermaid
flowchart TD
Start([join_party]) --> Validate["Validate control and NAT"]
Validate --> BuildPeerInfo["Build PeerInfo with NAT details"]
BuildPeerInfo --> JoinCtrl["Join via ControlPlane"]
JoinCtrl --> ReceiveParty["Receive PartyInfo with peers"]
ReceiveParty --> Convert["Convert to local Party format"]
Convert --> ConnectExisting["Connect to existing peers (async)"]
ConnectExisting --> SetCurParty["Set current_party"]
SetCurParty --> End([Return Party])
```

**Diagram sources**
- [party.py](file://core/party.py#L198-L247)
- [control.py](file://core/control.py#L251-L267)
- [connection.py](file://core/connection.py#L38-L124)

**Section sources**
- [party.py](file://core/party.py#L198-L247)
- [control.py](file://core/control.py#L251-L267)
- [connection.py](file://core/connection.py#L38-L124)

### leave_party() Process
Graceful departure includes:
- Iterating over active connections and removing WireGuard peers.
- Releasing virtual IPs back to the pool.
- Notifying the control plane to remove the peer from the party.
- Clearing the current party reference.

```mermaid
flowchart TD
Start([leave_party]) --> DisconnectAll["Disconnect from all peers"]
DisconnectAll --> RemoveWG["Remove WireGuard peers"]
RemoveWG --> ReleaseIP["Release virtual IPs"]
ReleaseIP --> LeaveCtrl["Leave via ControlPlane"]
LeaveCtrl --> ClearParty["Clear current_party"]
ClearParty --> End([Done])
```

**Diagram sources**
- [party.py](file://core/party.py#L249-L261)
- [connection.py](file://core/connection.py#L126-L150)

**Section sources**
- [party.py](file://core/party.py#L249-L261)
- [connection.py](file://core/connection.py#L126-L150)

### NAT Type Propagation and Compatibility
NAT type is propagated to the control plane and used to determine compatibility for direct P2P connections. The compatibility matrix defines which NAT types can connect directly without relay.

```mermaid
flowchart TD
DetectNAT["NATTraversal.detect_nat()"] --> StoreNAT["Store NAT type and endpoints"]
StoreNAT --> Register["Register PeerInfo with ControlPlane"]
Register --> Compatibility["Compute compatible peers"]
Compatibility --> Strategy["Direct or Relay strategy"]
```

**Diagram sources**
- [nat.py](file://core/nat.py#L64-L105)
- [party.py](file://core/party.py#L182-L194)
- [party.py](file://core/party.py#L73-L99)

**Section sources**
- [nat.py](file://core/nat.py#L64-L105)
- [party.py](file://core/party.py#L182-L194)
- [party.py](file://core/party.py#L73-L99)

### Automatic Peer Connection Establishment
On join, PartyManager schedules asynchronous connection tasks to existing peers. ConnectionManager coordinates NAT traversal, selects endpoints, adds WireGuard peers, and starts monitoring tasks.

```mermaid
sequenceDiagram
participant PM as "PartyManager"
participant CONN as "ConnectionManager"
participant COORD as "ConnectionCoordinator"
participant NAT as "NATTraversal"
participant NET as "NetworkManager"
PM->>CONN : connect_to_peer(party_id, peer_id)
CONN->>CONN : discover_peer via ControlPlane
CONN->>COORD : coordinate_connection(peer_public_key, peer_nat_info)
COORD->>NAT : can_direct_connect / get_connection_strategy
COORD-->>CONN : strategy and endpoint
CONN->>NET : add_peer(public_key, endpoint, allowed_ips)
CONN-->>PM : success/failure
```

**Diagram sources**
- [party.py](file://core/party.py#L262-L278)
- [connection.py](file://core/connection.py#L38-L124)
- [nat.py](file://core/nat.py#L330-L369)

**Section sources**
- [party.py](file://core/party.py#L262-L278)
- [connection.py](file://core/connection.py#L38-L124)
- [nat.py](file://core/nat.py#L330-L369)

### Party State Persistence and Cleanup
The control plane maintains state in a file-backed store with batched writes to reduce I/O. A periodic cleanup task removes stale peers and empty parties based on last_seen timestamps.

```mermaid
flowchart TD
Init["ControlPlane.initialize()"] --> LoadState["Load state from disk"]
LoadState --> StartCleanup["Start cleanup task (every minute)"]
StartCleanup --> CheckStale["Check peers older than 5 min"]
CheckStale --> RemovePeers["Remove stale peers"]
RemovePeers --> EmptyParties["Delete empty parties"]
EmptyParties --> Persist["Persist state (batched writes)"]
```

**Diagram sources**
- [control.py](file://core/control.py#L209-L217)
- [control.py](file://core/control.py#L378-L410)
- [control.py](file://core/control.py#L411-L424)

**Section sources**
- [control.py](file://core/control.py#L209-L217)
- [control.py](file://core/control.py#L378-L410)
- [control.py](file://core/control.py#L411-L424)

### Session Timeout Handling and Automatic Cleanup
- Control plane: Cleanup task removes peers older than 5 minutes and deletes empty parties.
- ConnectionManager: Monitors connection health, attempts reconnection, and auto-cleans failed connections after a timeout.
- RemoteControlPlaneClient: Maintains heartbeat to keep sessions alive.

```mermaid
flowchart TD
Heartbeat["RemoteControlPlaneClient heartbeat loop"] --> KeepAlive["Keep peer alive in ControlPlane"]
KeepAlive --> CleanupTask["ControlPlane cleanup task"]
CleanupTask --> RemoveStale["Remove stale peers"]
RemoveStale --> AutoClean["ConnectionManager auto-clean failed connections"]
AutoClean --> Disconnect["disconnect_from_peer()"]
```

**Diagram sources**
- [control_client.py](file://core/control_client.py#L404-L425)
- [control.py](file://core/control.py#L378-L410)
- [connection.py](file://core/connection.py#L306-L333)

**Section sources**
- [control_client.py](file://core/control_client.py#L404-L425)
- [control.py](file://core/control.py#L378-L410)
- [connection.py](file://core/connection.py#L306-L333)

### Error Handling
- Network failures: NAT detection and STUN requests handle timeouts and OS errors; ConnectionManager retries and switches relays.
- Control plane unavailability: RemoteControlPlaneClient falls back to local mode; PartyManager continues with NAT initialization and manual control plane usage.
- Peer disconnections: ConnectionManager monitors latency, attempts reconnection, and cleans up failed connections after timeout.
- Exceptions: Custom exceptions (NATError, STUNError, HolePunchError, PeerConnectionError, ConfigError, PartyError) categorize and propagate issues.

**Section sources**
- [nat.py](file://core/nat.py#L64-L105)
- [connection.py](file://core/connection.py#L213-L333)
- [control_client.py](file://core/control_client.py#L506-L524)
- [exceptions.py](file://core/exceptions.py#L10-L96)

## Dependency Analysis
Party lifecycle components depend on each other as follows:

```mermaid
graph TB
PartyManager --> ControlPlane
PartyManager --> ConnectionManager
PartyManager --> NetworkManager
PartyManager --> NATTraversal
ConnectionManager --> NATTraversal
ConnectionManager --> NetworkManager
ConnectionManager --> IPAddressPool
ControlPlane --> RemoteControlPlaneClient
```

**Diagram sources**
- [party.py](file://core/party.py#L102-L120)
- [connection.py](file://core/connection.py#L18-L36)
- [control.py](file://core/control.py#L187-L207)
- [control_client.py](file://core/control_client.py#L23-L438)

**Section sources**
- [party.py](file://core/party.py#L102-L120)
- [connection.py](file://core/connection.py#L18-L36)
- [control.py](file://core/control.py#L187-L207)
- [control_client.py](file://core/control_client.py#L23-L438)

## Performance Considerations
- Party creation: minimal network requests and CPU overhead.
- Joining: proportional to peer count; NAT traversal and WireGuard setup dominate cost.
- Status updates: latency measurements are on-demand and lightweight.
- Cleanup: periodic tasks avoid continuous scanning; batched state writes reduce disk I/O.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Cannot create party: Check internet/firewall; use local mode temporarily.
- Cannot join party: Verify party ID, host status, and recreate party if needed.
- Peer connection failed: Check NAT type, firewall (allow UDP 51820), and try different networks.
- High latency: Distinguish between base latency and LANrage overhead; optimize network or switch relay.

```mermaid
flowchart TD
Start([Party Issue]) --> Create{Can create party?}
Create --> |No| NetIssues["Check internet/firewall"]
NetIssues --> LocalMode["Use local mode temporarily"]
Create --> |Yes| Join{Can join party?}
Join --> |No| VerifyID["Verify party ID and host status"]
VerifyID --> Recreate["Recreate party with new ID"]
Join --> |Yes| Connect{Can connect to peers?}
Connect --> |No| NATCheck["Check NAT type and firewall"]
NATCheck --> TryDirect["Try direct connection or use relay"]
Connect --> |Yes| Latency{High latency?}
Latency --> |Yes| Optimize["Optimize network or switch relay"]
Latency --> |No| Success([Resolved])
```

**Diagram sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L11-L50)

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L372-L503)

## Conclusion
Party lifecycle management in LANrage is designed for reliability and adaptability. The PartyManager orchestrates control plane registration, NAT traversal, and connection establishment, while the control plane ensures persistence and cleanup. Robust error handling and automatic cleanup procedures help maintain a smooth gaming experience even under adverse network conditions.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Practical Examples
- Creating a party: Use PartyManager.create_party() to generate a party ID, register with the control plane, and add the host as the first peer.
- Joining a party: Use PartyManager.join_party() to obtain party information, convert to local format, and connect to existing peers.
- Leaving a party: Use PartyManager.leave_party() to gracefully disconnect peers, notify the control plane, and clear the current party.

**Section sources**
- [PARTY.md](file://docs/PARTY.md#L153-L214)
- [test_party.py](file://tests/test_party.py#L160-L196)

### NAT Compatibility Matrix
- Open NAT can connect to anyone.
- Full cone NAT can connect to others of compatible types.
- Restricted cone can connect with hole punching.
- Symmetric NAT requires relay.

**Section sources**
- [party.py](file://core/party.py#L19-L41)
- [nat.py](file://core/nat.py#L295-L322)