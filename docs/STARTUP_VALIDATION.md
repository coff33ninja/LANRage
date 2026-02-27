# Startup Validation

Checklist and diagnostics for reliable LANrage startup.

## Scope

Covers preflight checks and startup failure triage.

Related docs:
- [Network Layer](/docs/core/networking/NETWORK.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## Preflight Checklist

- settings DB is readable/writable
- WireGuard tools and privileges are available
- required directories/files are accessible
- configured ports/hosts are valid

## Startup Sequence Validation

Validate in order:
1. config/settings load
2. network initialization
3. NAT/control initialization
4. metrics/integrations start
5. API/UI binding

## Failure Triage

- fail at config load: verify DB state and defaults
- fail at network init: verify WireGuard install/privileges
- fail at control init: verify mode and remote endpoint/auth config
- fail at API bind: verify host/port conflicts

## Acceptance Criteria

This doc is complete when startup issues can be isolated to stage and resolved with explicit checks.
