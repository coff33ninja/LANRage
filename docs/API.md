# API Reference

HTTP API surface exposed by `api/server.py`.

## Base

- Host: configured by runtime settings (default local host)
- Port: configured by runtime settings (default `8666`)
- Framework: FastAPI
- Interactive docs: `/docs`

## Core Endpoints

### Service and UI

- `GET /api` - service health
- `GET /metrics` - Prometheus text metrics
- `GET /` - main web UI
- `GET /logo.png`
- `GET /favicon.ico`

### Party

- `GET /status`
- `POST /party/create`
- `POST /party/join`
- `POST /party/leave`

### Metrics

- `GET /api/metrics/summary`
- `GET /api/metrics/peers`
- `GET /api/metrics/peers/{peer_id}`
- `GET /api/metrics/peers/{peer_id}/latency`
- `GET /api/metrics/system`
- `GET /api/metrics/system/history`
- `GET /api/metrics/sessions`

### Discord

- `POST /api/discord/webhook`
- `POST /api/discord/invite`
- `GET /api/discord/status`
- `GET /api/discord/instructions`
- `POST /api/discord/test`

### Server Browser

- `GET /api/servers`
- `POST /api/servers`
- `GET /api/servers/{server_id}`
- `DELETE /api/servers/{server_id}`
- `POST /api/servers/{server_id}/heartbeat`
- `POST /api/servers/{server_id}/players`
- `POST /api/servers/{server_id}/join`
- `POST /api/servers/{server_id}/favorite`
- `DELETE /api/servers/{server_id}/favorite`
- `GET /api/servers/{server_id}/latency`
- `GET /api/servers/stats`

### Games and Settings

- `GET /api/games`
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/settings/reset`
- `GET /api/settings/configs`
- `POST /api/settings/configs`
- `POST /api/settings/configs/{config_id}/activate`
- `DELETE /api/settings/configs/{config_id}`

### Updater

- `GET /api/system/update/status`
- `POST /api/system/update`

## Request/Response Conventions

- JSON is default response format unless endpoint declares otherwise (`/metrics` uses text format).
- Validation errors are returned as 4xx responses with FastAPI/Pydantic error payloads.
- Internal failures return 5xx with error detail payload.

## Party Workflow Example

1. `POST /party/create` to host a party.
2. Share party identifier out-of-band.
3. Joiners call `POST /party/join`.
4. Poll `GET /status` for runtime party state.
5. End session with `POST /party/leave`.

## Metrics Workflow Example

1. Read high-level health with `GET /api/metrics/summary`.
2. Drill into a peer via `GET /api/metrics/peers/{peer_id}`.
3. Pull latency history with `GET /api/metrics/peers/{peer_id}/latency`.
4. Integrate scrape tooling via `GET /metrics`.

## Settings Workflow Example

1. `GET /api/settings` for effective settings.
2. `POST /api/settings` to update values.
3. Manage named config sets with `/api/settings/configs*` endpoints.
4. Use `POST /api/settings/reset` for baseline reset.

## Error Handling Guidance

When an endpoint fails:
- verify upstream subsystem initialization (network/control/party/metrics)
- verify required IDs exist (party, peer, server, config)
- inspect API server logs for root-cause stack traces

## Acceptance Criteria

This API reference is complete when:
- all current route decorators in `api/server.py` are represented
- endpoint groups map cleanly to subsystem docs
- text vs JSON response semantics are explicit
