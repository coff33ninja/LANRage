# Discord Integration

The Discord integration (`core/discord_integration.py`) provides party chat notifications, Rich Presence, and voice chat coordination through Discord webhooks and the Discord RPC API.

## Overview

LANrage integrates with Discord to provide:
- **Webhook Notifications**: Party events, peer joins/leaves, game sessions
- **Rich Presence**: Show current party/game status in Discord profile
- **Voice Chat Links**: Automatic Discord voice channel invites
- **Game Session Stats**: Post-game statistics to Discord channels

---

## Classes

### DiscordIntegration

Main Discord integration class.

#### Initialization

```python
from core.config import Config
from core.discord_integration import DiscordIntegration

config = await Config.load()
discord = DiscordIntegration(config)
```

**Parameters:**
- `config` (Config): LANrage configuration

**Attributes:**
- `webhook_url` (Optional[str]): Discord webhook URL for notifications
- `party_invite_url` (Optional[str]): Discord server/channel invite URL
- `session` (aiohttp.ClientSession): HTTP session for webhook requests
- `rpc` (Presence): Discord Rich Presence client (if pypresence installed)
- `rpc_connected` (bool): Whether Rich Presence is connected

---

### Methods

#### start()

Start Discord integration.

```python
await discord.start()
```

**Behavior:**
- Creates aiohttp session for webhook requests
- Attempts to connect Discord Rich Presence (requires pypresence)
- Prints connection status

**Returns:** None

**Output:**
- `✓ Discord Rich Presence connected` - If pypresence available and connected
- `ℹ Discord Rich Presence not available (install pypresence)` - If pypresence not installed
- `⚠ Discord Rich Presence failed: <error>` - If connection failed

---

#### stop()

Stop Discord integration.

```python
await discord.stop()
```

**Behavior:**
- Closes aiohttp session
- Disconnects Rich Presence (if connected)
- Handles cleanup errors gracefully

**Returns:** None

---

#### set_webhook(webhook_url)

Set Discord webhook URL for notifications.

```python
discord.set_webhook("https://discord.com/api/webhooks/123456789/abcdefg")
```

**Parameters:**
- `webhook_url` (str): Discord webhook URL from channel settings

**Behavior:**
- Stores webhook URL for future notifications
- Prints confirmation message

**Returns:** None

**How to Get Webhook URL:**
1. Open Discord server
2. Go to Server Settings → Integrations
3. Click "Create Webhook" or "View Webhooks"
4. Click "New Webhook"
5. Name it "LANrage"
6. Select notification channel
7. Copy Webhook URL

---

#### set_party_invite(invite_url)

Set Discord server/channel invite URL.

```python
discord.set_party_invite("https://discord.gg/abc123")
```

**Parameters:**
- `invite_url` (str): Discord invite link

**Behavior:**
- Stores invite URL for inclusion in notifications
- Prints confirmation message

**Returns:** None

**How to Get Invite URL:**
1. Open Discord server
2. Right-click voice channel
3. Click "Invite People"
4. Click "Edit Invite Link"
5. Set "Expire After" to "Never"
6. Set "Max Uses" to "No Limit"
7. Copy invite link

---

#### send_notification(title, message, color)

Send notification to Discord webhook.

```python
await discord.send_notification(
    title="Party Created",
    message="Join the party!",
    color=0x4CAF50  # Green
)
```

**Parameters:**
- `title` (str): Notification title
- `message` (str): Notification message
- `color` (int): Embed color in hex (default: 0x667EEA = LANrage purple)

**Behavior:**
- Creates Discord embed with title, message, color, timestamp
- Sends to configured webhook URL
- Handles errors gracefully (prints warning on failure)

**Returns:** None

**Color Codes:**
- `0x4CAF50` - Green (success)
- `0x2196F3` - Blue (info)
- `0xFF9800` - Orange (warning)
- `0x9C27B0` - Purple (game events)
- `0x607D8B` - Gray (neutral)
- `0x667EEA` - LANrage purple (default)

---

#### notify_party_created(party_id, party_name, host)

Notify that a party was created.

```python
await discord.notify_party_created(
    party_id="party-123",
    party_name="Friday Night Gaming",
    host="Alice"
)
```

**Parameters:**
- `party_id` (str): Unique party identifier
- `party_name` (str): Human-readable party name
- `host` (str): Host peer name

