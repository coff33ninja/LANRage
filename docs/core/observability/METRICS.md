# Metrics and Observability

Operational metrics surface for connection quality, peer health, and host resource behavior.

## Scope

This document covers metrics collection and exposure behavior used by LANrage runtime.

Related docs:
- [API](API.md)
- [Performance Profiling](/docs/core/observability/PERFORMANCE_PROFILING.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## Metrics Domains

- Peer path quality: latency/jitter/status trends
- System health: CPU, memory, network rates
- Session metrics: game session timing and quality context
- Aggregate quality: network quality scoring/reporting

## Collection Model

- periodic collection loops gather system and peer signals
- rolling in-memory windows are used for summaries/history
- aggregation endpoints expose snapshots and history without requiring external storage by default

## API and Export Surface

- summary and peer/system endpoints under `/api/metrics/*`
- Prometheus-compatible export available at `/metrics`

Use `/metrics` for scrape-based tooling and `/api/metrics/*` for UI/diagnostic workflows.

## Operational Use Cases

- detect degraded peer paths before full disconnect
- validate relay/direct strategy quality over time
- correlate local resource saturation with connection instability
- baseline performance before and after releases

## Alerting Guidance

Suggested triggers:
- sustained high peer latency or jitter
- repeated state transitions to degraded/failed
- prolonged high CPU/memory pressure
- sharp drop in overall quality score

## Runbook Pointers

When quality degrades:
1. check peer-specific metrics
2. check system load metrics
3. verify strategy state (direct vs relay)
4. evaluate relay switch/reconnect outcomes

## Testing Focus

- endpoint shape and required fields
- aggregation correctness for rolling windows
- stability under missing/intermittent samples
- Prometheus output format sanity

## Acceptance Criteria

This doc is complete when metrics domains, API/export surface, and operational runbook usage are explicit.
