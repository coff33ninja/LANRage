"""Discord integration for party chat and presence"""

import asyncio
import contextlib
import sys
import time
from collections import deque
from dataclasses import dataclass

import aiohttp

from .config import Config
from .logging_config import get_logger, set_context, timing_decorator

logger = get_logger(__name__)


@dataclass
class NotificationMessage:
    """A queued notification message"""

    title: str
    description: str
    color: int
    timestamp: float


class NotificationBatcher:
    """Batches Discord notifications to reduce API calls

    Groups similar notifications within a time window (e.g., multiple
    peer joins) into a single message to reduce Discord API traffic.
    """

    def __init__(self, batch_interval_ms: float = 500.0):
        """Initialize notification batcher

        Args:
            batch_interval_ms: Time window to collect notifications (milliseconds)
        """
        self.batch_interval = batch_interval_ms / 1000.0
        self.pending_notifications: deque[NotificationMessage] = deque()
        self.last_flush_time = time.time()
        self.flush_lock = asyncio.Lock()

    async def queue_notification(
        self, title: str, description: str, color: int
    ) -> bool:
        """Queue a notification for batched sending

        Returns:
            True if notification was queued, False if should send immediately
        """
        current_time = time.time()
        time_since_flush = current_time - self.last_flush_time

        self.pending_notifications.append(
            NotificationMessage(title, description, color, current_time)
        )

        # Send immediately if batch interval exceeded
        return time_since_flush < self.batch_interval  # Queue if within interval

    async def flush(self) -> list[NotificationMessage]:
        """Get pending notifications and reset batch

        Returns:
            List of pending notifications
        """
        async with self.flush_lock:
            notifications = list(self.pending_notifications)
            self.pending_notifications.clear()
            self.last_flush_time = time.time()
            return notifications

    def get_pending_count(self) -> int:
        """Get count of pending notifications"""
        return len(self.pending_notifications)


