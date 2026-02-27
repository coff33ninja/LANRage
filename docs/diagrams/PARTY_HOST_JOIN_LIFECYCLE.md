# Party Host/Join Lifecycle

Host and joiner orchestration flow at party manager layer.

```mermaid
sequenceDiagram
participant Host as Host Client
participant Joiner as Joiner Client
participant PM as PartyManager
participant CP as ControlPlane
participant CM as ConnectionManager

Host->>PM: create_party(name)
PM->>CP: register_party(host peer info)
CP-->>PM: party state
PM-->>Host: party created

Joiner->>PM: join_party(party_id, peer_name)
PM->>PM: lazy init NAT/control if needed
PM->>CP: join_party(joiner peer info)
CP-->>PM: party + peer list
PM->>CM: connect_to_peer(...) for existing peers
PM-->>Joiner: joined party state

Host->>PM: leave_party()
Joiner->>PM: leave_party()
PM->>CP: leave_party(...)
```

Related docs:
- [Party Management](/docs/core/control_plane/PARTY.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
