# Signal Queue/Poll Sequence

Queued signaling delivery flow used by control-plane peers.

```mermaid
sequenceDiagram
participant A as Sender Peer
participant CP as ControlPlane
participant B as Target Peer

A->>CP: signal_connection(party_id, from=A, to=B, signal_data)
CP->>CP: enqueue envelope in pending_signals[B]

Note over B,CP: B polls periodically

B->>CP: poll_signals(party_id, B)
CP-->>B: queued envelopes for B
CP->>CP: clear pending_signals[B]

B->>B: process signaling payloads
```

Semantics:
- Queue is keyed by target peer ID.
- Poll returns all queued items for the target peer.
- Poll clears returned queue entries.

Related docs:
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)
