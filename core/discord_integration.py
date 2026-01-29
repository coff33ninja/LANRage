"""Discord integration for party chat and presence"""

import sys
import time
from typing import Optional

import aiohttp

from .config import Config


class DiscordIntegration:
    """Integrates LANrage with Discord for chat and presence"""

    def __init__(self, config: Config):
        self.config = config
        self.webhook_url: Optional[str] = None
        self.party_invite_url: Optional[str] = None
        self.session = None
        self.running = False

        # Discord Rich Presence (if pypresence is available)
        self.rpc = None
        self.rpc_connected = False

    async def start(self):
        """Start Discord integration"""
        self.running = True
        self.session = aiohttp.ClientSession()

        # Try to connect Rich Presence
        await self._connect_rich_presence()

    async def stop(self):
        """Stop Discord integration"""
        self.running = False

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

            self.rpc = Presence(discord_app_id)
            self.rpc.connect()
            self.rpc_connected = True
            print("✓ Discord Rich Presence connected")
        except ImportError:
            print("ℹ Discord Rich Presence not available (install pypresence)")
        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Discord Rich Presence failed: {error_msg}")

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
        """Send notification to Discord webhook

        Args:
            title: Notification title
            message: Notification message
            color: Embed color (default: LANrage purple)
        """
        if not self.webhook_url:
            return

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
                    print(f"⚠ Discord webhook failed: {error_text}")

        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Discord notification failed: {error_msg}")

    async def notify_party_created(self, party_id: str, party_name: str, host: str):
        """Notify that a party was created"""
        message = f"**Host**: {host}\n**Party ID**: `{party_id}`"

        if self.party_invite_url:
            message += f"\n\n[Join Voice Chat]({self.party_invite_url})"

        await self.send_notification(
            f"🎮 Party Created: {party_name}", message, color=0x4CAF50
        )

    async def notify_peer_joined(self, peer_name: str, party_name: str):
        """Notify that a peer joined the party"""
        await self.send_notification(
            f"👋 {peer_name} joined",
            f"Welcome to **{party_name}**!",
            color=0x2196F3,
        )

    async def notify_peer_left(self, peer_name: str, party_name: str):
        """Notify that a peer left the party"""
        await self.send_notification(
            f"👋 {peer_name} left", f"Left **{party_name}**", color=0xFF9800
        )

    async def notify_game_started(self, game_name: str, players: list):
        """Notify that a game session started"""
        player_list = ", ".join(players)
        await self.send_notification(
            f"🎮 Game Started: {game_name}",
            f"**Players**: {player_list}",
            color=0x9C27B0,
        )

    async def notify_game_ended(
        self, game_name: str, duration: float, avg_latency: Optional[float]
    ):
        """Notify that a game session ended"""
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
        details: Optional[str] = None,
        party_size: Optional[tuple] = None,
        start_time: Optional[int] = None,
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

            self.rpc.update(**kwargs)

        except Exception as e:
            error_msg = str(e)
            print(f"⚠ Discord presence update failed: {error_msg}")

    async def clear_presence(self):
        """Clear Discord Rich Presence"""
        if self.rpc and self.rpc_connected:
            try:
                self.rpc.clear()
            except OSError as e:
                # Discord RPC clear is optional, log but don't fail
                print(f"Debug: Discord RPC clear failed: {e}", file=sys.stderr)
            except Exception as e:
                # Catch any other unexpected errors
                print(
                    f"Debug: Unexpected error clearing Discord RPC: {e}",
                    file=sys.stderr,
                )

    def get_party_invite_link(self) -> Optional[str]:
        """Get Discord party invite link"""
        return self.party_invite_url

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
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
async def quick_discord_setup(webhook_url: str, invite_url: Optional[str] = None):
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
