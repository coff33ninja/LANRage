# Discord App Setup

Register and configure a Discord application for LANrage Rich Presence.

## Steps

1. Open Discord developer portal and create app.
2. Capture application ID.
3. Configure Rich Presence assets (optional but recommended).
4. Set `discord_app_id` in LANrage settings.
5. restart LANrage and verify status.

## Asset Guidance

- use a stable logo asset name used by LANrage presence payloads
- allow propagation time after upload before testing

## Operational Notes

- application ID is safe to store as config value
- avoid storing bot tokens/secrets in project docs/config unless explicitly needed

See also:
- [Discord Rich Presence Setup](DISCORD_RICH_PRESENCE_SETUP.md)
- [Discord Integration](/docs/core/integrations/DISCORD.md)
