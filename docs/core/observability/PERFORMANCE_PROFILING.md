# Performance Profiling

Profiling workflow for identifying hotspots and runtime regressions.

## Scope

Covers profiling strategy and practical workflows for LANrage runtime.

Related docs:
- [Metrics](/docs/core/observability/METRICS.md)
- [Performance Optimization](PERFORMANCE_OPTIMIZATION.md)

## Profiling Goals

- identify hot functions/paths under realistic load
- measure effect of optimization changes
- catch regressions in CI/local performance runs

## Workflow

1. define target scenario (startup, join, sustained session, teardown)
2. collect profiling data with representative workload
3. rank hotspots by cumulative and per-call cost
4. optimize highest-impact path first
5. re-measure and compare against baseline

## Common Targets

- connection orchestration loops
- relay selection and probe paths
- metrics aggregation paths
- API endpoints under load

## Guardrails

- avoid micro-optimizing cold paths
- keep readability and correctness priority
- confirm no behavior regressions while optimizing

## Regression Checks

- compare before/after metrics and test pass rate
- confirm latency/quality behavior remains stable
- include profiling artifacts for high-impact changes

## Acceptance Criteria

This doc is complete when profiling workflow is repeatable and tied to concrete optimization decisions.
