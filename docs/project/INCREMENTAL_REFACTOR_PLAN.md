# Incremental Refactor Plan

Goal: move from a flat `core/` layout to domain subpackages and complete canonical-import migration.

## Migration Policy

- Canonical locations live under domain packages (for example, `core/networking/*`).
- Legacy shim modules were removed after migration completion.
- Canonical package imports are now required.

## Migration Rules Per Slice

1. Move one domain group into a subpackage.
2. Update moved modules and consumers to stable absolute imports (`from core...`).
3. Run focused tests for that slice.
4. If green, continue to next slice.

## Domain Slices

### Slice 1 - `core/networking` (Completed)

- Canonical modules:
  - `core/networking/network.py`
  - `core/networking/nat.py`
  - `core/networking/ipam.py`
  - `core/networking/connection.py`
- Verification target:
  - `tests/test_wireguard.py`
  - `tests/test_nat.py`
  - `tests/test_ipam.py`
  - `tests/test_connection.py`

### Slice 2 - `core/control_plane` (Completed)

- Canonical modules:
  - `core/control_plane/control.py`
  - `core/control_plane/control_client.py`
  - `core/control_plane/party.py`
  - `core/control_plane/settings.py`
- Verification target:
  - `tests/test_control_signaling.py`
  - `tests/test_control_client.py`
  - `tests/test_control_server_auth.py`
  - `tests/test_control_server.py`
  - `tests/test_party.py`
  - `tests/test_settings.py`
  - `tests/test_multi_peer.py`
  - `tests/test_control_plane_logging.py`

### Slice 3 - `core/integrations` (Completed)

- Canonical target modules:
  - `core/integrations/discord_integration.py`
  - `core/integrations/updater.py`
- Verification target:
  - `tests/test_discord.py`
  - `tests/test_updater.py`

### Slice 4 - `core/observability` (Completed)

- Canonical target modules:
  - `core/observability/logging_config.py`
  - `core/observability/metrics.py`
  - `core/observability/profiler.py`
- Verification target:
  - `tests/test_logging_config.py`
  - `tests/test_metrics.py`
  - `tests/test_metrics_logging.py`
  - `tests/test_profiling.py`

### Slice 5 - `core/gameplay` (Completed)

- Canonical target modules:
  - `core/gameplay/games.py`
  - `core/gameplay/mod_sync.py`
  - `core/gameplay/server_browser.py`
  - `core/gameplay/broadcast.py`
- Verification target:
  - `tests/test_games.py`
  - `tests/test_game_detection_advanced.py`
  - `tests/test_mod_sync.py`
  - `tests/test_server_browser.py`
  - `tests/test_broadcast.py`
  - `tests/test_broadcast_dedup.py`
  - `tests/test_broadcast_logging.py`
  - `tests/test_games_logging.py`

## Final Cleanup Criteria

- All internal imports use canonical subpackage paths.
- All tests pass on canonical-only import layout.
- Guard rails block new legacy imports.

### Current Status

- Done: internal imports migrated to canonical package paths.
- Done: guard test added (`tests/test_no_legacy_core_imports.py`) to block legacy import reintroduction.
- Done: legacy shim modules removed in breaking-layout pass.

