# Discord Integration Clarification

**Date**: January 29, 2026

## Summary

Voice chat, screen sharing, and text chat are **not** planned as built-in LANrage features. Instead, they are provided through **Discord integration**.

---

## Why Discord?

LANrage uses Discord for party communication because:

1. **Best-in-class features**
   - Voice chat: Crystal clear, optimized for gaming
   - Screen sharing: Built-in and reliable
   - Text chat: Full history and formatting
   - File sharing: Seamless integration

2. **No infrastructure needed**
   - Discord handles all hosting
   - No maintenance burden
   - Always reliable (99.99% uptime)

3. **Gamers already use it**
   - Familiar interface
   - No learning curve
   - Works on phone too

4. **Cost savings**
   - Free to use
   - No server costs
   - No bandwidth bills

---

## Features via Discord

### ✅ Voice Chat
- Click "Join Voice Chat" link in LANrage
- Connects to Discord voice channel
- Crystal clear audio
- Low latency

### ✅ Screen Sharing
- Share your screen directly in Discord
- Great for showing game problems
- Troubleshoot together
- Minimal latency

### ✅ Text Chat
- Party notifications in Discord channel
- Discuss game strategy
- Share videos/links
- Search chat history

### ✅ Mobile Support
- Discord app on phone
- Stay connected while AFK
- Mobile voice chat
- Mobile screen sharing

---

## Documentation Updates

The following docs have been updated to clarify this approach:

- **ROADMAP.md** - Voice/screen sharing marked as complete (via Discord)
- **ARCHITECTURE.md** - Removed from future enhancements
- **PARTY.md** - Clarified that Discord provides these
- **SESSION_PROGRESS.md** - Roadmap updated
- **docs/README.md** - Roadmap updated

---

## Implementation Details

### Discord Integration Module
- **File**: `core/discord_integration.py` (316 LOC)
- **Features**:
  - Webhook notifications for party events
  - Rich Presence showing current game
  - Automatic invite link sharing
  - Optional pypresence support

### API Endpoints
- `POST /api/discord/webhook` - Set webhook URL
- `POST /api/discord/invite` - Set invite link
- `GET /api/discord/status` - Get configuration
- `POST /api/discord/test` - Send test notification

### Web UI
- **File**: `static/discord.html`
- Setup wizard for webhook and invite
- One-click configuration
- Test notification button

---

## Why This Is Better Than Alternatives

| Approach | Voice | Screen | Chat | Maintenance | Cost |
|----------|-------|--------|------|-------------|------|
| **Discord Integration** | ✅ | ✅ | ✅ | None | Free |
| Built-in WebRTC | ⚠️ Limited | ❌ Hard | ⚠️ Basic | Complex | High |
| Custom chat | ❌ | ❌ | ✅ | Very Hard | High |
| Mumble/TeamSpeak | ✅ | ❌ | ⚠️ | Complex | Cost |

---

## Conclusion

By integrating with Discord, LANrage provides **best-in-class communication features without the maintenance burden**. This is the right architectural decision for a focused gaming-first VPN.

**Result**: Users get the best voice/screen/chat experience while LANrage stays focused on its core mission: **making gaming feel like a LAN party**.
