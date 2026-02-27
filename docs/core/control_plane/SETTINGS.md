# Settings System

Database-backed settings and named configuration management.

## Scope

This document covers `core/control_plane/settings.py` and how runtime settings are loaded/applied.

Related docs:
- [API](API.md)
- [Network Layer](/docs/core/networking/NETWORK.md)
- [Control Plane Server](/docs/servers/CONTROL_PLANE_SERVER.md)

## Responsibilities

Settings subsystem responsibilities:
- persist typed settings values in SQLite
- provide async-safe get/set/all operations
- manage named server configs (save/list/activate/delete)
- manage favorites and custom game profiles
- provide integrity check, size, and backup helpers

Non-responsibilities:
- runtime service orchestration itself
- remote synchronization between machines

## Storage Model

Primary DB location:
- user-local settings DB under LANrage config directory

Core tables:
- `settings`
- `server_configs`
- `favorite_servers`
- `game_profiles`

Type handling:
- primitive and JSON-like values are serialized with stored type metadata
- deserialization restores typed runtime values

## Concurrency and Safety

- async lock protects multi-operation races in process
- per-operation DB interactions reduce inconsistent state risk
- explicit backup helper supports safe export snapshots

## Runtime Integration

`Config.load()` consumes settings DB values to produce effective runtime config.

Operationally:
- settings must be initialized before first load
- missing/invalid critical values should surface early at startup

## Named Configs Workflow

Typical lifecycle:
1. save named config with mode and payload
2. list configs for UI selection
3. activate a config set
4. delete obsolete profiles

Use cases:
- fast switching between client/relay setups
- preserving known-good profiles

## API and UI Integration

Settings endpoints:
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/settings/reset`
- `GET /api/settings/configs`
- `POST /api/settings/configs`
- `POST /api/settings/configs/{config_id}/activate`
- `DELETE /api/settings/configs/{config_id}`

UI:
- settings pages consume these endpoints for read/update and config management flows

## Maintenance Operations

- integrity validation
- database size inspection
- backup creation for recovery workflows

Use maintenance checks before upgrades or major configuration migrations.

## Failure Modes

Common issues:
- DB locked/contention scenarios
- corrupted DB file
- missing default values after reset/migration

Recovery:
- run integrity check
- restore from backup if available
- re-initialize defaults and re-apply known config set

## Testing Focus

Minimum regression scope:
- typed get/set roundtrip
- named config create/list/activate/delete
- favorites and game profile persistence
- integrity/backup helper behavior

## Acceptance Criteria

This doc is complete when:
- storage model and typed serialization are explicit
- API/UI integration points are explicit
- backup/recovery pathways are actionable
- config-set lifecycle is testable
