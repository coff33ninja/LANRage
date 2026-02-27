# NAT Strategy Decision Tree

Decision path from NAT compatibility to direct or relay endpoint.

```mermaid
flowchart TD
A[Start coordinate_connection] --> B[Read peer NAT info]
B --> C{can_direct_connect(peer_nat_type)}
C -->|Yes| D[Attempt UDP hole punch]
D --> E{Hole punch success}
E -->|Yes| F[Use direct peer endpoint]
E -->|No| G[Discover/select relay endpoint]
C -->|No| G
G --> H[Use relay endpoint]
F --> I[Return strategy + endpoint]
H --> I
```

Related docs:
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Connection Management](/docs/core/networking/CONNECTION.md)
