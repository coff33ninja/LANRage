# Discord Rich Presence Setup Guide

This guide will help you set up Discord Rich Presence for LANrage so your Discord status shows what you're playing.

## What is Discord Rich Presence?

Discord Rich Presence allows LANrage to update your Discord status with:
- Current party status ("In Party", "Playing Game", etc.)
- Game details (game name, session duration)
- Party size (e.g., "3 of 8 players")
- Session start time (shows elapsed time)

## Prerequisites

- Discord Desktop App (Rich Presence doesn't work on web/mobile)
- Discord Developer Account (free)
- LANrage v1.2.3 or higher

## Step 1: Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** button (top right)
3. Enter application name: **"LANrage"**
4. Click **"Create"**

## Step 2: Get Your Application ID

1. On the application page, you'll see **"Application ID"** under the app name
2. Click the **"Copy"** button to copy the Application ID
3. Keep this ID handy - you'll need it in Step 4

Example Application ID: `1234567890123456789` (18-19 digits)

## Step 3: Upload LANrage Logo (Optional but Recommended)

To show the LANrage logo in your Discord status:

1. In your Discord application, go to **"Rich Presence"** → **"Art Assets"**
2. Click **"Add Image"**
3. Upload the LANrage logo (`logo.png` from the repository)
4. Name it: **`lanrage_logo`** (exactly this name)
5. Click **"Save Changes"**

**Note**: The logo must be:
- 512x512 pixels minimum
- PNG format
- Named exactly `lanrage_logo` (lowercase, underscore)

## Step 4: Configure LANrage

1. Open LANrage web UI: http://127.0.0.1:8666
2. Go to **Settings** tab
3. Scroll to **Discord Integration** section
4. Paste your Application ID in the **"Discord Application ID"** field
5. Click **"Save Settings"**

## Step 5: Restart LANrage

1. Stop LANrage (Ctrl+C in terminal)
2. Start LANrage again: `python lanrage.py`
3. Look for this message in the console:
   ```
   ✓ Discord Rich Presence connected
   ```

If you see this instead:
```
ℹ Discord Rich Presence not configured (set Discord App ID in settings)
```
Go back to Step 4 and verify your Application ID is correct.

## Step 6: Verify It's Working

1. Open Discord Desktop App
2. Click on your profile (bottom left)
3. You should see **"Playing LANrage"** in your status
4. When you join a party or start a game, the status will update automatically

## Troubleshooting

### "Discord Rich Presence not configured"

**Cause**: Application ID not set or empty

**Solution**: 
- Go to Settings tab
- Enter your Discord Application ID
- Click "Save Settings"
- Restart LANrage

### "Discord Rich Presence failed: [error]"

**Cause**: Discord Desktop App not running or pypresence not installed

**Solution**:
1. Make sure Discord Desktop App is running (not web/mobile)
2. Verify pypresence is installed:
   ```bash
   .venv\Scripts\python.exe -m pip show pypresence
   ```
3. If not installed:
   ```bash
   uv pip install pypresence
   ```

### Status Not Updating

**Cause**: Discord may cache the status

**Solution**:
1. Restart Discord Desktop App
2. Restart LANrage
3. Wait 10-15 seconds for status to update

### "Invalid Application ID"

**Cause**: Application ID is incorrect or contains spaces

**Solution**:
- Application ID should be 18-19 digits
- No spaces or special characters
- Copy directly from Discord Developer Portal

## What Gets Displayed?

### When Idle
```
Playing LANrage
In Menu
```

### When in Party
```
Playing LANrage
In Party: [Party Name]
3 of 8 players
```

### When Playing Game
```
Playing LANrage
Playing: Minecraft
Session: 1h 23m
4 of 8 players
```

## Privacy Note

Discord Rich Presence only shows:
- Party status (in party, playing game)
- Game name (if detected)
- Party size (current/max players)
- Session duration

It does **NOT** show:
- Your IP address
- Peer names or details
- Network information
- Game server details

## Additional Discord Features

LANrage also supports:
- **Discord Webhooks**: Send party notifications to a Discord channel
- **Discord Voice Invite**: Share voice channel invite with party members

See [Discord Integration Guide](DISCORD_SETUP_GUIDE.md) for full setup.

## Need Help?

- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Open an issue on [GitHub](https://github.com/coff33ninja/LANRage/issues)
- Join our Discord community (link in README)

## Example Screenshots

### Discord Developer Portal
![Discord App Setup](https://via.placeholder.com/800x400?text=Discord+Developer+Portal)

### LANrage Settings
![LANrage Settings](https://via.placeholder.com/800x400?text=LANrage+Settings+Tab)

### Discord Status
![Discord Status](https://via.placeholder.com/400x200?text=Discord+Rich+Presence)

---

**Last Updated**: January 31, 2026  
**LANrage Version**: v1.2.3+
