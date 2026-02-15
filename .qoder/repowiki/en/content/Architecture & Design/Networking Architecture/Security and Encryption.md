# Security and Encryption

<cite>
**Referenced Files in This Document**
- [SECURITY.md](file://SECURITY.md)
- [README.md](file://README.md)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md)
- [docs/NETWORK.md](file://docs/NETWORK.md)
- [core/network.py](file://core/network.py)
- [core/connection.py](file://core/connection.py)
- [core/nat.py](file://core/nat.py)
- [core/control.py](file://core/control.py)
- [core/config.py](file://core/config.py)
- [servers/relay_server.py](file://servers/relay_server.py)
- [tests/test_wireguard.py](file://tests/test_wireguard.py)
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
This document explains LANrage’s security implementation using WireGuard’s cryptographic primitives. It covers how the system achieves confidentiality and integrity with ChaCha20-Poly1305 authenticated encryption, forward secrecy via X25519 key exchange, and a peer-to-peer trust model that eliminates the need for certificate authorities. It also documents key management, ephemeral key handling, session key derivation, replay attack protection, and the security implications of the mesh topology and peer verification mechanisms in distributed gaming scenarios.

## Project Structure
LANrage integrates WireGuard at the network layer and orchestrates peer connections with NAT traversal and relay fallback. The security-critical components are:
- WireGuard interface management and key handling
- NAT traversal and connection coordination
- Control plane for peer discovery and signaling
- Relay server for encrypted packet forwarding

```mermaid
graph TB
subgraph "Client Node"
NM["NetworkManager<br/>core/network.py"]
CONN["ConnectionManager<br/>core/connection.py"]
NAT["NATTraversal<br/>core/nat.py"]
CTRL["ControlPlane<br/>core/control.py"]
end
subgraph "Relay Node"
RS["RelayServer<br/>servers/relay_server.py"]
end
NM --> CONN
CONN --> NAT
CONN --> CTRL
CONN --> RS
```

**Diagram sources**
- [core/network.py](file://core/network.py#L25-L515)
- [core/connection.py](file://core/connection.py#L18-L493)
- [core/nat.py](file://core/nat.py#L41-L525)
- [core/control.py](file://core/control.py#L187-L880)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L297)

**Section sources**
- [README.md](file://README.md#L93-L108)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L1-L279)
- [docs/NETWORK.md](file://docs/NETWORK.md#L1-L453)

## Core Components
- WireGuard interface management with automatic key generation and base64 encoding for configuration
- Peer-to-peer trust model using public key authentication and cryptographic identity
- ChaCha20-Poly1305 authenticated encryption providing confidentiality and integrity
- X25519 key exchange ensuring forward secrecy and perfect forward security
- Persistent keepalive for NAT traversal and session liveness
- Relay server forwarding encrypted packets without decryption

**Section sources**
- [core/network.py](file://core/network.py#L123-L160)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L225-L247)
- [docs/NETWORK.md](file://docs/NETWORK.md#L351-L372)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L138)

## Architecture Overview
The system builds a secure mesh of peers:
- Each peer generates Curve25519 keys and shares only public keys
- Peers authenticate each other using public keys and WireGuard’s cryptographic handshake
- Traffic is encrypted end-to-end; relays forward only UDP packets without inspecting payload
- NAT traversal uses STUN and UDP hole punching; fallback routes via relays

```mermaid
sequenceDiagram
participant A as "Peer A<br/>NetworkManager"
participant CTRL as "ControlPlane<br/>core/control.py"
participant B as "Peer B<br/>NetworkManager"
participant RELAY as "RelayServer<br/>servers/relay_server.py"
A->>CTRL : "Discover peer public key"
CTRL-->>A : "Peer public key + NAT info"
A->>B : "Initiate WireGuard handshake"
Note over A,B : "ChaCha20-Poly1305 encryption<br/>X25519 key exchange<br/>Forward secrecy"
A->>RELAY : "If direct P2P fails, forward encrypted packets"
RELAY-->>B : "Forward encrypted packets"
B-->>A : "Encrypted response"
```

**Diagram sources**
- [core/control.py](file://core/control.py#L331-L346)
- [core/network.py](file://core/network.py#L392-L420)
- [servers/relay_server.py](file://servers/relay_server.py#L85-L138)

**Section sources**
- [core/nat.py](file://core/nat.py#L244-L294)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L234-L247)

## Detailed Component Analysis

### WireGuard Encryption and Forward Secrecy
- ChaCha20-Poly1305 provides authenticated encryption with 256-bit keys and Poly1305 MAC for integrity
- X25519 key exchange ensures forward secrecy: new session keys are derived per handshake
- Persistent keepalive (25 seconds) maintains NAT bindings and session liveness

```mermaid
flowchart TD
Start(["Handshake Initiation"]) --> Derive["Derive shared secret via X25519"]
Derive --> HKDF["HKDF-based session key derivation"]
HKDF --> AEAD["Encrypt payload with ChaCha20-Poly1305"]
AEAD --> Send["Send encrypted packet"]
Recv["Receive encrypted packet"] --> Verify["Verify Poly1305 tag"]
Verify --> Decrypt["Decrypt with ChaCha20 stream"]
Decrypt --> End(["Authenticated plaintext"])
```

**Diagram sources**
- [docs/NETWORK.md](file://docs/NETWORK.md#L351-L372)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L234-L247)

**Section sources**
- [docs/NETWORK.md](file://docs/NETWORK.md#L351-L372)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L234-L247)

### Peer-to-Peer Trust Model and Identity
- Peers are identified by public keys; no passwords or tokens are used
- Public keys are shared via the control plane; private keys are stored securely on disk
- Man-in-the-middle resistance comes from cryptographic authentication and public key pinning

```mermaid
classDiagram
class ControlPlane {
+register_party()
+join_party()
+discover_peer()
+heartbeat()
}
class PeerInfo {
+string peer_id
+string public_key
+string nat_type
+string public_ip
+int public_port
+string local_ip
+int local_port
}
ControlPlane --> PeerInfo : "stores and shares"
```

**Diagram sources**
- [core/control.py](file://core/control.py#L115-L152)
- [core/control.py](file://core/control.py#L187-L457)

**Section sources**
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L241-L247)
- [core/control.py](file://core/control.py#L331-L346)

### Key Management: Generation, Encoding, and Storage
- Curve25519 keys generated cryptographically securely and saved to the user’s home directory
- Private key permissions restricted (0600 on Unix); public key safe to share
- Keys are base64-encoded for configuration and passed to WireGuard tools

```mermaid
flowchart TD
Gen["Generate Curve25519 keypair"] --> Save["Write raw keys to ~/.lanrage/keys/"]
Save --> Perm["Set 0600 permissions (Unix)"]
Perm --> Encode["Base64 encode keys"]
Encode --> WG["Pass to WireGuard interface"]
```

**Diagram sources**
- [core/network.py](file://core/network.py#L123-L160)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L119-L122)

**Section sources**
- [core/network.py](file://core/network.py#L123-L160)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L227-L233)

### Ephemeral Keys, Session Derivation, and Replay Protection
- Each handshake derives fresh session keys; previous session keys become invalid after rekeying
- WireGuard’s anti-replay window prevents replay attacks across sessions
- Persistent keepalive helps maintain session liveness and detects connectivity issues

```mermaid
sequenceDiagram
participant A as "Peer A"
participant B as "Peer B"
A->>B : "Handshake Initiation (ephemeral ECDH)"
B-->>A : "Handshake Response"
A-->>B : "Cookie/Challenge verification"
A->>B : "Encrypted Data (session key)"
Note over A,B : "Anti-replay protects against replays"
```

**Diagram sources**
- [docs/NETWORK.md](file://docs/NETWORK.md#L366-L372)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L234-L240)

**Section sources**
- [docs/NETWORK.md](file://docs/NETWORK.md#L366-L372)
- [core/network.py](file://core/network.py#L411-L414)

### Mesh Topology and Peer Verification
- Mesh enables direct P2P when possible; otherwise uses relays
- Peer verification relies on public key authentication; peers must exchange public keys via the control plane
- Relay visibility is limited to encrypted packets; relays cannot decrypt payloads

```mermaid
graph TB
A["Peer A"] -- "Direct/Relayed" --> B["Peer B"]
A -- "Direct/Relayed" --> C["Peer C"]
B -- "Direct/Relayed" --> C
R["Relay"] -. "Forwards UDP only" .- A
R -. "Forwards UDP only" .- B
R -. "Forwards UDP only" .- C
```

**Diagram sources**
- [core/connection.py](file://core/connection.py#L38-L125)
- [servers/relay_server.py](file://servers/relay_server.py#L85-L138)

**Section sources**
- [core/connection.py](file://core/connection.py#L38-L125)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L138)

### NAT Traversal and Relay Fallback
- STUN is used to detect NAT type and determine connectivity
- UDP hole punching attempts direct P2P; if unsuccessful, relay fallback is used
- Relay endpoints are discovered and latency measured to select optimal relays

```mermaid
flowchart TD
Detect["Detect NAT type via STUN"] --> CanDirect{"Can connect directly?"}
CanDirect --> |Yes| Punch["Attempt UDP hole punch"]
CanDirect --> |No| Relay["Select best relay"]
punch --> Success{"Direct connection?"}
Success --> |Yes| Connect["Configure WireGuard peer"]
Success --> |No| Relay
Relay --> Connect
```

**Diagram sources**
- [core/nat.py](file://core/nat.py#L64-L106)
- [core/nat.py](file://core/nat.py#L244-L294)
- [core/nat.py](file://core/nat.py#L379-L398)

**Section sources**
- [core/nat.py](file://core/nat.py#L64-L106)
- [core/nat.py](file://core/nat.py#L379-L398)

### Control Plane and Signaling
- Local control plane stores and shares peer information; remote control plane is planned for v1.1
- Heartbeats keep peers alive; stale entries are cleaned up
- Signal messages facilitate NAT coordination (placeholder for future WebRTC-style signaling)

**Section sources**
- [core/control.py](file://core/control.py#L209-L227)
- [core/control.py](file://core/control.py#L362-L377)
- [core/control.py](file://core/control.py#L347-L361)

## Dependency Analysis
WireGuard security depends on correct integration of:
- NetworkManager for key generation, base64 encoding, and wg interface configuration
- ConnectionManager for peer orchestration and WireGuard peer updates
- NATTraversal for connectivity strategy and relay selection
- ControlPlane for peer discovery and signaling
- RelayServer for encrypted packet forwarding

```mermaid
graph LR
CFG["Config<br/>core/config.py"] --> NM["NetworkManager<br/>core/network.py"]
NM --> CONN["ConnectionManager<br/>core/connection.py"]
CONN --> NAT["NATTraversal<br/>core/nat.py"]
CONN --> CTRL["ControlPlane<br/>core/control.py"]
CONN --> RS["RelayServer<br/>servers/relay_server.py"]
```

**Diagram sources**
- [core/config.py](file://core/config.py#L17-L114)
- [core/network.py](file://core/network.py#L25-L515)
- [core/connection.py](file://core/connection.py#L18-L493)
- [core/nat.py](file://core/nat.py#L41-L525)
- [core/control.py](file://core/control.py#L187-L880)
- [servers/relay_server.py](file://servers/relay_server.py#L30-L297)

**Section sources**
- [core/config.py](file://core/config.py#L46-L47)
- [core/network.py](file://core/network.py#L28-L37)
- [core/connection.py](file://core/connection.py#L21-L33)

## Performance Considerations
- WireGuard overhead is minimal (~100 bytes per packet) with hardware-accelerated crypto
- Persistent keepalive (25 seconds) balances NAT traversal reliability with minimal overhead
- Relay selection uses latency measurements to minimize round-trip delays

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common security-related issues and mitigations:
- WireGuard not found or permission denied: ensure proper installation and elevated privileges
- Interface creation failures: verify kernel modules, port availability, and configuration
- Peer unreachable: confirm endpoints, firewall rules, and NAT traversal status
- Relay visibility: expect encrypted traffic metadata visibility; use trusted relays

**Section sources**
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L166-L224)
- [docs/NETWORK.md](file://docs/NETWORK.md#L373-L410)

## Conclusion
LANrage’s security model leverages WireGuard’s ChaCha20-Poly1305 authenticated encryption and X25519 key exchange to deliver confidentiality, integrity, and forward secrecy. The peer-to-peer trust model, based on public key authentication, eliminates the need for certificates or central PKI. The mesh topology, combined with NAT traversal and relay fallback, ensures resilient connectivity for gaming scenarios. While ephemeral key rotation is noted as future work, the existing implementation provides strong cryptographic protections suitable for personal and small-group gaming use.