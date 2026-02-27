# Discord Integration

Discord webhook and Rich Presence integration surface for LANrage sessions.

## Scope

This document covers `core/integrations/discord_integration.py` behavior and related API setup paths.

Related docs:
- [Discord Setup Guide](DISCORD_SETUP_GUIDE.md)
- [Discord App Setup](DISCORD_APP_SETUP.md)
- [Discord Rich Presence Setup](DISCORD_RICH_PRESENCE_SETUP.md)
- [API](API.md)

## Responsibilities

Discord integration responsibilities:
- webhook notification delivery for party/session events
- optional Rich Presence updates via Discord RPC
- invite-link storage and distribution in notification context
- status/test helpers for setup validation

Non-responsibilities:
- custom voice/text/chat hosting
- storing Discord credentials beyond configured URLs/app ID

## Notification Model

Typical event notifications:
- party created
- peer joined/left
- game started/ended

Delivery behavior:
- send structured webhook payload
- tolerate transient failures without crashing gameplay runtime

## Rich Presence Model

Optional capability requiring desktop Discord + presence dependency.

Presence fields typically include:
- state and details
- party size
- session timing

Operational notes:
- requires valid Discord application ID in settings
- presence clear/update must handle unavailable RPC gracefully

## Configuration Paths

Primary configuration values:
- `discord_webhook_url`
- `discord_party_invite_url`
- `discord_app_id`

Configuration via:
- settings UI
- API endpoints
- settings database-backed config

## API Surface

Discord endpoints:
- `POST /api/discord/webhook`
- `POST /api/discord/invite`
- `GET /api/discord/status`
- `GET /api/discord/instructions`
- `POST /api/discord/test`

## Failure Modes

Common issues:
- invalid webhook format
- invite URL format issues
- Rich Presence unavailable due to desktop app/dependency/config gaps

Recovery guidance:
- validate URL format before save
- verify app ID and dependency for Rich Presence
- use `/api/discord/test` and `/api/discord/status` for verification

## Security Notes

- webhook URL should be treated as sensitive operational secret
- integration sends party/session metadata, not game payload plaintext
- avoid exposing webhook URLs in logs, screenshots, or shared configs

## Testing Focus

Minimum regression scope:
- webhook/invite set and status retrieval
- test-notification endpoint behavior
- presence update/clear behavior under unavailable RPC
- validation helper behavior for URL formats

## Acceptance Criteria

This doc is complete when:
- webhook and presence responsibilities are explicit
- setup/verification path is explicit
- endpoint surface matches API implementation
- failure and security guidance is actionable
