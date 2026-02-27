# Discord Setup Guide

Fast path to enable Discord notifications and optional Rich Presence.

## 1. Configure Webhook (Recommended)

1. Create Discord webhook in your target channel.
2. Save it through LANrage settings UI or API.
3. Run test notification endpoint to verify delivery.

Expected result:
- test event appears in target Discord channel.

## 2. Configure Invite Link (Optional)

1. Create long-lived Discord invite for party voice/text entry.
2. Save invite URL through UI/API.
3. Confirm invite link appears in relevant notifications.

## 3. Enable Rich Presence (Optional)

Requirements:
- Discord desktop app running
- Rich Presence dependency installed
- valid Discord app ID configured

Validation:
- check `/api/discord/status`
- verify status reflects active LANrage presence during session

## API Quick Commands

- `POST /api/discord/webhook`
- `POST /api/discord/invite`
- `POST /api/discord/test`
- `GET /api/discord/status`

## Troubleshooting

- no notification: verify webhook URL and channel permissions
- no presence: verify app ID + desktop Discord + dependency
- invalid URL errors: confirm Discord URL formats

## Security

- keep webhook URL private
- rotate webhook if leaked

See also:
- [Discord Integration](/docs/core/integrations/DISCORD.md)
- [Discord App Setup](DISCORD_APP_SETUP.md)
- [Discord Rich Presence Setup](DISCORD_RICH_PRESENCE_SETUP.md)
