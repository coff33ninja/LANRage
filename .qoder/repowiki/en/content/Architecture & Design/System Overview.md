# System Overview

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [ARCHITECTURE.md](file://docs/ARCHITECTURE.md)
- [CONTROL_PLANE.md](file://docs/CONTROL_PLANE.md)
- [NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md)
- [NETWORK.md](file://docs/NETWORK.md)
- [lanrage.py](file://lanrage.py)
- [api/server.py](file://api/server.py)
- [core/config.py](file://core/config.py)
- [core/control.py](file://core/control.py)
- [core/nat.py](file://core/nat.py)
- [core/network.py](file://core/network.py)
- [core/connection.py](file://core/connection.py)
- [core/party.py](file://core/party.py)
- [core/ipam.py](file://core/ipam.py)
- [core/task_manager.py](file://core/task_manager.py)
- [servers/control_server.py](file://servers/control_server.py)
- [servers/relay_server.py](file://servers/relay_server.py)
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
LANrage is a zero-configuration mesh VPN designed to make online gaming feel like a LAN party. It solves the fundamental problem of gaming networking over the internet—where traditional NAT traversal and port forwarding create latency-heavy, unreliable connections—by combining:
- Direct peer-to-peer (P2P) connectivity when possible
- Smart relay fallback for NAT traversal
- A virtual LAN overlay with broadcast/multicast emulation
- Game-aware profiles and QoS
- A clean web UI and REST API

Its core design philosophy prioritizes gamers: latency obsession, zero configuration, and open-source simplicity. The system achieves near-LAN performance by leveraging WireGuard for secure, low-latency tunnels and implementing robust NAT traversal with STUN/UDP hole punching and relay selection.

**Section sources**
- [README.md](file://README.md#L22-L56)
- [README.md](file://README.md#L326-L333)

## Project Structure
LANrage is organized around a modular Python architecture with three primary layers:
- Control plane: Peer discovery, party management, and relay coordination
- Data plane: WireGuard-based virtual network and peer tunnels
- Client application: Local API server, web UI, and runtime orchestration

```mermaid
graph TB
subgraph "Client Runtime"
A["lanrage.py<br/>Entry point"]
B["api/server.py<br/>FastAPI server"]
C["core/party.py<br/>PartyManager"]
D["core/network.py<br/>NetworkManager"]
E["core/control.py<br/>ControlPlane"]
F["core/nat.py<br/>NATTraversal"]
G["core/connection.py<br/>ConnectionManager"]
H["core/ipam.py<br/>IPAddressPool"]
I["core/task_manager.py<br/>TaskManager"]
end
subgraph "Control Plane Server"
J["servers/control_server.py<br/>Centralized control plane"]
end
subgraph "Relay Infrastructure"
K["servers/relay_server.py<br/>Stateless relay"]
end
A --> B
A --> C
A --> D
A --> E
A --> F
A --> G
A --> H
A --> I
C --> E
C --> F
C --> G
G --> D
G --> H
E --> J
F --> K
```

**Diagram sources**
- [lanrage.py](file://lanrage.py#L40-L154)
- [api/server.py](file://api/server.py#L680-L701)
- [core/party.py](file://core/party.py#L102-L158)
- [core/network.py](file://core/network.py#L25-L41)
- [core/control.py](file://core/control.py#L187-L227)
- [core/nat.py](file://core/nat.py#L41-L63)
- [core/connection.py](file://core/connection.py#L18-L37)
- [core/ipam.py](file://core/ipam.py#L10-L32)
- [core/task_manager.py](file://core/task_manager.py#L11-L25)
- [servers/control_server.py](file://servers/control_server.py#L231-L242)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L80)

**Section sources**
- [lanrage.py](file://lanrage.py#L40-L154)
- [api/server.py](file://api/server.py#L680-L701)

## Core Components
- Control plane (SQLite-based or remote WebSocket-based)
  - Peer discovery, party registration, heartbeat, and cleanup
  - Local file-based discovery and remote control plane integration
- Data plane (WireGuard)
  - Encrypted tunnels, direct P2P or relayed paths, MTU and keepalive tuning
- Client application
  - Local API server, web UI, network manager, party manager, and metrics
- Relay nodes
  - Stateless packet forwarders with optional discovery and selection

**Section sources**
- [ARCHITECTURE.md](file://docs/ARCHITECTURE.md#L7-L38)
- [CONTROL_PLANE.md](file://docs/CONTROL_PLANE.md#L1-L629)
- [NETWORK.md](file://docs/NETWORK.md#L1-L453)

## Architecture Overview
LANrage’s three-tier architecture separates concerns:
- Control plane: Manages identity, discovery, and signaling
- Data plane: Provides encrypted, low-latency tunnels
- Client application: Orchestrates initialization, NAT traversal, and user experience

```mermaid
graph TB
subgraph "Control Plane"
CP_Local["LocalControlPlane<br/>File-based discovery"]
CP_Remote["RemoteControlPlane<br/>WebSocket client"]
CP_Server["Control Plane Server<br/>SQLite registry"]
end
subgraph "Data Plane"
WG["WireGuard Interface<br/>lanrage0"]
Relay["Relay Nodes<br/>Stateless forwarding"]
end
subgraph "Client App"
PM["PartyManager"]
CM["ConnectionManager"]
NM["NetworkManager"]
IM["IPAddressPool"]
end
PM --> CP_Local
PM --> CP_Remote
CP_Remote --> CP_Server
PM --> CM
CM --> NM
CM --> IM
NM --> WG
CM --> Relay
```

**Diagram sources**
- [core/control.py](file://core/control.py#L458-L539)
- [core/control.py](file://core/control.py#L541-L800)
- [servers/control_server.py](file://servers/control_server.py#L231-L242)
- [core/connection.py](file://core/connection.py#L18-L37)
- [core/network.py](file://core/network.py#L25-L41)
- [core/ipam.py](file://core/ipam.py#L10-L32)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L80)

**Section sources**
- [ARCHITECTURE.md](file://docs/ARCHITECTURE.md#L3-L91)

## Detailed Component Analysis

### Control Plane
The control plane coordinates peer discovery and party lifecycle:
- Local mode uses a shared discovery file for LAN-only scenarios
- Remote mode connects to a centralized control plane server via WebSocket
- Persistent state stored in JSON with batched writes to reduce I/O
- Cleanup task removes stale peers and empty parties

```mermaid
classDiagram
class ControlPlane {
+initialize()
+register_party(party_id, name, host_peer_info)
+join_party(party_id, peer_info)
+leave_party(party_id, peer_id)
+update_peer(party_id, peer_info)
+get_party(party_id)
+get_peers(party_id)
+discover_peer(party_id, peer_id)
+heartbeat(party_id, peer_id)
-_save_state()
-_load_state()
-_cleanup_task()
}
class LocalControlPlane {
+_announce_party(party)
+discover_parties()
}
class RemoteControlPlane {
+initialize()
+_connect()
+_authenticate()
+_handle_messages()
+_reconnect()
+close()
}
ControlPlane <|-- LocalControlPlane
ControlPlane <|-- RemoteControlPlane
```

**Diagram sources**
- [core/control.py](file://core/control.py#L187-L227)
- [core/control.py](file://core/control.py#L458-L539)
- [core/control.py](file://core/control.py#L541-L800)

**Section sources**
- [CONTROL_PLANE.md](file://docs/CONTROL_PLANE.md#L1-L629)
- [core/control.py](file://core/control.py#L19-L114)

### NAT Traversal and Relay Selection
LANrage detects NAT type using STUN, performs UDP hole punching, and falls back to relay servers when needed. It selects the best relay by latency measurement and supports multi-region discovery.

```mermaid
sequenceDiagram
participant PM as "PartyManager"
participant NAT as "NATTraversal"
participant CC as "ConnectionCoordinator"
participant CP as "ControlPlane"
participant WG as "NetworkManager"
PM->>NAT : detect_nat()
NAT-->>PM : STUNResponse(nat_type, endpoints)
PM->>CC : coordinate_connection(peer_public_key, peer_nat_info)
CC->>NAT : can_direct_connect(peer_nat_type)
alt Direct possible
CC->>NAT : attempt_hole_punch(peer_public_ip, peer_public_port)
NAT-->>CC : success/failure
else Relay fallback
CC->>CP : list_relays() (optional)
CP-->>CC : relays[]
CC->>CC : _select_best_relay(relays)
end
CC-->>PM : strategy=direct/relay, endpoint
PM->>WG : add_peer(peer_public_key, endpoint, allowed_ips)
```

**Diagram sources**
- [core/nat.py](file://core/nat.py#L41-L106)
- [core/nat.py](file://core/nat.py#L200-L276)
- [core/nat.py](file://core/nat.py#L330-L398)
- [core/connection.py](file://core/connection.py#L38-L125)
- [core/network.py](file://core/network.py#L392-L420)

**Section sources**
- [NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L1-L562)
- [core/nat.py](file://core/nat.py#L19-L106)
- [core/nat.py](file://core/nat.py#L330-L398)
- [core/connection.py](file://core/connection.py#L38-L125)

### Data Plane: WireGuard Interface and Virtual Network
The data plane manages the WireGuard interface, peer configuration, and latency measurement. It enforces a virtual LAN subnet and MTU suitable for gaming.

```mermaid
flowchart TD
Start(["Initialize NetworkManager"]) --> CheckWG["Check WireGuard availability"]
CheckWG --> EnsureKeys["Ensure/load keys"]
EnsureKeys --> CreateIF["Create interface (Windows/Linux)"]
CreateIF --> AddPeer["add_peer(peer_key, endpoint, allowed_ips)"]
AddPeer --> Measure["measure_latency(peer_ip)"]
Measure --> Done(["Ready"])
```

**Diagram sources**
- [core/network.py](file://core/network.py#L70-L94)
- [core/network.py](file://core/network.py#L123-L160)
- [core/network.py](file://core/network.py#L161-L310)
- [core/network.py](file://core/network.py#L392-L420)
- [core/network.py](file://core/network.py#L340-L391)

**Section sources**
- [NETWORK.md](file://docs/NETWORK.md#L1-L453)
- [core/network.py](file://core/network.py#L25-L94)

### Virtual Network Topology, Subnet Allocation, and Interface Management
- Virtual subnet: 10.66.0.0/16 with interface lanrage0
- MTU: 1420 to account for WireGuard overhead
- IPAM allocates per-peer virtual IPs from sequential /24 subnets within the base subnet
- ConnectionManager assigns virtual IPs and configures WireGuard peers

```mermaid
graph LR
subgraph "Virtual LAN (10.66.0.0/16)"
Host["Host: 10.66.0.1"]
PeerA["Peer A: 10.66.0.2"]
PeerB["Peer B: 10.66.0.3"]
Relay["Relay: 10.66.x.y"]
end
Host --- PeerA
Host --- PeerB
Host -.-> Relay
```

**Diagram sources**
- [NETWORK.md](file://docs/NETWORK.md#L267-L288)
- [core/ipam.py](file://core/ipam.py#L10-L32)
- [core/connection.py](file://core/connection.py#L181-L212)

**Section sources**
- [NETWORK.md](file://docs/NETWORK.md#L267-L288)
- [core/ipam.py](file://core/ipam.py#L55-L98)
- [core/connection.py](file://core/connection.py#L181-L212)

### Security Model
- Transport encryption: WireGuard ChaCha20-Poly1305 with X25519 key exchange
- Authentication: Public key cryptography; peers exchange WireGuard public keys
- Trust model: Peer-to-peer with trustless relay nodes that never decrypt traffic
- Control plane: Optional remote control plane with future authentication

```mermaid
graph TB
A["Peer A<br/>WireGuard pubkey"] -- "Encrypted tunnel" --> B["Peer B<br/>WireGuard pubkey"]
A -. "Relay (no decryption)" .-> C["Relay Node"]
C -. "Relay (no decryption)" .-> B
```

**Diagram sources**
- [ARCHITECTURE.md](file://docs/ARCHITECTURE.md#L79-L91)
- [NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L479-L485)
- [NETWORK.md](file://docs/NETWORK.md#L351-L372)

**Section sources**
- [ARCHITECTURE.md](file://docs/ARCHITECTURE.md#L79-L91)
- [NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L463-L485)
- [NETWORK.md](file://docs/NETWORK.md#L351-L372)

### Client Application Lifecycle: From Initialization to Active Gaming
The client initializes settings, network, NAT detection, control plane, and starts the API server. Users create or join parties, which triggers peer discovery, NAT traversal, and WireGuard configuration.

```mermaid
sequenceDiagram
participant User as "User"
participant Entry as "lanrage.py"
participant API as "api/server.py"
participant Party as "PartyManager"
participant Conn as "ConnectionManager"
participant Net as "NetworkManager"
participant Ctrl as "ControlPlane"
participant Nat as "NATTraversal"
User->>Entry : Launch LANrage
Entry->>Entry : Load settings/config
Entry->>Net : initialize()
Entry->>Nat : initialize_nat()
Entry->>Party : initialize_control()
Party->>Ctrl : initialize()
Entry->>API : start_api_server()
User->>API : POST /party/create
API->>Party : create_party(name)
Party->>Ctrl : register_party(...)
Party->>Conn : connect_to_peer(party_id, peer_id)
Conn->>Ctrl : discover_peer(...)
Conn->>Nat : coordinate_connection(...)
Nat-->>Conn : strategy + endpoint
Conn->>Net : add_peer(peer_key, endpoint, allowed_ips)
Net-->>Conn : success
Conn-->>Party : connection established
Party-->>API : party status
API-->>User : UI reflects active session
```

**Diagram sources**
- [lanrage.py](file://lanrage.py#L40-L154)
- [api/server.py](file://api/server.py#L155-L175)
- [core/party.py](file://core/party.py#L159-L196)
- [core/connection.py](file://core/connection.py#L38-L125)
- [core/network.py](file://core/network.py#L392-L420)
- [core/control.py](file://core/control.py#L228-L267)
- [core/nat.py](file://core/nat.py#L330-L398)

**Section sources**
- [lanrage.py](file://lanrage.py#L40-L154)
- [api/server.py](file://api/server.py#L155-L175)
- [core/party.py](file://core/party.py#L159-L196)
- [core/connection.py](file://core/connection.py#L38-L125)

## Dependency Analysis
Key dependencies and interactions:
- PartyManager depends on NetworkManager, NATTraversal, and ControlPlane
- ConnectionManager depends on NetworkManager, NATTraversal, and IPAM
- ControlPlane integrates with LocalControlPlane/RemoteControlPlane and optionally a centralized control plane server
- NATTraversal integrates with ConnectionCoordinator and optionally queries the control plane for relay discovery
- API server orchestrates PartyManager, NetworkManager, Metrics, Discord, and ServerBrowser

```mermaid
graph LR
PartyMgr["PartyManager"] --> NetMgr["NetworkManager"]
PartyMgr --> Ctrl["ControlPlane"]
PartyMgr --> Nat["NATTraversal"]
ConnMgr["ConnectionManager"] --> NetMgr
ConnMgr --> Nat
ConnMgr --> IPAM["IPAddressPool"]
Nat --> CC["ConnectionCoordinator"]
CC --> Ctrl
Entry["lanrage.py"] --> PartyMgr
Entry --> NetMgr
Entry --> API["api/server.py"]
API --> PartyMgr
API --> NetMgr
```

**Diagram sources**
- [core/party.py](file://core/party.py#L102-L158)
- [core/connection.py](file://core/connection.py#L18-L37)
- [core/network.py](file://core/network.py#L25-L41)
- [core/nat.py](file://core/nat.py#L330-L398)
- [core/ipam.py](file://core/ipam.py#L10-L32)
- [lanrage.py](file://lanrage.py#L108-L154)
- [api/server.py](file://api/server.py#L680-L701)

**Section sources**
- [core/party.py](file://core/party.py#L102-L158)
- [core/connection.py](file://core/connection.py#L18-L37)
- [core/nat.py](file://core/nat.py#L330-L398)
- [core/network.py](file://core/network.py#L25-L41)
- [core/ipam.py](file://core/ipam.py#L10-L32)
- [lanrage.py](file://lanrage.py#L108-L154)
- [api/server.py](file://api/server.py#L680-L701)

## Performance Considerations
- Latency targets
  - Direct P2P: <1ms overhead
  - Same-region relay: 5–15ms overhead
  - Cross-region relay: 30–100ms overhead
- Throughput: Line speed with WireGuard overhead
- CPU/memory: <5% idle, <15% active; <100MB per client
- MTU: 1420 bytes; persistent keepalive 25 seconds for NAT traversal
- Scalability: Single relay 50–100 concurrent connections, 500 Mbps throughput; relay pools with anycast and auto-scaling

**Section sources**
- [ARCHITECTURE.md](file://docs/ARCHITECTURE.md#L119-L172)
- [NETWORK.md](file://docs/NETWORK.md#L325-L350)

## Troubleshooting Guide
Common issues and resolutions:
- NAT detection failures
  - Cause: Firewall blocking UDP, STUN unreachable
  - Resolution: Check firewall, test STUN manually, try different network
- Hole punching failures
  - Cause: Symmetric NAT, strict firewall, timing
  - Resolution: Automatic relay fallback, retry on different network
- Relay connection slowness
  - Cause: Geographic distance, overload, congestion
  - Resolution: Use closer relay, deploy more relays, check network quality
- WireGuard not found
  - Cause: Missing WireGuard, insufficient privileges
  - Resolution: Install WireGuard, run as admin/root, ensure port 51820 available
- Peer unreachable
  - Cause: Incorrect endpoint, firewall, NAT traversal issues
  - Resolution: Verify endpoint, allow UDP 51820, test ping, check NAT status

**Section sources**
- [NAT_TRAVERSAL.md](file://docs/NAT_TRAVERSAL.md#L486-L523)
- [NETWORK.md](file://docs/NETWORK.md#L373-L410)

## Conclusion
LANrage’s mesh VPN architecture delivers a zero-configuration, latency-first gaming experience by combining robust NAT traversal, a secure WireGuard data plane, and a practical control plane. Its three-tier design cleanly separates discovery/signaling, transport, and application concerns, enabling scalable, reliable peer-to-peer gaming over the internet with minimal friction.