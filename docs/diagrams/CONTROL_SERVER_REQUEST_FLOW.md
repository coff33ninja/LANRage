# Control Server Request Flow

Request/authorization/persistence flow for protected control-plane endpoints.

```mermaid
flowchart TD
A[Incoming HTTP Request] --> B{Protected endpoint?}
B -->|No| Z[Handle public response]
B -->|Yes| C[Parse Authorization Bearer token]
C --> D{Token valid and unexpired?}
D -->|No| E[Return 401]
D -->|Yes| F[Validate path/body identity invariants]
F --> G{Request valid?}
G -->|No| H[Return 4xx]
G -->|Yes| I[Execute DB operation]
I --> J[Return JSON response]
```

Related docs:
- [Control Plane Server](/docs/servers/CONTROL_PLANE_SERVER.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
