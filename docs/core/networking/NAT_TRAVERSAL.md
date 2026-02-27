# NAT Traversal

NAT detection, direct-connect attempts, and relay fallback coordination for peer connectivity.

## Scope

This document covers `core/networking/nat.py` behavior and interaction with connection orchestration.

Related docs:
- [Connection Management](/docs/core/networking/CONNECTION.md)
- [Network Layer](/docs/core/networking/NETWORK.md)
- [Relay Server](/docs/servers/RELAY_SERVER.md)
- [Control Plane](/docs/core/control_plane/CONTROL_PLANE.md)

Related diagrams:
- [NAT Strategy Decision Tree](diagrams/NAT_STRATEGY_DECISION_TREE.md)
- [Connection Fallback Sequence](diagrams/SEQUENCE_CONNECTION_FALLBACK.md)

## Responsibilities

`NATTraversal` and `ConnectionCoordinator` are responsible for:
- NAT type detection via STUN
- hole-punch attempt for direct path establishment
- strategy decision (direct or relay)
- relay discovery and best-endpoint selection

They are not responsible for:
- creating WireGuard interfaces
- party membership lifecycle
- long-term metrics storage

## NAT Types and Compatibility

`NATType` states:
- `UNKNOWN`
- `OPEN`
- `FULL_CONE`
- `RESTRICTED_CONE`
- `PORT_RESTRICTED_CONE`
- `SYMMETRIC`

Practical strategy rule:
- if `can_direct_connect(peer_nat_type)` is true -> attempt direct
- otherwise -> relay

## STUN Detection Flow

Detection behavior:
1. iterate configured STUN servers
2. send binding request
3. parse mapped address attributes
4. infer NAT type from local/public mapping
5. persist public/local endpoint data on success

Failure behavior:
- if all STUN probes fail, raise NAT-specific error for upper-layer fallback handling

## Direct Path Attempt

Direct strategy uses UDP hole punching:
- send punch packets toward peer public endpoint
- wait for acknowledgement window
- return success/failure

If direct attempt fails, coordinator falls back to relay.

## Relay Fallback Flow

Relay endpoint discovery order:
1. control-plane-discovered relays (if client available)
2. configured relay in runtime settings
3. default relay endpoint fallback

Best relay selection:
- measure candidate relay latency
- choose lowest-latency reachable relay
- fallback to first candidate when measurements unavailable

## Important Boundary: Probe Fallbacks

ICMP -> TCP -> DNS latency fallback with measurement-interval caching is a **server browser** feature (`core/gameplay/server_browser.py`), not NAT traversal relay-selection logic in `core/networking/nat.py`.

NAT relay selection remains based on its own relay-latency probe path and fallback ordering above.

## Error and Recovery Semantics

Common error conditions:
- STUN server timeout/unreachable
- malformed or unusable peer NAT info
- hole-punch timeout/failure
- relay discovery endpoint unavailable

Recovery principles:
- degrade from direct to relay
- continue with configured/default relay when control-plane discovery fails
- surface explicit failure context to connection manager for status and retry behavior

## Security Notes

- NAT traversal exchanges coordination metadata only.
- Data payload confidentiality remains in WireGuard transport layer.
- Relay fallback does not require relay payload decryption.

## Testing Focus

Minimum regression coverage:
- NAT detection success/failure paths
- strategy decision for representative NAT combinations
- hole-punch success/failure handling
- relay discovery hierarchy and selection behavior
- relay fallback when control-plane relay list is unavailable

## Acceptance Criteria

This doc is complete when:
- NAT decision semantics and fallback order are explicit.
- direct vs relay behavior is operationally testable.
- boundaries between NAT traversal and server browser probing are explicit.
- failure handling aligns with current connection coordinator behavior.

