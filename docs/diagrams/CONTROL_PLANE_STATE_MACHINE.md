# Control Plane State Machine

Party and peer lifecycle transitions in the control plane.

```mermaid
stateDiagram-v2
[*] --> Idle

Idle --> PartyRegistered: register_party(host)
PartyRegistered --> Active: host heartbeat ok

Active --> Active: update_peer / heartbeat
Active --> Active: join_party(peer)
Active --> PeerRemoved: leave_party(peer)
Active --> CleanupCheck: cleanup tick

PeerRemoved --> Active: peers remain
PeerRemoved --> PartyRemoved: host left or no peers

CleanupCheck --> Active: no stale peers
CleanupCheck --> PeerRemoved: stale peers removed
CleanupCheck --> PartyRemoved: party becomes empty

PartyRemoved --> Idle
```

Related docs:
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Party](/docs/core/control_plane/PARTY.md)
