[Diagram Pack Index](README.md)

# LANrage System Flow Diagrams

This document is the detailed visual map of how LANrage works end-to-end.

## 1. System Context

```mermaid
flowchart LR
    USER["Player / Host"]
    CLIENT["LANrage Client App\n(FastAPI + Web UI + Core services)"]
    CONTROL["Control Plane Server\nservers/control_server.py"]
    RELAY["Relay Server\nservers/relay_server.py"]
    DISCORD["Discord API"]
    GAME["LAN Game Process"]

    USER --> CLIENT
    CLIENT <--> CONTROL
    CLIENT <--> RELAY
    CLIENT <--> DISCORD
    CLIENT <--> GAME
```

## 2. Client Internal Components

```mermaid
flowchart TB
    subgraph UI["Presentation Layer"]
        WEB["Web UI"]
        API["FastAPI Endpoints\napi/server.py"]
    end

    subgraph APP["Application Layer"]
        PARTY["Party Manager\ncore/party.py"]
        CONN["Connection Manager\ncore/connection.py"]
        CONTROL_CLIENT["Control Client\ncore/control_client.py"]
        TASKS["Task Manager\ncore/task_manager.py"]
        LOCKS["Operation Lock / Conflict Resolver\ncore/operation_lock.py + core/conflict_resolver.py"]
    end

    subgraph NET["Networking Layer"]
        NETMGR["Network Manager\ncore/network.py"]
        NAT["NAT Traversal\ncore/nat.py"]
        RELSEL["Relay Selector\ncore/relay_selector.py"]
        BCAST["Broadcast Emulator\ncore/broadcast.py"]
    end

    subgraph GAMEFEAT["Game Services"]
        GAMES["Game Detector/Profile Manager\ncore/games.py"]
        MODSYNC["Mod Sync Planner\ncore/mod_sync.py"]
        BROWSER["Server Browser\ncore/server_browser.py"]
        DISCORD_INT["Discord Integration\ncore/discord_integration.py"]
    end

    subgraph DATA["Persistence + Observability"]
        SETTINGS["Settings Store\ncore/settings.py (SQLite)"]
        METRICS["Metrics\ncore/metrics.py"]
        LOGS["Structured Logging\ncore/logging_config.py"]
    end

    WEB --> API
    API --> PARTY
    API --> SETTINGS

    PARTY --> CONN
    PARTY --> CONTROL_CLIENT
    PARTY --> TASKS
    PARTY --> LOCKS

    CONN --> NETMGR
    CONN --> NAT
    NAT --> RELSEL

    NETMGR --> BCAST
    CONN --> GAMES
    GAMES --> MODSYNC
    PARTY --> BROWSER
    PARTY --> DISCORD_INT

    CONN --> METRICS
    NETMGR --> METRICS
    PARTY --> METRICS

    API --> LOGS
    PARTY --> LOGS
    CONN --> LOGS
```

## 3. End-to-End Data Plane Paths

```mermaid
flowchart LR
    A["Client A WireGuard Interface"] -->|Direct UDP tunnel preferred| B["Client B WireGuard Interface"]
    A -->|Fallback when NAT blocks direct path| R["Relay Server"] --> B

    A -. broadcasts/multicast emulation .-> B
```

## 4. Sequence: Party Create + Join

```mermaid
sequenceDiagram
    participant HostUI as Host Web UI
    participant HostParty as Host PartyManager
    participant HostControl as Host ControlClient
    participant CPS as Control Plane Server
    participant JoinUI as Joiner Web UI
    participant JoinParty as Joiner PartyManager
    participant JoinControl as Joiner ControlClient

    HostUI->>HostParty: create_party(name, max_players)
    HostParty->>HostControl: register_party(...)
    HostControl->>CPS: POST /parties
    CPS-->>HostControl: party_id + token
    HostControl-->>HostParty: created
    HostParty-->>HostUI: party metadata

    JoinUI->>JoinParty: join_party(party_id, nickname)
    JoinParty->>JoinControl: join request
    JoinControl->>CPS: POST /parties/{id}/join
    CPS-->>JoinControl: peer list + auth token
    JoinControl-->>JoinParty: membership confirmed
    JoinParty-->>JoinUI: connected
```

## 5. Sequence: Connection Establishment and Fallback

```mermaid
sequenceDiagram
    participant A as Client A ConnectionManager
    participant NATa as Client A NAT
    participant NATb as Client B NAT
    participant B as Client B ConnectionManager
    participant RelaySel as RelaySelector
    participant Relay as Relay Server

    A->>NATa: detect_nat_type()
    B->>NATb: detect_nat_type()

    A->>B: attempt_direct_handshake()
    alt Direct path succeeds
        A->>A: configure WireGuard peer (direct)
        B->>B: configure WireGuard peer (direct)
        A-->>A: route=direct, low-latency
    else Direct path fails
        A->>RelaySel: select_best_relay(region, latency)
        RelaySel-->>A: relay endpoint
        A->>Relay: establish relayed path
        B->>Relay: establish relayed path
        A-->>A: route=relay
    end
```

## 6. Sequence: Game Detection + Mod Sync Planning

```mermaid
sequenceDiagram
    participant UI as Web UI
    participant GM as GameManager
    participant MS as ModSync Planner
    participant Peer as Party Peer

    UI->>GM: scan active game
    GM-->>UI: detected game profile

    UI->>GM: evaluate_mod_compatibility(game_id)
    GM->>MS: validate local artifacts(manifest)
    MS-->>GM: missing/valid artifacts
    GM-->>UI: compatibility report

    UI->>GM: build_mod_sync_plan(game_id)
    GM->>MS: generate peer fetch plan
    MS->>Peer: propose source URLs (WireGuard reachable)
    MS-->>GM: sync plan
    GM-->>UI: actionable download/sync steps
```

## 7. Runtime Signals and Control Loops

```mermaid
flowchart TB
    TICK["Heartbeat / periodic tasks"] --> HEALTH["Peer state refresh"]
    HEALTH --> ROUTE["Connection quality evaluation"]
    ROUTE -->|degraded| SWITCH["Relay failover / reconnect"]
    ROUTE -->|stable| KEEP["Keep direct route"]

    EVENTS["Game/process/network events"] --> PROFILE["Profile apply/reset"]
    EVENTS --> METRICS["Metrics capture"]
    METRICS --> DASH["UI dashboard"]
```

## 8. CI/CD and Documentation Automation

```mermaid
flowchart LR
    COMMIT["Push to main"] --> CI["ci.yml\nquality + tests + security"]
    COMMIT --> VER["update-readme-version.yml\nversioned docs sync"]
    COMMIT --> GAMESDOC["update-supported-games-readme.yml\nsupported games sync"]

    COMMIT --> AUTOTAG["auto-tag.yml\ncreate vX.Y.Z tag on pyproject bump"]
    AUTOTAG --> RELEASE["release.yml\nGitHub release + auto notes + assets"]
```

## 9. Failure Domains and Fallback Strategy

- Control plane unavailable: existing tunnels can continue; new joins/deep discovery degrade.
- Direct P2P blocked by NAT/firewall: relay fallback path is used.
- Relay degraded: selector can re-rank and switch to next candidate.
- Game mod mismatch: compatibility report + sync planning gives deterministic remediation path.

## 10. Reading Order for New Contributors

1. `docs/ARCHITECTURE.md`
2. This file (`docs/diagrams/SYSTEM_FLOW.md`)
3. `docs/CONTROL_PLANE.md`
4. `docs/NAT_TRAVERSAL.md`
5. `docs/TESTING.md`

