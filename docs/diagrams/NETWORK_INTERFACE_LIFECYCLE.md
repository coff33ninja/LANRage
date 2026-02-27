# Network Interface Lifecycle

Platform-specific WireGuard interface lifecycle.

```mermaid
flowchart TD
A[initialize()] --> B[check WireGuard availability]
B --> C[ensure keys exist]
C --> D{platform}
D -->|Windows| E[generate .conf and install/reuse tunnel service]
D -->|Linux| F[create wireguard interface and configure key/address/MTU]
E --> G[interface_created=true]
F --> G
G --> H[peer add/remove operations]
H --> I[measure latency / report status]
I --> J[cleanup()]
J --> K{platform}
K -->|Windows| L[uninstall tunnel service]
K -->|Linux| M[delete interface]
L --> N[interface_created=false]
M --> N
```

Related docs:
- [Network Layer](/docs/core/networking/NETWORK.md)
- [WireGuard Setup](../WIREGUARD_SETUP.md)
