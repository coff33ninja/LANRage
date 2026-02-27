# Troubleshooting

Runbook-oriented troubleshooting for common LANrage failures.

## Scope

Provides symptom -> diagnosis -> action guidance across startup, connectivity, control plane, and performance.

## Quick Triage Order

1. startup/config health
2. control-plane reachability/auth
3. NAT strategy and endpoint selection
4. WireGuard peer/interface state
5. runtime metrics and quality trends

## Common Scenarios

### Cannot start service

Checks:
- settings DB integrity
- WireGuard install and permissions
- port binding conflicts

### Cannot create/join party

Checks:
- control-plane mode and reachability
- party ID validity
- auth token registration path

### Peers discovered but cannot connect

Checks:
- NAT strategy selected
- direct path hole-punch outcome
- relay endpoint availability
- WireGuard peer add/remove success

### High latency or unstable session

Checks:
- direct vs relay path state
- relay region suitability
- repeated degraded/fail transitions in monitor loop
- host CPU/network saturation

### Discord features not working

Checks:
- webhook/invite URL validity
- Rich Presence app ID + dependency + desktop app

## Data to Collect Before Escalation

- relevant API endpoint responses
- recent logs around failure window
- connection/metrics snapshots
- reproduction steps with exact timing

## Acceptance Criteria

This doc is complete when common failures map to deterministic checks and actionable next steps.
