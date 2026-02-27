# LANrage - What's Missing (Current Status)

**Last Verified**: February 27, 2026  
**Scope**: Current codebase status (not the archival February 2026 snapshot)

---

## Summary

Most items previously listed as "missing" are implemented. The old file had become stale and mixed historical notes with active work.

As of this update:
- Server-browser auto-join flow is implemented.
- Control-plane signaling queue/poll path is implemented.
- Remote websocket auth handshake is implemented (lightweight token-aware handshake).
- Party join now lazily initializes NAT/control plane instead of failing early.
- Latency measurement includes:
  - multi-sample ICMP median
  - EMA smoothing
  - trend detection
  - adaptive measurement interval
  - TCP connect fallback
  - DNS lookup fallback
- Control-plane HTTP APIs enforce Bearer token authentication.
- Prometheus-compatible `/metrics` endpoint is available from the API server.

---

## Recently Completed (This Pass)

1. **Server browser auto-join**
- `static/servers.html` now completes join flow and redirects to main UI.

2. **Control-plane signaling**
- `core/control.py` now queues signaling payloads per target peer.
- Added polling API in control layer: `poll_signals(...)`.

3. **Remote control-plane auth + heartbeat hardening**
- `core/control.py` now sends token-aware auth payload over websocket.
- Remote heartbeat path now sends websocket heartbeat messages correctly.

4. **Party join robustness**
- `core/party.py` now lazy-initializes NAT/control when needed during join.

5. **Server registration fix**
- `api/server.py` host lookup now uses `party.host_id` correctly.

6. **Latency fallback completion**
- `core/server_browser.py` now falls back to TCP connect timing, then DNS lookup timing when ping fails.
- Measurement interval cache is now respected to avoid redundant probes.

7. **Stale TODO cleanup**
- Removed obsolete placeholder TODO in `core/config.py`.

8. **Control-plane auth hardening**
- `servers/control_server.py` now enforces token auth on party/peer/relay endpoints.
- `core/control_client.py` now auto-registers peers and acquires auth token before protected calls.
- `core/party.py` now proactively registers peer identity when initializing remote control.

9. **Observability: Prometheus endpoint**
- `api/server.py` now exposes `/metrics` in Prometheus text format.

10. **Connection quality scoring integration**
- `core/metrics.py` now provides `get_network_quality_report()` with score, grade, peer-grade map, and system contribution.
- Overall network quality scoring now prioritizes peer-path quality while retaining system load influence.

11. **Relay optimization weighting**
- `core/relay_selector.py` now supports geographic weighting using peer regions and optional region latency matrix.
- Relay scoring now includes overload penalties for heavily loaded relays.

12. **Conflict-resolution semantics (LWW + hooks)**
- `core/conflict_resolver.py` now supports:
  - conflict event hooks (`register_conflict_hook`)
  - batch Last-Write-Wins resolution (`resolve_batch_lww`) using timestamp + priority tiebreak

---

## Remaining Work (Actual)

The following are still optional/advanced and not blocking core functionality:

1. **Control-plane security evolution**
- Optional OAuth/JWT integration if remote multi-tenant deployment is required.
- WebSocket-side strict auth policy if/when centralized WS signaling service is deployed.

2. **Observability expansion**
- Alerting thresholds and long-horizon dashboards.

3. **Phase 5+ enhancements**
- Alerting automation for quality degradation based on score/grade thresholds.
- Optional relay policy tuning via runtime-configurable weights.
- Extended conflict audit persistence (durable operation journal).

---

## Test Coverage Added For This Update

- `tests/test_control_signaling.py` for signaling queue/poll behavior.
- `tests/test_party.py` for lazy `join_party` initialization path.
- `tests/test_server_browser.py` for TCP fallback and measurement interval cache behavior.
- `tests/test_control_server_auth.py` for Bearer token enforcement.
- `tests/test_control_client.py` includes auto-auth regression coverage.
- `tests/test_api_prometheus_metrics.py` for `/metrics` export format.
- `tests/test_metrics.py` includes network quality report coverage.
- `tests/test_relay_selector.py` includes geographic weighting coverage.
- `tests/test_conflict_resolver.py` includes LWW and conflict-hook coverage.

---

## Validation Snapshot

Focused tests run locally:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_party.py tests/test_control_signaling.py tests/test_control_plane_logging.py tests/test_server_browser.py tests/test_control_server.py tests/test_control_server_auth.py tests/test_control_client.py tests/test_api_prometheus_metrics.py -q
```

If you want, next step is a full suite run and then a final cleanup pass over `IMPLEMENTATION_PLAN.md` so both planning/status documents are aligned.
