# LANrage Docs Hub

Canonical, maintained documentation for LANrage.

## Start Here

- [Quick Start](QUICKSTART.md): Fast path from clone to first party.
- [User Guide](USER_GUIDE.md): End-user workflows and UI usage.
- [Troubleshooting](TROUBLESHOOTING.md): Common failures and fixes.
- [Deep Dive](DEEP_DIVE.md): End-to-end technical behavior and design rationale.

## By Audience

### Players / Hosts

- [Quick Start](QUICKSTART.md)
- [User Guide](USER_GUIDE.md)
- [Supported Games](SUPPORTED_GAMES.md)
- [Discord Setup Guide](DISCORD_SETUP_GUIDE.md)
- [Server Browser](/docs/core/gameplay/SERVER_BROWSER.md)

### Operators

- [Production Ready Checklist](PRODUCTION_READY.md)
- [Startup Validation](STARTUP_VALIDATION.md)
- [CI/CD](CI_CD.md)
- [Relay Server](/docs/servers/RELAY_SERVER.md)
- [WireGuard Setup](WIREGUARD_SETUP.md)

### Contributors

- [Architecture](ARCHITECTURE.md)
- [API Reference](API.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [Testing](TESTING.md)
- [Performance Profiling](/docs/core/observability/PERFORMANCE_PROFILING.md)
- [Contributing](../CONTRIBUTING.md)

## System Areas

- Networking and tunnel lifecycle: [NETWORK.md](/docs/core/networking/NETWORK.md)
- Connection orchestration: [CONNECTION.md](/docs/core/networking/CONNECTION.md)
- Party lifecycle: [PARTY.md](/docs/core/control_plane/PARTY.md)
- Broadcast emulation: [BROADCAST.md](/docs/core/gameplay/BROADCAST.md)
- Metrics and dashboards: [METRICS.md](/docs/core/observability/METRICS.md)
- Discord integration: [DISCORD.md](/docs/core/integrations/DISCORD.md)
- Game detection and profiles: [GAMES.md](/docs/core/gameplay/GAMES.md)

## Folder Layout

- `docs/core/networking/`:
  - [Network](/docs/core/networking/NETWORK.md)
  - [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
  - [Connection](/docs/core/networking/CONNECTION.md)
- `docs/core/control_plane/`:
  - [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
  - [Party](/docs/core/control_plane/PARTY.md)
  - [Settings](/docs/core/control_plane/SETTINGS.md)
- `docs/core/integrations/`:
  - [Discord](/docs/core/integrations/DISCORD.md)
- `docs/core/observability/`:
  - [Metrics](/docs/core/observability/METRICS.md)
  - [Performance Profiling](/docs/core/observability/PERFORMANCE_PROFILING.md)
- `docs/core/gameplay/`:
  - [Games](/docs/core/gameplay/GAMES.md)
  - [Server Browser](/docs/core/gameplay/SERVER_BROWSER.md)
  - [Broadcast](/docs/core/gameplay/BROADCAST.md)
- `docs/servers/`:
  - [Control Plane Server](/docs/servers/CONTROL_PLANE_SERVER.md)
  - [Relay Server](/docs/servers/RELAY_SERVER.md)

## Architecture and Flows

- High-level architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Control/data-plane details: [DEEP_DIVE.md](DEEP_DIVE.md)
- Runtime diagrams: [diagrams/README.md](diagrams/README.md)

## Project Status and Planning

- Current progress snapshot: [Session Progress](project/SESSION_PROGRESS.md)
- Forward roadmap: [Roadmap](project/ROADMAP.md)
- Delivery/parity tracker: [Doc Parity Tracker](project/DOC_PARITY_TRACKER.md)
- Implementation backlog/history: [Implementation Plan](project/IMPLEMENTATION_PLAN.md)
- Improvement archive: [Improvements](project/IMPROVEMENTS.md)
- Remaining-item ledger: [What's Missing](project/WHATS_MISSING.md)
- Root/documentation structure policy: [Root Layout](project/ROOT_LAYOUT.md)
- Versioning and release policy: [VERSIONING.md](VERSIONING.md)

## Code Layout Alignment

- Canonical networking modules are in `core/networking/`.
- Canonical imports are required across `core/networking/`, `core/control_plane/`, `core/integrations/`, `core/observability/`, and `core/gameplay/`.

## Source of Truth Policy

- `docs/` is canonical for project documentation.
- Documentation was expanded using external research inputs, then normalized into canonical docs.
- Canonical docs are authoritative for current behavior.

## Doc Maintenance Rules

- Keep audience-first navigation in this file.
- Prefer links to canonical docs over duplicating long explanations.
- If adding a new major subsystem doc, link it in both `README.md` (root) and this hub.
