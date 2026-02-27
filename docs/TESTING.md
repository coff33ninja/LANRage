# Testing

Testing strategy for correctness, regressions, and operational confidence.

## Scope

Covers test categories and execution expectations.

Related docs:
- [CI/CD](CI_CD.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## Test Categories

- unit tests for module-level behavior
- integration tests across control/NAT/connection flows
- API tests for route behavior and payload shape
- regression tests for recently fixed issues

## Execution Guidance

- run focused tests while developing
- run broader suite before merge
- include targeted tests for docs-described behavioral changes

## Priority Coverage Areas

- party create/join/leave lifecycle
- control-plane auth and protected endpoints
- NAT strategy direct/relay branches
- connection monitor/recovery behavior
- metrics and API endpoint correctness

## Failure Handling

- categorize failures: deterministic bug vs environment/setup
- fix root cause, avoid masking flaky behavior
- update/add tests when fixing behavior bugs

## Acceptance Criteria

This doc is complete when contributors can select the right test scope and interpret failures quickly.