**Behavior:**
- Sends green embed with party details
- Includes party ID for joining
- Includes voice chat link if configured

**Returns:** None

---

#### notify_peer_joined(peer_name, party_name)

Notify that a peer joined the party.

```python
await discord.notify_peer_joined("Bob", "Friday Night Gaming")
```

**Parameters:**
- `peer_name` (str): Peer name
- `party_name` (str): Party name

**Behavior:**
- Sends blue embed with welcome message

**Returns:** None

---

#### notify_peer_left(peer_name, party_name)

Notify that a peer left the party.

```python
await discord.notify_peer_left("Bob", "Friday Night Gaming")
```

**Parameters:**
- `peer_name` (str): Peer name
- `party_name` (str): Party name

**Behavior:**
- Sends orange embed with departure message

**Returns:** None

---

#### notify_game_started(game_name, players)

Notify that a game session started.

```python
await discord.notify_game_started(
    game_name="Minecraft",
    players=["Alice", "Bob", "Charlie"]
)
```

**Parameters:**
- `game_name` (str): Game name
- `players` (list): List of player names

**Behavior:**
- Sends purple embed with game name and player list

**Returns:** None

---

#### notify_game_ended(game_name, duration, avg_latency)

Notify that a game session ended.

```python
await discord.notify_game_ended(
    game_name="Minecraft",
    duration=3600.0,  # 1 hour
    avg_latency=45.2  # 45.2ms
)
```

**Parameters:**
- `game_name` (str): Game name
- `duration` (float): Session duration in seconds
- `avg_latency` (Optional[float]): Average latency in milliseconds

**Behavior:**
- Sends gray embed with session statistics
- Formats duration as human-readable (e.g., "1h 30m")
- Includes average latency if available

**Returns:** None

---

#### update_presence(state, details, party_size, start_time)

Update Discord Rich Presence.

```python
await discord.update_presence(
    state="In Party",
    details="Playing Minecraft",
    party_size=(3, 8),  # 3 of 8 players
    start_time=1706544000  # Unix timestamp
)
```

**Parameters:**
- `state` (str): Current state (e.g., "In Party", "In Game")
- `details` (Optional[str]): Additional details (e.g., game name)
- `party_size` (Optional[tuple]): Tuple of (current, max) party size
- `start_time` (Optional[int]): Unix timestamp of session start

**Behavior:**
- Updates Discord profile with LANrage activity
- Shows party size and elapsed time
- Requires pypresence and Discord app registration

**Returns:** None

**Note:** Requires `discord_app_id` to be set in LANrage settings (UI/API/database-backed settings).

---

#### clear_presence()

Clear Discord Rich Presence.

```python
await discord.clear_presence()
```

**Behavior:**
- Removes LANrage activity from Discord profile
- Handles errors gracefully

**Returns:** None

---

#### get_party_invite_link()

Get Discord party invite link.

```python
invite_url = discord.get_party_invite_link()
```

**Returns:** Optional[str] - Discord invite URL or None if not configured

---

### DiscordWebhookHelper

Helper class for Discord webhook setup and validation.

#### Static Methods

##### get_webhook_instructions()

Get instructions for creating a Discord webhook.

```python
from core.discord_integration import DiscordWebhookHelper

instructions = DiscordWebhookHelper.get_webhook_instructions()
print(instructions)
```

**Returns:** str - Multi-line instructions for webhook setup

---

##### get_invite_instructions()

Get instructions for creating a Discord invite.

```python
instructions = DiscordWebhookHelper.get_invite_instructions()
print(instructions)
```

**Returns:** str - Multi-line instructions for invite setup

---

##### validate_webhook_url(url)

Validate Discord webhook URL format.

```python
is_valid = DiscordWebhookHelper.validate_webhook_url(
    "https://discord.com/api/webhooks/123456789/abcdefg"
)
```

**Parameters:**
- `url` (str): URL to validate

**Returns:** bool - True if valid webhook URL format

**Valid Formats:**
- `https://discord.com/api/webhooks/...`
- `https://discordapp.com/api/webhooks/...`

---

##### validate_invite_url(url)

Validate Discord invite URL format.

```python
is_valid = DiscordWebhookHelper.validate_invite_url("https://discord.gg/abc123")
```

**Parameters:**
- `url` (str): URL to validate

**Returns:** bool - True if valid invite URL format

**Valid Formats:**
- `https://discord.gg/...`
- `https://discord.com/invite/...`