class DiscordIntegration:
    """Integrates LANrage with Discord for chat and presence"""

    def __init__(self, config: Config):
        self.config = config
        self.webhook_url: str | None = None
        self.party_invite_url: str | None = None
        self.session = None
        self.running = False

        # Notification batching (500ms batch window)
        self.notification_batcher = NotificationBatcher(batch_interval_ms=500.0)
        self.batch_flush_task: asyncio.Task | None = None

        # Discord Rich Presence (if pypresence is available)
        self.rpc = None
        self.rpc_connected = False

        # Discord Bot (if discord.py is available)
        self.bot = None
        self.bot_connected = False
        self.bot_task: asyncio.Task | None = None

    @timing_decorator(name="discord_start")
    async def start(self):
        """Start Discord integration"""
        logger.info("Starting Discord integration")
        self.running = True
        self.session = aiohttp.ClientSession()

        # Load Discord settings from database
        from .settings import get_settings_db

        db = await get_settings_db()
        discord_webhook = await db.get_setting("discord_webhook", "")
        discord_invite = await db.get_setting("discord_invite", "")

        # Set webhook and invite if configured
        if discord_webhook:
            self.set_webhook(discord_webhook)
        if discord_invite:
            self.set_party_invite(discord_invite)

        # Try to connect Rich Presence
        await self._connect_rich_presence()

        # Try to connect Discord bot
        await self._connect_bot()

        # Start batch flush task for notifications (every 500ms)
        self.batch_flush_task = asyncio.create_task(self._batch_flush_loop())
        logger.info("Discord integration started")

    @timing_decorator(name="discord_stop")
    async def stop(self):
        """Stop Discord integration"""
        logger.info("Stopping Discord integration")
        self.running = False

        # Cancel batch flush task
        if self.batch_flush_task:
            self.batch_flush_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.batch_flush_task

        # Final flush of pending notifications
        await self._flush_pending_notifications()

        # Stop Discord bot
        if self.bot and self.bot_connected:
            try:
                await self.bot.close()
                self.bot_connected = False
                print("✓ Discord bot disconnected")
            except Exception as e:
                print(f"Debug: Discord bot cleanup failed: {e}", file=sys.stderr)

        # Cancel bot task
        if self.bot_task:
            self.bot_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.bot_task

        if self.session:
            await self.session.close()

        if self.rpc and self.rpc_connected:
            try:
                self.rpc.close()
            except OSError as e:
                # Discord RPC cleanup is optional, log but don't fail
                print(f"Debug: Discord RPC cleanup failed: {e}", file=sys.stderr)
            except Exception as e:
                # Catch any other unexpected errors
                print(
                    f"Debug: Unexpected error closing Discord RPC: {e}", file=sys.stderr
                )

    async def _batch_flush_loop(self):
        """Background task to periodically flush batched notifications"""
        try:
            while self.running:
                await asyncio.sleep(self.notification_batcher.batch_interval)
                await self._flush_pending_notifications()
        except asyncio.CancelledError:
            pass

    async def _flush_pending_notifications(self):
        """Send all pending batched notifications"""
        notifications = await self.notification_batcher.flush()

        if not notifications:
            return

        # If multiple notifications, combine them into one message
        if len(notifications) > 1:
            # Group by type and create summary
            combined_title = f"📋 {len(notifications)} Events"
            combined_desc = "\n".join([f"• {n.title}" for n in notifications])
            await self._send_webhook(combined_title, combined_desc, color=0x757575)
        else:
            # Single notification, send as-is
            n = notifications[0]
            await self._send_webhook(n.title, n.description, color=n.color)

    async def _connect_rich_presence(self):
        """Connect to Discord Rich Presence"""
        try:
            from pypresence import Presence

            # Load Discord app ID from settings
            from .settings import get_settings_db

            db = await get_settings_db()
            discord_app_id = await db.get_setting("discord_app_id", "")

            if not discord_app_id:
                print(
                    "ℹ Discord Rich Presence not configured (set Discord App ID in settings)"
                )
                return

            # Run pypresence connection in thread pool to avoid event loop conflicts
            loop = asyncio.get_event_loop()

            def connect_rpc():
                """Connect to Discord RPC in a separate thread"""
                rpc = Presence(discord_app_id)
                rpc.connect()
                return rpc

            # Run blocking RPC connection in executor
            self.rpc = await loop.run_in_executor(None, connect_rpc)
            self.rpc_connected = True
            print("✓ Discord Rich Presence connected")
        except ImportError:
            print("ℹ Discord Rich Presence not available (install pypresence)")
        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Discord Rich Presence failed: {error_msg}")

    async def _connect_bot(self):
        """Connect Discord bot for online presence"""
        try:
            import discord

            # Load Discord bot settings from database
            from .settings import get_settings_db

            db = await get_settings_db()
            bot_token = await db.get_setting("discord_bot_token", "")
            channel_id = await db.get_setting("discord_channel_id", "")

            if not bot_token:
                print("ℹ Discord bot not configured (set bot token in settings)")
                return

            # Create bot with minimal intents
            intents = discord.Intents.default()
            intents.message_content = False  # Don't need message content
            intents.guilds = True  # Need guild info
            intents.guild_messages = True  # Need to send messages

            self.bot = discord.Client(intents=intents)
            self.bot_channel_id = int(channel_id) if channel_id else None

            @self.bot.event
            async def on_ready():
                """Bot connected successfully"""
                self.bot_connected = True
                print(f"✓ Discord bot connected as {self.bot.user}")

                # Send startup message if channel configured
                if self.bot_channel_id:
                    try:
                        channel = self.bot.get_channel(self.bot_channel_id)
                        if channel:
                            await channel.send("🎮 LANrage bot is now online!")
                    except Exception as e:
                        print(f"⚠ Failed to send bot startup message: {e}")

            @self.bot.event
            async def on_disconnect():
                """Bot disconnected"""
                self.bot_connected = False
                print("⚠ Discord bot disconnected")

            # Start bot in background task
            self.bot_task = asyncio.create_task(self._run_bot(bot_token))

        except ImportError:
            print("ℹ Discord bot not available (install discord.py)")
        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Discord bot connection failed: {error_msg}")

    async def _run_bot(self, token: str):
        """Run Discord bot in background"""
        try:
            await self.bot.start(token)
        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Discord bot error: {error_msg}")
            self.bot_connected = False

    def set_webhook(self, webhook_url: str):
        """Set Discord webhook URL for notifications

        Args:
            webhook_url: Discord webhook URL from channel settings
        """
        self.webhook_url = webhook_url
        print("✓ Discord webhook configured")

    def set_party_invite(self, invite_url: str):
        """Set Discord server/channel invite URL

        Args:
            invite_url: Discord invite link (e.g., https://discord.gg/abc123)
        """
        self.party_invite_url = invite_url
        print(f"✓ Discord party invite set: {invite_url}")

    async def send_notification(self, title: str, message: str, color: int = 0x667EEA):
        """Queue notification for batched sending to Discord webhook

        Args:
            title: Notification title
            message: Notification message
            color: Embed color (default: LANrage purple)
        """
        if not self.webhook_url:
            return

        set_context(correlation_id_val=f"discord_notification_{title[:30]}")
        logger.debug(f"Queueing Discord notification: {title}")

        # Queue notification for batching
        should_send_immediate = not await self.notification_batcher.queue_notification(
            title, message, color
        )

        # If batch interval exceeded, send immediately
        if should_send_immediate:
            await self._send_webhook(title, message, color)

    async def send_bot_message(self, message: str):
        """Send message via Discord bot to configured channel

        Args:
            message: Message to send
        """
        if not self.bot or not self.bot_connected or not self.bot_channel_id:
            return

        set_context(correlation_id_val=f"discord_bot_{self.bot_channel_id}")
        logger.debug(f"Sending Discord bot message: {message[:50]}")

        try:
            channel = self.bot.get_channel(self.bot_channel_id)
            if channel:
                await channel.send(message)
                logger.debug("Discord bot message sent successfully")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send bot message: {error_msg}")

    async def _send_webhook(self, title: str, message: str, color: int = 0x667EEA):
        """Send notification directly to Discord webhook

        Args:
            title: Notification title
            message: Notification message
            color: Embed color
        """
        if not self.webhook_url:
            return

        set_context(correlation_id_val=f"discord_webhook_{title[:30]}")

        try:
            embed = {
                "title": title,
                "description": message,
                "color": color,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "footer": {"text": "LANrage"},
            }

            payload = {"embeds": [embed]}

            async with self.session.post(self.webhook_url, json=payload) as response:
                if response.status != 204:
                    error_text = await response.text()
                    logger.warning(f"Discord webhook failed: {error_text}")
                else:
                    logger.debug(f"Discord webhook sent: {title}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Discord notification failed: {error_msg}")

    async def notify_party_created(self, party_id: str, party_name: str, host: str):
        """Notify that a party was created"""
        set_context(party_id_val=party_id)
        logger.info(f"Notifying party created: {party_name} (ID: {party_id})")

        message = f"**Host**: {host}\n**Party ID**: `{party_id}`"

        if self.party_invite_url:
            message += f"\n\n[Join Voice Chat]({self.party_invite_url})"

        await self.send_notification(
            f"🎮 Party Created: {party_name}", message, color=0x4CAF50
        )

    async def notify_peer_joined(self, peer_name: str, party_name: str):
        """Notify that a peer joined the party"""
        set_context(correlation_id_val=f"discord_peer_join_{peer_name}")
        logger.info(f"Notifying peer joined: {peer_name} to {party_name}")

        await self.send_notification(
            f"👋 {peer_name} joined",
            f"Welcome to **{party_name}**!",
            color=0x2196F3,
        )

    async def notify_peer_left(self, peer_name: str, party_name: str):
        """Notify that a peer left the party"""
        set_context(correlation_id_val=f"discord_peer_leave_{peer_name}")
        logger.info(f"Notifying peer left: {peer_name} from {party_name}")

        await self.send_notification(
            f"👋 {peer_name} left", f"Left **{party_name}**", color=0xFF9800
        )

    async def notify_game_started(self, game_name: str, players: list):
        """Notify that a game session started"""
        set_context(game_id_val=game_name)
        logger.info(f"Notifying game started: {game_name} with {len(players)} players")

        player_list = ", ".join(players)
        await self.send_notification(
            f"🎮 Game Started: {game_name}",
            f"**Players**: {player_list}",
            color=0x9C27B0,
        )

    async def notify_game_ended(
        self, game_name: str, duration: float, avg_latency: float | None
    ):
        """Notify that a game session ended"""
        set_context(game_id_val=game_name)
        logger.info(
            f"Notifying game ended: {game_name} (duration: {duration:.1f}s, latency: {avg_latency or 'N/A'}ms)"
        )

        duration_str = self._format_duration(duration)
        latency_str = f"{avg_latency:.0f}ms" if avg_latency else "N/A"

        await self.send_notification(
            f"🏁 Game Ended: {game_name}",
            f"**Duration**: {duration_str}\n**Avg Latency**: {latency_str}",
            color=0x607D8B,
        )

    async def update_presence(
        self,
        state: str,
        details: str | None = None,
        party_size: tuple | None = None,
        start_time: int | None = None,
    ):
        """Update Discord Rich Presence

        Args:
            state: Current state (e.g., "In Party")
            details: Additional details (e.g., game name)
            party_size: Tuple of (current, max) party size
            start_time: Unix timestamp of session start
        """
        if not self.rpc or not self.rpc_connected:
            return

        set_context(correlation_id_val=f"discord_presence_{state}")
        logger.debug(
            f"Updating Discord presence: {state}",
            extra={"details": details, "party_size": party_size},
        )

        try:
            kwargs = {
                "state": state,
                "large_image": "lanrage_logo",  # Asset name uploaded to Discord Developer Portal
                "large_text": "LANrage",
                # Note: Asset must be uploaded at https://discord.com/developers/applications
                # Go to your app → Rich Presence → Art Assets → Add Image
                # Name it "lanrage_logo" and upload a 512x512 PNG
            }

            if details:
                kwargs["details"] = details

            if party_size:
                kwargs["party_size"] = party_size

            if start_time:
                kwargs["start"] = start_time

            # Run RPC update in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.rpc.update(**kwargs))
            logger.debug("Discord presence updated successfully")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Discord presence update failed: {error_msg}")

    async def clear_presence(self):
        """Clear Discord Rich Presence"""
        if self.rpc and self.rpc_connected:
            set_context(correlation_id_val="discord_presence_clear")
            logger.debug("Clearing Discord presence")

            try:
                # Run RPC clear in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.rpc.clear)
                logger.debug("Discord presence cleared successfully")
            except OSError as e:
                # Discord RPC clear is optional, log but don't fail
                logger.warning(f"Discord RPC clear failed: {e}")
            except Exception as e:
                # Catch any other unexpected errors
                logger.warning(f"Unexpected error clearing Discord RPC: {e}")

    def get_party_invite_link(self) -> str | None:
        """Get Discord party invite link"""
        return self.party_invite_url

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"


