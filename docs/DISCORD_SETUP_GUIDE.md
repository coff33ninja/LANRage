# Discord Setup Guide

**Quick guide for setting up Discord integration with LANrage**

## Why Discord?

Instead of building a custom chat system, LANrage integrates with Discord to provide:
- ✅ Voice chat (already reliable)
- ✅ Text chat with history
- ✅ File sharing
- ✅ Screen sharing
- ✅ Mobile apps
- ✅ No infrastructure costs
- ✅ Familiar interface

## Setup Steps

### 1. Access Discord Setup

Open your browser and navigate to:
```
http://localhost:8666/static/discord.html
```

Or click "💬 DISCORD SETUP" from the main LANrage UI.

### 2. Create Discord Webhook (Required)

**What it does**: Sends notifications when players join, leave, or start games.

**Steps**:
1. Open your Discord server
2. Go to **Server Settings → Integrations**
3. Click **"Create Webhook"** or **"View Webhooks"**
4. Click **"New Webhook"**
5. Name it `LANrage`
6. Select the channel for notifications
7. Copy the **Webhook URL**
8. Paste it in the LANrage Discord setup page
9. Click **"Save Webhook"**
10. Test with **"Send Test"** button

**Example webhook URL**:
```
https://discord.com/api/webhooks/123456789/abcdefghijklmnop
```

### 3. Create Discord Invite (Optional)

**What it does**: Shares a voice channel link with your party members.

**Steps**:
1. Open your Discord server
2. Right-click on a **voice channel**
3. Click **"Invite People"**
4. Click **"Edit Invite Link"**
5. Set **"Expire After"** to `Never`
6. Set **"Max Uses"** to `No Limit`
7. Copy the **invite link**
8. Paste it in the LANrage Discord setup page
9. Click **"Save Invite"**

**Example invite URL**:
```
https://discord.gg/abc123xyz
```

### 4. Enable Rich Presence (Optional)

**What it does**: Shows your LANrage status in Discord.

**Requirements**: `pypresence` package

**Steps**:
1. Activate virtual environment:
   ```bash
   .venv\Scripts\activate.bat  # Windows
   source .venv/bin/activate   # Linux/Mac
   ```

2. Install pypresence:
   ```bash
   uv pip install pypresence
   ```

3. Restart LANrage:
   ```bash
   python lanrage.py
   ```

4. Your Discord status will update automatically!

## Notification Examples

### Party Created
```
🎮 Party Created: Gaming Night
Host: Alice
Party ID: party123

[Join Voice Chat](https://discord.gg/abc123)
```

### Peer Joined
```
👋 Bob joined
Welcome to Gaming Night!
```

### Game Started
```
🎮 Game Started: Minecraft
Players: Alice, Bob, Charlie
```

### Game Ended
```
🏁 Game Ended: Minecraft
Duration: 2h 15m
Avg Latency: 25ms
```

## Troubleshooting

### Webhook not working
- ✅ Verify webhook URL format starts with `https://discord.com/api/webhooks/`
- ✅ Check Discord channel permissions
- ✅ Test with "Send Test" button
- ✅ Check LANrage logs for errors

### Invite link not showing
- ✅ Verify invite URL format starts with `https://discord.gg/`
- ✅ Ensure invite is set to never expire
- ✅ Check that invite has unlimited uses

### Rich Presence not connecting
- ✅ Install pypresence: `uv pip install pypresence`
- ✅ Restart LANrage
- ✅ Check that Discord desktop app is running
- ✅ Verify Discord app ID is registered (future feature)

## Security Notes

- 🔒 Keep webhook URLs private (they allow posting to your channel)
- 🔒 Invite links can be public or private (set expiration/max uses as needed)
- 🔒 No sensitive data is sent to Discord (only party names, peer names, game names)
- 🔒 All communication uses HTTPS

## API Usage

For programmatic control, use the Discord API endpoints:

```bash
# Set webhook
curl -X POST http://localhost:8666/api/discord/webhook \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://discord.com/api/webhooks/..."}'

# Set invite
curl -X POST http://localhost:8666/api/discord/invite \
  -H "Content-Type: application/json" \
  -d '{"invite_url": "https://discord.gg/..."}'

# Get status
curl http://localhost:8666/api/discord/status

# Send test notification
curl -X POST http://localhost:8666/api/discord/test
```

## Related Documentation

- [Discord Integration](DISCORD.md) - Full technical documentation
- [Settings System](SETTINGS.md) - Configuration management
- [Statistics Dashboard](METRICS.md) - Metrics and monitoring

## Need Help?

- Check [Discord Integration](DISCORD.md) for detailed documentation
- Open an issue on GitHub
- Ask in the LANrage community
