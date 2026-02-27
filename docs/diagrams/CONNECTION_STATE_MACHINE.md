# Connection State Machine

Lifecycle transitions for a peer connection record.

```mermaid
stateDiagram-v2
[*] --> Connecting

Connecting --> Connected: strategy resolved + peer configured
Connecting --> Failed: setup failure

Connected --> Degraded: high latency or intermittent probe failure
Connected --> Failed: repeated probe failure
Connected --> Disconnected: explicit disconnect

Degraded --> Connected: latency recovers
Degraded --> Failed: remediation fails
Degraded --> Connected: successful relay switch/reconnect

Failed --> Disconnected: cleanup path
Disconnected --> [*]
```

Related docs:
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
