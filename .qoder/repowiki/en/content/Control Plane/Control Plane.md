# Control Plane

<cite>
**Referenced Files in This Document**
- [core/control.py](file://core/control.py)
- [core/control_client.py](file://core/control_client.py)
- [servers/control_server.py](file://servers/control_server.py)
- [servers/relay_server.py](file://servers/relay_server.py)
- [core/network.py](file://core/network.py)
- [core/nat.py](file://core/nat.py)
- [core/settings.py](file://core/settings.py)
- [core/config.py](file://core/config.py)
- [docs/CONTROL_PLANE.md](file://docs/CONTROL_PLANE.md)
- [docs/RELAY_SERVER.md](file://docs/RELAY_SERVER.md)
- [docs/ARCHITECTURE.md](file://docs/ARCHITECTURE.md)
- [.env.example](file://.env.example)
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
This document describes LANrage’s control plane system responsible for peer discovery, key exchange, and session management. It explains how the system discovers peers, coordinates sessions, persists state, and integrates with relay servers for NAT traversal. It also documents the control server architecture, relay server implementation, database integration, security measures, and deployment guidelines.

## Project Structure
The control plane spans several modules:
- Core control plane logic and state persistence
- Remote control plane client for HTTP-based coordination
- Control plane server with FastAPI and SQLite
- Relay server for stateless packet forwarding
- Network and NAT traversal utilities for key exchange and connectivity
- Settings and configuration management

```mermaid
graph TB
subgraph "Core"
A["core/control.py<br/>ControlPlane, LocalControlPlane, RemoteControlPlane"]
B["core/control_client.py<br/>RemoteControlPlaneClient"]
C["core/network.py<br/>WireGuard key generation"]
D["core/nat.py<br/>NAT detection, hole punching"]
E["core/settings.py<br/>SettingsDatabase"]
F["core/config.py<br/>Config model"]
end
subgraph "Servers"
G["servers/control_server.py<br/>FastAPI control plane server"]
H["servers/relay_server.py<br/>Stateless relay server"]
end
subgraph "Docs"
I["docs/CONTROL_PLANE.md"]
J["docs/RELAY_SERVER.md"]
K["docs/ARCHITECTURE.md"]
end
A --> B
B --> G
A --> H
C --> G
D --> G
E --> F
F --> G
F --> H
I --> A
J --> H
K --> A
```

**Diagram sources**
- [core/control.py](file://core/control.py#L187-L880)
- [core/control_client.py](file://core/control_client.py#L23-L438)
- [servers/control_server.py](file://servers/control_server.py#L1-L729)
- [servers/relay_server.py](file://servers/relay_server.py#L1-L297)
- [core/network.py](file://core/network.py#L25-L515)
- [core/nat.py](file://core/nat.py#L41-L525)
- [core/settings.py](file://core/settings.py#L20-L525)
- [core/config.py](file://core/config.py#L17-L114)
- [docs/CONTROL_PLANE.md](file://docs/CONTROL_PLANE.md#L1-L629)
- [docs/RELAY_SERVER.md](file://docs/RELAY_SERVER.md#L1-L544)
- [docs/ARCHITECTURE.md](file://docs/ARCHITECTURE.md#L1-L206)

**Section sources**
- [docs/ARCHITECTURE.md](file://docs/ARCHITECTURE.md#L1-L206)

## Core Components
- ControlPlane: In-memory party registry with file-backed persistence and cleanup.
- LocalControlPlane: File-based discovery for local LAN testing.
- RemoteControlPlane: HTTP client to a centralized control plane server.
- RemoteControlPlaneClient: Async HTTP client with retry/backoff and heartbeat.
- Control Plane Server: FastAPI service with SQLite for persistent state, authentication tokens, and relay registry.
- Relay Server: Stateless UDP packet forwarder for NAT traversal.
- Network Manager: WireGuard key generation and interface management.
- NAT Traversal: STUN-based NAT detection and UDP hole punching.
- Settings Database: SQLite-backed settings store with typed serialization.

**Section sources**
- [core/control.py](file://core/control.py#L187-L880)
- [core/control_client.py](file://core/control_client.py#L23-L438)
- [servers/control_server.py](file://servers/control_server.py#L1-L729)
- [servers/relay_server.py](file://servers/relay_server.py#L1-L297)
- [core/network.py](file://core/network.py#L25-L515)
- [core/nat.py](file://core/nat.py#L41-L525)
- [core/settings.py](file://core/settings.py#L20-L525)

## Architecture Overview
The control plane architecture separates concerns:
- Control Plane (SQLite): Persistent registry of parties, peers, and relay servers; authentication tokens.
- Data Plane (WireGuard): Encrypted P2P tunnels with optional relay fallback.
- Client Application: Local API server, Web UI, and orchestration of control plane and data plane.
- Relay Nodes: Stateless forwarders for NAT traversal.

```mermaid
graph TB
subgraph "Client"
CP["ControlPlane / RemoteControlPlaneClient"]
WG["WireGuard Interface"]
NAT["NAT Traversal"]
end
subgraph "Control Plane"
DB["SQLite (aiosqlite)"]
API["FastAPI Control Server"]
end
subgraph "Relay"
RS["Relay Server"]
end
CP --> API
API --> DB
NAT --> WG
WG --> RS
RS --> WG
```

**Diagram sources**
- [servers/control_server.py](file://servers/control_server.py#L1-L729)
- [core/control_client.py](file://core/control_client.py#L23-L438)
- [core/network.py](file://core/network.py#L25-L515)
- [core/nat.py](file://core/nat.py#L41-L525)
- [servers/relay_server.py](file://servers/relay_server.py#L1-L297)

## Detailed Component Analysis

### Control Plane: Peer Discovery, Registration, and State Persistence
- Data models:
  - PeerInfo: Peer identity, keys, NAT info, and timestamps.
  - PartyInfo: Party metadata and member registry.
- ControlPlane:
  - Registers/joins/leaves parties.
  - Updates peer info and heartbeats.
  - Periodic cleanup of stale peers and parties.
  - Batched state persistence to disk with deduplicated writes.
- LocalControlPlane:
  - Announces parties to a shared discovery file for local LAN discovery.
- RemoteControlPlane:
  - HTTP client to control server with retry/backoff and heartbeat.
  - WebSocket connection (planned) for live updates.

```mermaid
classDiagram
class ControlPlane {
+initialize()
+shutdown()
+register_party(party_id, name, host_peer_info)
+join_party(party_id, peer_info)
+leave_party(party_id, peer_id)
+update_peer(party_id, peer_info)
+get_party(party_id)
+get_peers(party_id)
+discover_peer(party_id, peer_id)
+heartbeat(party_id, peer_id)
-_cleanup_task()
-_save_state()
-_load_state()
}
class LocalControlPlane {
+_announce_party(party)
+discover_parties()
}
class RemoteControlPlane {
+_connect()
+_authenticate()
+_handle_messages()
+_reconnect()
+close()
}
class PeerInfo {
+to_dict()
+from_dict(data)
+validate_nat_type()
+get_nat_type_enum()
}
class PartyInfo {
+to_dict()
+from_dict(data)
+generate_party_id()
}
ControlPlane <|-- LocalControlPlane
ControlPlane <|-- RemoteControlPlane
ControlPlane --> PartyInfo
PartyInfo --> PeerInfo
```

**Diagram sources**
- [core/control.py](file://core/control.py#L115-L880)

**Section sources**
- [core/control.py](file://core/control.py#L187-L880)
- [docs/CONTROL_PLANE.md](file://docs/CONTROL_PLANE.md#L1-L629)

### Remote Control Plane Client: HTTP Coordination
- Async HTTP client with:
  - Automatic retry/backoff.
  - Connection pooling and timeouts.
  - Heartbeat management.
- Operations:
  - Register peer and obtain token.
  - Create/join parties.
  - Discover peers and parties.
  - Heartbeat and graceful leave.

```mermaid
sequenceDiagram
participant Client as "RemoteControlPlaneClient"
participant API as "Control Server"
participant DB as "SQLite"
Client->>API : POST /auth/register
API->>DB : Store token
DB-->>API : OK
API-->>Client : {token, peer_id}
Client->>API : POST /parties
API->>DB : Insert party + host peer
DB-->>API : OK
API-->>Client : {party_id, party}
Client->>API : GET /parties/{party_id}/peers
API->>DB : SELECT peers
DB-->>API : rows
API-->>Client : {peers}
Client->>API : POST /parties/{party_id}/peers/{peer_id}/heartbeat
API->>DB : UPDATE last_seen
DB-->>API : OK
API-->>Client : {status : ok}
```

**Diagram sources**
- [core/control_client.py](file://core/control_client.py#L161-L438)
- [servers/control_server.py](file://servers/control_server.py#L267-L594)

**Section sources**
- [core/control_client.py](file://core/control_client.py#L23-L438)
- [servers/control_server.py](file://servers/control_server.py#L267-L594)

### Control Plane Server: Centralized Registry and Authentication
- Endpoints:
  - Authentication: register peer and issue token.
  - Party management: create, join, leave, list peers, discover peer.
  - Heartbeat: keep peer alive.
  - Relay registry: register and list relays.
- Database schema:
  - parties, peers, relay_servers, auth_tokens.
- Background cleanup:
  - Removes stale peers, empty parties, expired tokens, and stale relays.

```mermaid
flowchart TD
Start([Startup]) --> InitDB["Init database schema"]
InitDB --> StartCleanup["Start cleanup task"]
StartCleanup --> Listen["Start FastAPI server"]
subgraph "Endpoints"
Auth["POST /auth/register"]
CreateParty["POST /parties"]
JoinParty["POST /parties/{party_id}/join"]
LeaveParty["DELETE /parties/{party_id}/peers/{peer_id}"]
GetParty["GET /parties/{party_id}"]
GetPeers["GET /parties/{party_id}/peers"]
DiscoverPeer["GET /parties/{party_id}/peers/{peer_id}"]
Heartbeat["POST /parties/{party_id}/peers/{peer_id}/heartbeat"]
RegisterRelay["POST /relays"]
ListRelays["GET /relays"]
end
Listen --> Auth
Listen --> CreateParty
Listen --> JoinParty
Listen --> LeaveParty
Listen --> GetParty
Listen --> GetPeers
Listen --> DiscoverPeer
Listen --> Heartbeat
Listen --> RegisterRelay
Listen --> ListRelays
```

**Diagram sources**
- [servers/control_server.py](file://servers/control_server.py#L36-L213)
- [servers/control_server.py](file://servers/control_server.py#L267-L729)

**Section sources**
- [servers/control_server.py](file://servers/control_server.py#L1-L729)

### Relay Server: Stateless Packet Forwarder
- Stateless forwarding of encrypted WireGuard packets.
- Automatic cleanup of stale clients.
- Statistics tracking and periodic reporting.
- Optional rate limiting and blocked IP tracking.

```mermaid
sequenceDiagram
participant PeerA as "Peer A"
participant Relay as "RelayServer"
participant PeerB as "Peer B"
PeerA->>Relay : UDP packet (encrypted)
Relay->>Relay : Update client record
Relay->>PeerB : Forward packet
PeerB->>Relay : UDP packet (encrypted)
Relay->>Relay : Update client record
Relay->>PeerA : Forward packet
```

**Diagram sources**
- [servers/relay_server.py](file://servers/relay_server.py#L85-L255)

**Section sources**
- [servers/relay_server.py](file://servers/relay_server.py#L1-L297)
- [docs/RELAY_SERVER.md](file://docs/RELAY_SERVER.md#L1-L544)

### Key Exchange and Session Management
- WireGuard key exchange:
  - NetworkManager generates X25519 keypairs and manages WireGuard interface.
- NAT traversal:
  - NATTraversal detects NAT type via STUN and attempts UDP hole punching.
  - ConnectionCoordinator selects direct or relay strategy and discovers relays.
- Session coordination:
  - Control plane stores peer public keys and NAT info.
  - Clients coordinate endpoints and persist keys for future sessions.

```mermaid
flowchart TD
GenKeys["Generate WireGuard keys"] --> AddPeer["Add peer to WireGuard interface"]
AddPeer --> NATDet["NAT detection (STUN)"]
NATDet --> Strategy{"Direct or Relay?"}
Strategy --> |Direct| Punch["UDP hole punch"]
Strategy --> |Relay| Discover["Discover relay(s)"]
Punch --> Success{"Success?"}
Success --> |Yes| Connect["Establish P2P"]
Success --> |No| Discover
Discover --> ConnectRelay["Connect via relay"]
```

**Diagram sources**
- [core/network.py](file://core/network.py#L123-L160)
- [core/nat.py](file://core/nat.py#L64-L106)
- [core/nat.py](file://core/nat.py#L244-L294)
- [core/nat.py](file://core/nat.py#L330-L455)

**Section sources**
- [core/network.py](file://core/network.py#L25-L515)
- [core/nat.py](file://core/nat.py#L41-L525)

### Database Integration: Persistent Configuration and State
- SettingsDatabase:
  - Typed settings storage with JSON serialization for complex values.
  - Server configurations, favorites, and game profiles.
- Control Plane Database:
  - Parties, peers, relay servers, and auth tokens.
  - Indexes for efficient queries.
- Initialization and migrations:
  - Schema creation on first run.
  - Cleanup tasks for stale entries.

```mermaid
erDiagram
SETTINGS {
text key PK
text value
text type
text updated_at
}
SERVER_CONFIGS {
integer id PK
text name
text mode
integer enabled
text config
text created_at
text updated_at
}
FAVORITE_SERVERS {
text server_id PK
text name
text game
text address
text added_at
}
GAME_PROFILES {
integer id PK
text name UK
text game
text profile
text created_at
text updated_at
}
PARTIES {
text party_id PK
text name
text host_id
text created_at
text updated_at
}
PEERS {
text peer_id PK
text party_id FK
text public_key
text virtual_ip
text public_endpoint
text nat_type
text last_seen
}
RELAY_SERVERS {
text relay_id PK
text public_ip
integer port
text region
integer capacity
text registered_at
text last_seen
}
AUTH_TOKENS {
text token PK
text peer_id
text created_at
text expires_at
}
PARTIES ||--o{ PEERS : "members"
```

**Diagram sources**
- [core/settings.py](file://core/settings.py#L42-L95)
- [servers/control_server.py](file://servers/control_server.py#L40-L98)

**Section sources**
- [core/settings.py](file://core/settings.py#L20-L525)
- [servers/control_server.py](file://servers/control_server.py#L36-L98)

## Dependency Analysis
- ControlPlane depends on:
  - Config for paths and settings.
  - StatePersister for batched persistence.
  - PeerInfo/PartyInfo for data modeling.
- RemoteControlPlaneClient depends on:
  - httpx for async HTTP.
  - ControlPlaneError for error handling.
- Control Server depends on:
  - aiosqlite for async DB operations.
  - Pydantic models for request/response validation.
- Relay Server depends on:
  - asyncio for UDP handling.
  - Config for runtime settings.

```mermaid
graph LR
ControlPlane --> Config
ControlPlane --> StatePersister
ControlPlane --> PeerInfo
ControlPlane --> PartyInfo
RemoteControlPlaneClient --> Config
RemoteControlPlaneClient --> ControlPlaneError
ControlServer --> aiosqlite
ControlServer --> Pydantic
RelayServer --> Config
RelayServer --> asyncio
```

**Diagram sources**
- [core/control.py](file://core/control.py#L187-L210)
- [core/control_client.py](file://core/control_client.py#L35-L46)
- [servers/control_server.py](file://servers/control_server.py#L20-L30)
- [servers/relay_server.py](file://servers/relay_server.py#L16-L18)

**Section sources**
- [core/control.py](file://core/control.py#L187-L210)
- [core/control_client.py](file://core/control_client.py#L35-L46)
- [servers/control_server.py](file://servers/control_server.py#L20-L30)
- [servers/relay_server.py](file://servers/relay_server.py#L16-L18)

## Performance Considerations
- Control Plane:
  - Batched state writes reduce disk I/O.
  - Cleanup runs periodically to prune stale entries.
- Relay Server:
  - Stateless forwarding with minimal CPU/memory overhead.
  - UDP buffer tuning and kernel parameters improve throughput.
- NAT Traversal:
  - STUN reduces connection setup latency.
  - Hole punching avoids unnecessary relay usage.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Control Plane Client:
  - Timeouts and connection failures are retried with exponential backoff.
  - Heartbeat keeps peers alive; failures are logged but do not crash the client.
- Control Server:
  - Health endpoint reports counts of parties and relays.
  - Cleanup removes stale peers and expired tokens.
- Relay Server:
  - Stale client cleanup prevents resource leaks.
  - Stats printed periodically aid monitoring.
- NAT Traversal:
  - STUN failures indicate network restrictions; fall back to relay.
  - Hole punching failures suggest symmetric NAT requiring relay.

**Section sources**
- [core/control_client.py](file://core/control_client.py#L75-L160)
- [servers/control_server.py](file://servers/control_server.py#L244-L263)
- [servers/relay_server.py](file://servers/relay_server.py#L189-L222)
- [core/nat.py](file://core/nat.py#L64-L106)

## Conclusion
LANrage’s control plane provides a robust, database-backed foundation for peer discovery, session coordination, and relay management. The separation of concerns between control and data planes, combined with NAT traversal and relay fallback, ensures reliable connectivity across diverse network environments. The documented architecture, APIs, and deployment guidance enable scalable and secure operations.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Deployment Guidelines
- Control Plane Server:
  - Run with FastAPI/Uvicorn; ensure SQLite file location is writable.
  - Configure API host/port via settings database.
- Relay Server:
  - Expose UDP port 51820; tune kernel buffers for throughput.
  - Use systemd or Docker for production deployments.
- Client:
  - Configure settings via Web UI; restart to apply changes.
- Environment:
  - Legacy .env is deprecated; all settings are stored in the settings database.

**Section sources**
- [servers/control_server.py](file://servers/control_server.py#L685-L729)
- [servers/relay_server.py](file://servers/relay_server.py#L258-L297)
- [.env.example](file://.env.example#L1-L36)
- [docs/RELAY_SERVER.md](file://docs/RELAY_SERVER.md#L236-L302)