class DiscordWebhookHelper:
    """Helper for creating Discord webhooks"""

    @staticmethod
    def get_webhook_instructions() -> str:
        """Get instructions for creating a Discord webhook"""
        return """
To set up Discord notifications:

1. Open your Discord server
2. Go to Server Settings → Integrations
3. Click "Create Webhook" or "View Webhooks"
4. Click "New Webhook"
5. Name it "LANrage"
6. Select the channel for notifications
7. Copy the Webhook URL
8. Paste it in LANrage settings

Example webhook URL:
https://discord.com/api/webhooks/123456789/abcdefghijklmnop
"""

    @staticmethod
    def get_invite_instructions() -> str:
        """Get instructions for creating a Discord invite"""
        return """
To set up Discord voice chat:

1. Open your Discord server
2. Right-click on a voice channel
3. Click "Invite People"
4. Click "Edit Invite Link"
5. Set "Expire After" to "Never"
6. Set "Max Uses" to "No Limit"
7. Copy the invite link
8. Paste it in LANrage settings

Example invite URL:
https://discord.gg/abc123xyz
"""

    @staticmethod
    def validate_webhook_url(url: str) -> bool:
        """Validate Discord webhook URL format"""
        return url.startswith("https://discord.com/api/webhooks/") or url.startswith(
            "https://discordapp.com/api/webhooks/"
        )

    @staticmethod
    def validate_invite_url(url: str) -> bool:
        """Validate Discord invite URL format"""
        return url.startswith("https://discord.gg/") or url.startswith(
            "https://discord.com/invite/"
        )


# Quick setup helper
async def quick_discord_setup(webhook_url: str, invite_url: str | None = None):
    """Quick setup for Discord integration

    Args:
        webhook_url: Discord webhook URL
        invite_url: Optional Discord invite URL

    Returns:
        Configured DiscordIntegration instance
    """
    from .config import Config

    config = Config.load()
    discord = DiscordIntegration(config)

    await discord.start()
    discord.set_webhook(webhook_url)

    if invite_url:
        discord.set_party_invite(invite_url)

    return discord
