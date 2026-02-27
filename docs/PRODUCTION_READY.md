# Production Readiness

Operational readiness criteria before broad deployment.

## Scope

Defines minimum expectations for reliability, observability, and recoverability.

## Readiness Checklist

- all required CI checks green
- baseline tests and targeted integration tests pass
- metrics and logs available for runtime diagnosis
- rollback plan defined for release
- backup/recovery procedures validated (settings/state)

## Reliability Controls

- explicit failure handling in control/connection paths
- bounded retry/reconnect behavior
- stale-state cleanup loops functioning

## Security Controls

- token-protected control-plane routes in remote mode
- webhook/token-like secrets handled as sensitive config
- least-privilege runtime permissions on hosts

## Deployment Controls

- single-region smoke test before wider rollout
- monitor quality metrics after deploy
- gate promotion on stable post-deploy metrics window

## Acceptance Criteria

This doc is complete when a deployment can be approved or blocked using objective checks.