---

## Quick Setup Function

### quick_discord_setup(webhook_url, invite_url)

Quick setup for Discord integration.

```python
from core.discord_integration import quick_discord_setup

discord = await quick_discord_setup(
    webhook_url="https://discord.com/api/webhooks/123456789/abcdefg",
    invite_url="https://discord.gg/abc123"  # Optional
)
```

**Parameters:**
- `webhook_url` (str): Discord webhook URL
- `invite_url` (Optional[str]): Discord invite URL

**Returns:** DiscordIntegration - Configured and started instance

---

## Usage Examples

### Basic Setup

```python
from core.config import Config
from core.discord_integration import DiscordIntegration

# Initialize
config = await Config.load()
discord = DiscordIntegration(config)

# Start integration
await discord.start()

# Configure webhook
discord.set_webhook("https://discord.com/api/webhooks/123456789/abcdefg")
discord.set_party_invite("https://discord.gg/abc123")

# Send test notification
await discord.send_notification(
    "Test Notification",
    "Discord integration is working!",
    color=0x4CAF50
)

# Stop integration
await discord.stop()
```

### Party Notifications

```python
# Party created
await discord.notify_party_created(
    party_id="party-123",
    party_name="Friday Night Gaming",
    host="Alice"
)

# Peer joined
await discord.notify_peer_joined("Bob", "Friday Night Gaming")

# Peer left
await discord.notify_peer_left("Bob", "Friday Night Gaming")
```

### Game Session Tracking

```python
# Game started
await discord.notify_game_started(
    game_name="Minecraft",
    players=["Alice", "Bob", "Charlie"]
)

# Update Rich Presence
await discord.update_presence(
    state="In Game",
    details="Minecraft",
    party_size=(3, 8),
    start_time=int(time.time())
)

# Game ended
await discord.notify_game_ended(
    game_name="Minecraft",
    duration=3600.0,
    avg_latency=45.2
)

# Clear Rich Presence
await discord.clear_presence()
```

### Validation

```python
from core.discord_integration import DiscordWebhookHelper

# Validate URLs
webhook_url = "https://discord.com/api/webhooks/123456789/abcdefg"
invite_url = "https://discord.gg/abc123"

if DiscordWebhookHelper.validate_webhook_url(webhook_url):
    discord.set_webhook(webhook_url)

if DiscordWebhookHelper.validate_invite_url(invite_url):
    discord.set_party_invite(invite_url)
```

---

## Integration with API

The Discord integration is exposed through the REST API (`api/server.py`):

### Endpoints

- `POST /api/discord/webhook` - Set webhook URL
- `POST /api/discord/invite` - Set invite URL
- `GET /api/discord/status` - Get integration status
- `GET /api/discord/instructions` - Get setup instructions
- `POST /api/discord/test` - Send test notification

See `docs/API.md` for full API documentation.

---

## Dependencies

### Required

- `aiohttp` - HTTP client for webhook requests

### Optional

- `pypresence` - Discord Rich Presence support

**Install pypresence:**
```bash
uv pip install pypresence
```

---

## Discord Application Setup

For Rich Presence to work, you need to register a Discord application:

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it "LANrage"
4. Go to "Rich Presence" → "Art Assets"
5. Upload LANrage logo as "lanrage_logo"
6. Copy Application ID
7. Set `discord_app_id` in LANrage settings (via UI, settings API, or database-backed settings).
8. Verify configuration by checking `GET /api/discord/status` for enabled Rich Presence or the startup log line:
   - `✓ Discord Rich Presence connected`
   - `ℹ Discord Rich Presence not configured (set Discord App ID in settings)`

---

## Error Handling

All Discord operations handle errors gracefully:

- **Webhook Failures**: Print warning, continue operation
- **Rich Presence Failures**: Print warning, disable Rich Presence
- **Network Errors**: Retry not implemented (fire-and-forget)

No Discord errors will crash LANrage or interrupt gameplay.

---

## Future Enhancements

1. **Slash Commands**: Discord bot for party management
2. **Voice Activity**: Detect voice channel activity
3. **Automatic Invites**: Auto-generate invite links
4. **Rich Presence Images**: Dynamic game-specific images
5. **Spectator Mode**: Discord users can spectate games
6. **Replay Sharing**: Share game replays to Discord
7. **Leaderboards**: Post leaderboards to Discord channels
8. **Scheduled Events**: Discord event integration
