# Network Layer

WireGuard interface and peer transport management for LANrage.

## Scope

This doc covers `core/networking/network.py` behavior and its interface with connection orchestration.

Related docs:
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [NAT Traversal](/docs/core/networking/NAT_TRAVERSAL.md)
- [WireGuard Setup](WIREGUARD_SETUP.md)
- [Architecture](ARCHITECTURE.md)

Related diagrams:
- [Network Interface Lifecycle](diagrams/NETWORK_INTERFACE_LIFECYCLE.md)
- [Data Plane Paths](diagrams/DATA_PLANE_PATHS.md)

## Responsibilities

`NetworkManager` is responsible for:
- WireGuard availability checks
- key generation/load and persistence
- interface creation/cleanup (platform-specific)
- peer add/remove operations
- latency probes and interface status reporting

It is not responsible for peer discovery strategy decisions (handled by connection/NAT/control layers).

## Runtime Model

Startup sequence:
1. Check WireGuard tools availability.
2. Ensure keys exist (load existing or generate new).
3. Create interface for current platform.
4. Mark interface active for subsequent peer operations.

Teardown sequence:
1. Remove platform-specific interface/service.
2. Mark interface inactive.

## Key Management

- Curve/X25519 keys are generated when absent.
- Keys are stored under configured `keys_dir`.
- Base64-encoded values are prepared for WireGuard command/config usage.
- Unix private key permissions are tightened to owner-only.

Operational note:
- Current behavior is persistent-key reuse, not automatic rotation.

## Cross-Platform Interface Behavior

### Windows path

- Generates tunnel config file (`<interface>.conf`) under config dir.
- Uses WireGuard tunnel service install/reuse flow.
- Requires elevated privileges.

### Linux path

- Requires root/sudo.
- Creates interface via `ip link add ... type wireguard`.
- Applies private key and address/MTU settings.
- Brings interface up and cleans up on failure.

See [WireGuard Setup](WIREGUARD_SETUP.md) for host prerequisites.

## Peer Operations

### Add peer

Inputs:
- peer public key
- optional endpoint
- allowed IP ranges

Behavior:
- Configures persistent keepalive for NAT stability.
- Supports direct or relay endpoint assignment from upstream connection logic.

### Remove peer

Behavior:
- Removes peer entry by public key.
- Used by disconnect and cleanup paths.

## Status and Latency

- `get_interface_status()` reports interface and `wg show` output/error state.
- `measure_latency(peer_ip)` performs platform-specific ping parsing.

Latency semantics:
- Returns numeric ms on success.
- Returns `None` when unreachable/probe failed.

## Error and Failure Semantics

Major failure classes:
- WireGuard missing/unavailable
- insufficient privilege for interface operations
- command timeout/failure during create/update/cleanup
- endpoint/peer configuration failures

Behavior:
- command failures raise explicit exceptions
- cleanup attempts are made where possible
- operational logs capture command context for debugging

## Operational Guidance

- Keep interface naming consistent across environment and docs.
- Ensure firewall rules support UDP transport and probe behavior.
- Verify privilege model before startup in automation contexts.
- Treat `network.log` and service-level logs as first-line diagnostics.

## Testing Focus

Minimum regression scope for network changes:
- interface create/cleanup paths per platform
- key generation and key reload path
- add/remove peer command composition
- latency parsing behavior
- interface status reporting under error conditions

## Acceptance Criteria

This doc is complete when:
- platform-specific lifecycle behavior is explicit
- key lifecycle and permission model are explicit
- peer operation semantics map to connection-layer usage
- failure modes and diagnostics are actionable

