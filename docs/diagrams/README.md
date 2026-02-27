# Diagrams Index

Architecture diagrams for LANrage are split by concern for easier navigation.

## Core Architecture

- [System Flow Overview](SYSTEM_FLOW.md)
- [System Context](SYSTEM_CONTEXT.md)
- [Client Components](CLIENT_COMPONENTS.md)
- [Data Plane Paths](DATA_PLANE_PATHS.md)

## Runtime Sequences

- [Startup Sequence](STARTUP_SEQUENCE.md)
- [Signal Queue/Poll Sequence](SIGNAL_QUEUE_POLL_SEQUENCE.md)
- [Party Lifecycle Sequence](SEQUENCE_PARTY_LIFECYCLE.md)
- [Party Host/Join Lifecycle](PARTY_HOST_JOIN_LIFECYCLE.md)
- [Connection Fallback Sequence](SEQUENCE_CONNECTION_FALLBACK.md)
- [Game + Mod Sync Sequence](SEQUENCE_GAME_MODSYNC.md)
- [Control Server Request Flow](CONTROL_SERVER_REQUEST_FLOW.md)
- [Network Interface Lifecycle](NETWORK_INTERFACE_LIFECYCLE.md)
- [NAT Strategy Decision Tree](NAT_STRATEGY_DECISION_TREE.md)
- [Connection State Machine](CONNECTION_STATE_MACHINE.md)

## Lifecycle and State

- [Control Plane State Machine](CONTROL_PLANE_STATE_MACHINE.md)
- [Control Server Cleanup Loop](CONTROL_SERVER_CLEANUP_LOOP.md)

## Operations

- [Runtime Control Loops](RUNTIME_CONTROL_LOOPS.md)
- [CI/CD and Release Automation](CI_CD_AUTOMATION.md)
- [Failure Domains and Fallbacks](FAILURE_DOMAINS.md)

## Suggested Reading Order

1. `SYSTEM_FLOW.md`
2. `SYSTEM_CONTEXT.md`
3. `STARTUP_SEQUENCE.md`
4. `CONTROL_PLANE_STATE_MACHINE.md`
5. `SIGNAL_QUEUE_POLL_SEQUENCE.md`
6. `CONTROL_SERVER_REQUEST_FLOW.md`
7. `CONTROL_SERVER_CLEANUP_LOOP.md`
8. `CLIENT_COMPONENTS.md`
9. `NETWORK_INTERFACE_LIFECYCLE.md`
10. `SEQUENCE_CONNECTION_FALLBACK.md`
11. `NAT_STRATEGY_DECISION_TREE.md`
12. `CONNECTION_STATE_MACHINE.md`
13. `SEQUENCE_GAME_MODSYNC.md`
14. `PARTY_HOST_JOIN_LIFECYCLE.md`
15. `CI_CD_AUTOMATION.md`
