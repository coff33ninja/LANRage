# Startup Sequence

This diagram captures the initialization and shutdown sequence used by `lanrage.py`.

```mermaid
sequenceDiagram
participant Main as lanrage.py
participant Settings as settings/config
participant Net as NetworkManager
participant Party as PartyManager
participant Control as ControlPlane
participant NAT as NATTraversal
participant Metrics as MetricsCollector
participant Integrations as Discord/ServerBrowser
participant API as FastAPI

Main->>Settings: initialize settings + load config
Main->>Net: initialize network prerequisites
Main->>NAT: detect_nat()
Main->>Control: initialize control mode
Main->>Party: wire managers and connection orchestration
Main->>Metrics: start collection loop
Main->>Integrations: start optional services
Main->>API: start HTTP server + UI endpoints

Note over API,Main: Runtime steady state

Main->>API: stop accepting new work
Main->>Integrations: stop and flush
Main->>Metrics: stop collection
Main->>Party: disconnect peers and leave session
Main->>Net: cleanup interface state
Main->>Main: shutdown complete
```

Related docs:
- [Architecture](../ARCHITECTURE.md)
- [System Flow Overview](SYSTEM_FLOW.md)
- [Runtime Control Loops](RUNTIME_CONTROL_LOOPS.md)
