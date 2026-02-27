# Discord Integration Rationale

Why LANrage integrates with Discord instead of building first-party chat/voice/screen features.

## Decision Summary

LANrage focuses on low-latency virtual LAN transport and session orchestration. Discord integration provides communication features without diverting core networking effort.

## Tradeoff Analysis

Benefits:
- mature voice/chat/screen ecosystem
- lower operational burden and cost
- familiar user workflow for gaming communities

Costs:
- dependency on external platform availability/policies
- webhook/invite configuration burden
- reduced control over communication UX internals

## Scope Boundary

In current architecture:
- LANrage handles networking, coordination, and observability
- Discord handles social communication layer

This boundary keeps complexity manageable while preserving core performance goals.

## When to Revisit

Re-evaluate if:
- Discord dependency becomes operationally risky for target deployments
- product goals require fully self-hosted communication stack
- enterprise/offline requirements disallow third-party comms integration

See also:
- [Discord Integration](/docs/core/integrations/DISCORD.md)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](project/ROADMAP.md)
