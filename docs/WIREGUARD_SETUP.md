# WireGuard Setup

Host prerequisites and verification steps for WireGuard-backed LANrage networking.

## Scope

Covers environment prerequisites for network initialization on supported platforms.

Related docs:
- [Network Layer](/docs/core/networking/NETWORK.md)
- [Startup Validation](STARTUP_VALIDATION.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## Prerequisites

### Windows

- WireGuard installed and available
- elevated privileges for tunnel/service operations

### Linux

- wireguard tools/module available
- root/sudo access for interface operations
- `ip`/`wg` commands available

## Validation Steps

1. confirm WireGuard tooling is installed
2. confirm required privileges
3. start LANrage and verify interface creation succeeds
4. verify status endpoint and connection flow in UI

## Common Setup Failures

- tool missing from host
- insufficient privilege for interface operations
- conflicting interface/service names
- firewall/host policy blocking UDP path

## Recovery

- fix prerequisite and restart runtime
- cleanup stale interface/service if previous run failed mid-setup
- re-run startup validation checklist

## Security Notes

- protect key files in configured keys directory
- use least-privilege where possible while preserving required network operations

## Acceptance Criteria

This doc is complete when operators can validate prerequisites and recover from common setup failures.
