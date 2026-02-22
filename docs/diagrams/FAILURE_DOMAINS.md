# Failure Domains and Fallbacks

- Control plane unavailable: existing tunnels can continue; new joins/discovery degrade.
- Direct P2P blocked by NAT/firewall: relay fallback path is used.
- Relay degraded: selector can re-rank and switch to next candidate.
- Game mod mismatch: compatibility report and sync planning provide deterministic remediation.
