# Discord App Setup Guide

This guide walks you through registering LANrage as a Discord application for Rich Presence integration.

## Why Register?

Discord Rich Presence shows your LANrage status in Discord:
- "Playing LANrage"
- Current game and party info
- Number of players in party
- Session duration

## Prerequisites

- Discord account
- LANrage installed with `pypresence` package

## Step-by-Step Registration

### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Name it **"LANrage"**
4. Click **"Create"**

### 2. Get Application ID

1. In your new application, go to **"General Information"**
2. Copy the **"Application ID"** (looks like: `1234567890123456789`)
3. Save this ID - you'll need it later

### 3. Upload Logo Assets

1. In your application, go to **"Rich Presence"** → **"Art Assets"**
2. Click **"Add Image"**
3. Upload your logo:
   - **Name**: `lanrage_logo` (exactly this name)
   - **Image**: 512x512 PNG recommended
   - **Format**: PNG, JPG, or GIF
   - **Max size**: 5MB
4. Click **"Save Changes"**

**Note**: Assets take ~15 minutes to propagate to Discord's CDN.

### 4. Configure LANrage Settings

Set `discord_app_id` in LANrage settings using any supported configuration path:
- Web UI (Settings → Discord Integration)
- Settings API
- Database-backed settings storage

Example value:
```
discord_app_id = "1234567890123456789"
```

### 5. Restart LANrage

```bash
# Stop LANrage if running
# Then start it again
python lanrage.py
```

### 6. Verify It Works

1. Open Discord
2. Start LANrage
3. Verify that the integration status reports Rich Presence as configured:
   - Check `GET /api/discord/status`, or
   - Check startup logs for `✓ Discord Rich Presence connected`
4. Create or join a party
5. Check your Discord profile - you should see:
   - "Playing LANrage"
   - LANrage logo
   - Party/game info

## Troubleshooting

### "Discord Rich Presence not available"

Install pypresence:
```bash
uv pip install pypresence
```

### "Discord Rich Presence failed"

1. Make sure Discord is running
2. Check Application ID is correct
3. Wait 15 minutes after uploading assets
4. Restart both Discord and LANrage

### Logo Not Showing

1. Verify asset name is exactly `lanrage_logo`
2. Wait 15 minutes for CDN propagation
3. Clear Discord cache:
   - Windows: `%AppData%\Discord\Cache`
   - Mac: `~/Library/Application Support/Discord/Cache`
   - Linux: `~/.config/discord/Cache`

### "Connection failed"

Discord RPC requires Discord desktop app (not browser):
- Download from [discord.com](https://discord.com/download)
- Make sure it's running before starting LANrage

## Asset Guidelines

### Logo Specifications

- **Size**: 512x512 pixels (recommended)
- **Format**: PNG with transparency (recommended)
- **Minimum**: 256x256 pixels
- **Maximum**: 1024x1024 pixels
- **File size**: Under 5MB

### Design Tips

- Use transparent background
- Keep design simple and recognizable
- Test at small sizes (Discord shows it at 60x60)
- Use high contrast colors

## Optional: Additional Assets

You can add more assets for different states:

```python
# In discord_integration.py, update_presence():
kwargs = {
    "state": state,
    "large_image": "lanrage_logo",
    "large_text": "LANrage",
    "small_image": "game_icon",  # Add game-specific icons
    "small_text": "Playing Minecraft",
}
```

Upload additional assets with names like:
- `game_minecraft`
- `game_csgo`
- `status_hosting`
- `status_connected`

## Security Notes

- Application ID is public (safe to share)
- Don't share your application token (if you create one)
- Rich Presence doesn't require OAuth or bot permissions

## For Contributors

If you're contributing to LANrage:

1. **Don't commit your Application ID** to the repository
2. Configure `discord_app_id` via settings (UI/API/database), not by editing source files
3. Keep local-only values in a gitignored local config or environment-specific settings management

## Official LANrage App

Once LANrage has an official Discord app, this guide will be updated with the official Application ID. Until then, users need to register their own app.

## Support

- Discord Developer Docs: https://discord.com/developers/docs/rich-presence/how-to
- LANrage Issues: https://github.com/yourusername/lanrage/issues
- Discord API Server: https://discord.gg/discord-api

## Example Rich Presence

```
Playing LANrage
🎮 Minecraft - Survival Mode
👥 3/8 players in party
⏱️ 01:23:45 elapsed
```

This shows:
- Game being played
- Party size and capacity
- Session duration
- Custom status message
