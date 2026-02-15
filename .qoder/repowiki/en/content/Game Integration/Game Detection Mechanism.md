# Game Detection Mechanism

<cite>
**Referenced Files in This Document**
- [core/games.py](file://core/games.py)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py)
- [tests/test_games.py](file://tests/test_games.py)
- [game_profiles/battle_royale.json](file://game_profiles/battle_royale.json)
- [game_profiles/fps.json](file://game_profiles/fps.json)
- [IMPLEMENTATION_PLAN.md](file://IMPLEMENTATION_PLAN.md)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md)
- [core/logging_config.py](file://core/logging_config.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
This document explains the multi-method game detection mechanism used to identify running games and apply game-specific optimizations. The system employs a three-tier detection approach:
- Process name matching (primary method, 95% confidence)
- Window title detection (Windows only, 80% confidence)
- Port-based detection (fallback method, 60–75% confidence)

It also documents the fuzzy matching algorithm using Levenshtein distance, the detection loop architecture, confidence scoring, ranking, platform-specific considerations, detection history tracking, and event logging.

## Project Structure
The detection logic resides primarily in the core module and is exercised by focused tests. Game profiles are defined in JSON files under the game_profiles directory.

```mermaid
graph TB
subgraph "Core"
G["core/games.py"]
L["core/logging_config.py"]
end
subgraph "Profiles"
BR["game_profiles/battle_royale.json"]
FPS["game_profiles/fps.json"]
end
subgraph "Tests"
T1["tests/test_game_detection_advanced.py"]
T2["tests/test_games.py"]
end
subgraph "Docs"
TP["IMPLEMENTATION_PLAN.md"]
TR["docs/TROUBLESHOOTING.md"]
end
G --> BR
G --> FPS
T1 --> G
T2 --> G
TP --> G
TR --> G
G --> L
```

**Diagram sources**
- [core/games.py](file://core/games.py#L364-L448)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L1-L373)
- [tests/test_games.py](file://tests/test_games.py#L1-L149)
- [game_profiles/battle_royale.json](file://game_profiles/battle_royale.json#L1-L45)
- [game_profiles/fps.json](file://game_profiles/fps.json#L1-L143)
- [IMPLEMENTATION_PLAN.md](file://IMPLEMENTATION_PLAN.md#L332-L375)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L52-L85)
- [core/logging_config.py](file://core/logging_config.py#L1-L277)

**Section sources**
- [core/games.py](file://core/games.py#L364-L448)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L1-L373)
- [tests/test_games.py](file://tests/test_games.py#L1-L149)
- [game_profiles/battle_royale.json](file://game_profiles/battle_royale.json#L1-L45)
- [game_profiles/fps.json](file://game_profiles/fps.json#L1-L143)
- [IMPLEMENTATION_PLAN.md](file://IMPLEMENTATION_PLAN.md#L332-L375)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L52-L85)
- [core/logging_config.py](file://core/logging_config.py#L1-L277)

## Core Components
- GameDetector: Orchestrates detection across methods, manages detection history, and triggers game lifecycle events.
- DetectionResult: Encapsulates detection outcomes with confidence and method metadata.
- Fuzzy matching: Uses Levenshtein distance to match process names against profiles.
- Detection methods:
  - Process name matching (highest priority)
  - Window title detection (Windows only)
  - Port-based detection (TCP/UDP)

Key behaviors:
- Non-blocking detection using asyncio executors.
- Confidence-based ranking and selection.
- Graceful degradation for unsupported platforms.
- Structured logging and correlation context propagation.

**Section sources**
- [core/games.py](file://core/games.py#L74-L92)
- [core/games.py](file://core/games.py#L169-L228)
- [core/games.py](file://core/games.py#L364-L448)
- [core/games.py](file://core/games.py#L450-L510)
- [core/games.py](file://core/games.py#L511-L581)
- [core/logging_config.py](file://core/logging_config.py#L233-L277)

## Architecture Overview
The detection system runs continuously, periodically scanning for running games across multiple methods and selecting the highest-confidence result per game.

```mermaid
sequenceDiagram
participant Loop as "Detection Loop"
participant Proc as "Process Scanner"
participant Win as "Window Title Detector"
participant Port as "Port Detector"
participant Rank as "Ranking Engine"
participant Events as "Lifecycle Events"
Loop->>Proc : Enumerate running processes
Proc-->>Loop : Process names
Loop->>Win : Enumerate visible windows (Windows only)
Win-->>Loop : Window titles
Loop->>Port : Probe open ports per profile
Port-->>Loop : Matched ports per game
Loop->>Rank : Aggregate DetectionResult items
Rank-->>Loop : Best DetectionResult per game
Loop->>Events : _on_game_started/_on_game_stopped
Events-->>Loop : Optimizations applied
```

**Diagram sources**
- [core/games.py](file://core/games.py#L364-L448)
- [core/games.py](file://core/games.py#L450-L510)
- [core/games.py](file://core/games.py#L511-L581)
- [core/games.py](file://core/games.py#L583-L632)

## Detailed Component Analysis

### Detection Loop and Ranking
- The loop runs every five seconds and aggregates results per game across methods.
- Results are ranked by confidence; the highest wins.
- New and stopped games trigger lifecycle events and logging.

```mermaid
flowchart TD
Start([Start Detection Cycle]) --> ScanProc["Scan Processes"]
ScanProc --> ScanWin["Scan Windows (Windows only)"]
ScanWin --> ScanPorts["Probe Open Ports"]
ScanPorts --> Aggregate["Aggregate Results per Game"]
Aggregate --> Rank["Select Highest Confidence"]
Rank --> NewGames{"New Games?"}
NewGames --> |Yes| OnStart["_on_game_started()"]
NewGames --> |No| CheckStop
OnStart --> CheckStop["Stopped Games?"]
CheckStop --> |Yes| OnStop["_on_game_stopped()"]
CheckStop --> |No| Sleep
OnStop --> Sleep([Sleep 5s])
Sleep --> Start
```

**Diagram sources**
- [core/games.py](file://core/games.py#L364-L448)
- [core/games.py](file://core/games.py#L583-L632)

**Section sources**
- [core/games.py](file://core/games.py#L364-L448)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L233-L265)

### Process Name Matching (Primary Method, 95% Confidence)
- Scans all running processes and compares names to profile executables.
- Uses fuzzy matching with Levenshtein distance and configurable threshold.
- Assigns 95% confidence when matched.

Fuzzy matching algorithm:
- Exact match (case-insensitive) and extension removal (e.g., .exe, .bat) are checked first.
- If still unmatched, computes Levenshtein distance between cleaned names.
- Similarity = 1 − (distance / max_len); match if similarity ≥ threshold.

```mermaid
flowchart TD
A["Process Name"] --> B["Clean Extensions (.exe/.bat)"]
B --> C{"Exact Match?"}
C --> |Yes| D["Match = True"]
C --> |No| E["Levenshtein Distance"]
E --> F["Similarity = 1 − (distance/max_len)"]
F --> G{"Similarity ≥ Threshold?"}
G --> |Yes| D
G --> |No| H["Match = False"]
```

**Diagram sources**
- [core/games.py](file://core/games.py#L194-L228)

Confidence scoring:
- Process-based detection sets confidence to 0.95 upon successful fuzzy match.

Platform considerations:
- No platform restrictions; always active.

**Section sources**
- [core/games.py](file://core/games.py#L194-L228)
- [core/games.py](file://core/games.py#L396-L411)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L119-L177)

### Window Title Detection (Windows Only, 80% Confidence)
- Enumerates visible window titles on Windows systems.
- Matches profile game names within window titles.
- Assigns 80% confidence when matched.
- Gracefully degrades on non-Windows platforms.

```mermaid
flowchart TD
WStart([On Windows]) --> Enum["Enum Windows"]
Enum --> Titles["Collect Visible Titles"]
Titles --> Match["Check if Profile Name in Title"]
Match --> |Yes| WinRes["Create DetectionResult (conf=0.80)"]
Match --> |No| WEnd([No Results])
WStart --> |Not Windows| WEnd
```

**Diagram sources**
- [core/games.py](file://core/games.py#L450-L510)

Platform considerations:
- Uses optional pywin32 dependency; silently skipped if unavailable.
- Non-Windows systems return empty results.

**Section sources**
- [core/games.py](file://core/games.py#L450-L510)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L209-L231)

### Port-Based Detection (Fallback, 60–75% Confidence)
- Probes local ports per profile for TCP and UDP.
- Calculates confidence based on match ratio: min(0.6 + (matched/total)*0.2, 0.75).
- Returns DetectionResult items with matched ports details.

```mermaid
flowchart TD
PStart([Probe Ports]) --> Protocols{"Protocol?"}
Protocols --> |UDP| UDP["Bind to UDP port (loopback)"]
Protocols --> |TCP| TCP["Connect to TCP port (loopback)"]
UDP --> UDPRes["Record Match if In Use"]
TCP --> TCPRes["Record Match if Connected"]
UDPRes --> NextPort["Next Port"]
TCPRes --> NextPort
NextPort --> Done{"All Ports Checked?"}
Done --> |No| Protocols
Done --> |Yes| Ratio["Compute Match Ratio"]
Ratio --> Conf["Conf = min(0.6 + ratio*0.2, 0.75)"]
Conf --> PEnd([Return Results])
```

**Diagram sources**
- [core/games.py](file://core/games.py#L511-L581)

**Section sources**
- [core/games.py](file://core/games.py#L511-L581)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L179-L207)

### DetectionResult and Ranking
- Dataclass encapsulating game_id, profile, confidence, method, and details.
- Confidence clamped to [0.0, 1.0].
- Sorting by confidence (higher is better) via __lt__.

```mermaid
classDiagram
class DetectionResult {
+string game_id
+GameProfile profile
+float confidence
+string method
+dict details
+__post_init__()
+__lt__(other)
}
```

**Diagram sources**
- [core/games.py](file://core/games.py#L74-L92)

**Section sources**
- [core/games.py](file://core/games.py#L74-L92)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L54-L117)

### Detection History Tracking and Event Logging
- Tracks detection events as (timestamp, game_id, action) tuples.
- Records "started" and "stopped" actions.
- Limits history to last 100 events.
- Sets correlation context for traceability and integrates with structured logging.

```mermaid
sequenceDiagram
participant GD as "GameDetector"
participant Hist as "History Buffer"
participant Log as "Logger"
GD->>Hist : Append (timestamp, game_id, "started")
GD->>Log : Log detection with correlation_id
Note over GD,Log : Context propagated via logging_config
GD->>Hist : Append (timestamp, game_id, "stopped")
```

**Diagram sources**
- [core/games.py](file://core/games.py#L583-L632)
- [core/logging_config.py](file://core/logging_config.py#L233-L277)

**Section sources**
- [core/games.py](file://core/games.py#L278-L280)
- [core/games.py](file://core/games.py#L583-L632)
- [core/logging_config.py](file://core/logging_config.py#L233-L277)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L266-L297)

### Example Detection Scenarios
- Process detection with high confidence:
  - Exact or fuzzy-matched process name yields 95% confidence.
- Window title detection on Windows:
  - Visible window title containing the game name yields 80% confidence.
- Port-based detection:
  - Partial or full port match yields 60–75% confidence depending on match ratio.

Validation references:
- Process detection confidence assertions and fuzzy match tests.
- Port detection result validation and confidence range tests.
- Window title detection behavior on Windows and non-Windows.

**Section sources**
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L119-L177)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L179-L207)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L209-L231)

## Dependency Analysis
The detection system depends on:
- psutil for process enumeration
- platform for OS checks
- socket for port probing
- win32gui (optional) for window title enumeration on Windows
- Structured logging for observability

```mermaid
graph LR
GD["GameDetector"] --> PS["psutil"]
GD --> PL["platform"]
GD --> SK["socket"]
GD --> LG["logging_config"]
GD -. optional .-> WG["win32gui"]
```

**Diagram sources**
- [core/games.py](file://core/games.py#L3-L17)
- [core/games.py](file://core/games.py#L450-L510)
- [core/logging_config.py](file://core/logging_config.py#L1-L277)

**Section sources**
- [core/games.py](file://core/games.py#L3-L17)
- [core/games.py](file://core/games.py#L450-L510)
- [core/logging_config.py](file://core/logging_config.py#L1-L277)

## Performance Considerations
- Non-blocking I/O: Uses asyncio run_in_executor for process and window/port scans.
- Lightweight fuzzy matching: Levenshtein computation is bounded by typical process name lengths.
- Periodic polling: Detection runs every 5 seconds to balance responsiveness and overhead.
- Graceful degradation: Windows-only features are safely skipped when dependencies are missing.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common detection failures and resolutions:
- Game not detected:
  - Verify the game is supported or create a custom profile.
  - Ensure the process name matches the profile executable (fuzzy matching helps).
  - Confirm ports are open/listening for port-based detection.
- Windows-only features:
  - Window title detection requires pywin32; absence leads to graceful skipping.
- Logging and diagnostics:
  - Enable debug logging and review detection history and correlation IDs.
  - Use the troubleshooting flowcharts for step-by-step resolution.

```mermaid
flowchart TD
DStart([Game Not Detected]) --> Supported{"Supported?"}
Supported --> |No| Profiles["Check game_profiles/"]
Profiles --> Exists{"Exists?"}
Exists --> |No| Custom["Create Custom Profile"]
Exists --> |Yes| Running{"Game Running?"}
Running --> |No| Start["Start Game"]
Running --> |Yes| Process["Check Process Name vs Profile"]
Process --> Match{"Matches?"}
Match --> |No| Update["Update Profile Executable"]
Match --> |Yes| Ports["Check Ports Open"]
Ports --> Conf["Confidence 60–75%"]
Conf --> Detected{"Detected?"}
Detected --> |No| Support["Request Support / Generic Mode"]
Detected --> |Yes| Success([Optimized])
```

**Diagram sources**
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L52-L85)

**Section sources**
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L52-L85)
- [core/games.py](file://core/games.py#L450-L510)
- [core/games.py](file://core/games.py#L511-L581)
- [tests/test_game_detection_advanced.py](file://tests/test_game_detection_advanced.py#L119-L177)

## Conclusion
The multi-method detection system provides robust, layered identification of running games with confidence-aware ranking. Process name matching offers the highest accuracy, window title detection enhances coverage on Windows, and port-based detection serves as a reliable fallback. The design emphasizes non-blocking operations, platform-aware behavior, and comprehensive observability through structured logging and detection history tracking.