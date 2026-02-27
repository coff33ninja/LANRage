# Discord Rich Presence Setup

Configure LANrage Rich Presence with your Discord application.

## Prerequisites

- Discord desktop app
- Rich Presence dependency installed
- Discord developer application created

## Steps

1. Create Discord application in developer portal.
2. Copy application ID.
3. Configure `discord_app_id` in LANrage settings.
4. Restart LANrage runtime.
5. Verify with `/api/discord/status` and live Discord profile presence.

## Optional Art Assets

Add app art assets for better presentation. Keep asset names consistent with presence update fields used by LANrage.

## Common Failures

- missing app ID -> presence disabled
- desktop Discord not running -> RPC connect failure
- dependency missing -> presence unavailable

## Verification Checklist

- status endpoint shows configured app ID
- presence appears while LANrage session is active
- presence clears correctly when session ends

See also:
- [Discord Integration](/docs/core/integrations/DISCORD.md)
- [Discord App Setup](DISCORD_APP_SETUP.md)
