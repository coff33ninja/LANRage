# Performance Optimization

Optimization strategy focused on latency, stability, and predictable runtime behavior.

## Scope

Covers optimization priorities and decision rules for LANrage runtime.

Related docs:
- [Performance Profiling](/docs/core/observability/PERFORMANCE_PROFILING.md)
- [Metrics](/docs/core/observability/METRICS.md)

## Optimization Priorities

1. reduce path latency on direct and relay flows
2. improve recovery behavior under degraded conditions
3. lower resource overhead in monitoring/control loops
4. preserve deterministic startup/join/connect behavior

## Decision Framework

For each proposed optimization:
- define target metric and baseline
- implement smallest high-impact change
- validate with tests and profiling
- rollback if gains are negligible or regressions appear

## Typical Optimization Areas

- connection monitor cadence and thresholds
- relay selection and failover heuristics
- expensive per-request recomputation in API handlers
- redundant probes or state writes

## Risks to Avoid

- reducing observability to gain minor throughput
- aggressive retries causing instability under outages
- overfitting heuristics to one network topology

## Acceptance Criteria

This doc is complete when optimization work can be prioritized, measured, and safely validated.
