# CI/CD

Quality gates and automation flow for LANrage changes.

## Scope

Covers lint/test/release automation expectations and troubleshooting entry points.

Related docs:
- [Testing](TESTING.md)
- [Versioning](VERSIONING.md)

## Pipeline Goals

- block regressions before merge
- keep style/lint/test quality consistent
- provide reproducible release artifacts

## Core Gates

- formatting and lint checks
- unit/integration test runs
- optional coverage thresholds
- release packaging checks on tag/release paths

## Recommended Flow

1. run local quality checks before push
2. push branch and watch workflow statuses
3. inspect failing job logs and patch root cause
4. re-run until all required checks pass

## Failure Triage

- lint failure: fix style/import/static issues first
- test failure: isolate deterministic vs environment-sensitive failures
- flaky failure: capture evidence and reduce nondeterminism before retrying blind

## Release Safety

- release only from green commit
- ensure changelog/version metadata are aligned
- validate produced artifacts before publish

## Acceptance Criteria

This doc is complete when contributors can diagnose failed checks and release from a green pipeline reliably.
