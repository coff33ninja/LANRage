"""Tests for Discord integration"""

import pytest
import pytest_asyncio

from core.config import Config
from core.discord_integration import DiscordIntegration, DiscordWebhookHelper


@pytest_asyncio.fixture
async def discord():
    """Create a Discord integration instance"""
    config = await Config.load()
    discord = DiscordIntegration(config)
    await discord.start()
    yield discord
    await discord.stop()


@pytest.mark.asyncio
async def test_discord_initialization(discord):
    """Test Discord integration initialization"""
    assert discord.running is True
    assert discord.session is not None
    # webhook_url and party_invite_url may be loaded from database if configured
    # Just verify initialization works without asserting specific states
    assert isinstance(discord.webhook_url, (str, type(None)))
    assert isinstance(discord.party_invite_url, (str, type(None)))


@pytest.mark.asyncio
async def test_set_webhook(discord):
    """Test setting webhook URL"""
    webhook_url = "https://discord.com/api/webhooks/123456789/abcdefg"
    discord.set_webhook(webhook_url)
    assert discord.webhook_url == webhook_url


@pytest.mark.asyncio
async def test_set_party_invite(discord):
    """Test setting party invite URL"""
    invite_url = "https://discord.gg/abc123"
    discord.set_party_invite(invite_url)
    assert discord.party_invite_url == invite_url


@pytest.mark.asyncio
async def test_get_party_invite_link(discord):
    """Test getting party invite link"""
    invite_url = "https://discord.gg/abc123"
    discord.set_party_invite(invite_url)
    assert discord.get_party_invite_link() == invite_url


@pytest.mark.asyncio
async def test_format_duration(discord):
    """Test duration formatting"""
    assert discord._format_duration(30) == "30s"
    assert discord._format_duration(90) == "1m 30s"
    assert discord._format_duration(3661) == "1h 1m"


def test_webhook_validation():
    """Test webhook URL validation"""
    valid_urls = [
        "https://discord.com/api/webhooks/123/abc",
        "https://discordapp.com/api/webhooks/123/abc",
    ]
    invalid_urls = [
        "https://example.com/webhook",
        "http://discord.com/api/webhooks/123/abc",
        "discord.com/api/webhooks/123/abc",
    ]

    for url in valid_urls:
        assert DiscordWebhookHelper.validate_webhook_url(url) is True

    for url in invalid_urls:
        assert DiscordWebhookHelper.validate_webhook_url(url) is False


def test_invite_validation():
    """Test invite URL validation"""
    valid_urls = [
        "https://discord.gg/abc123",
        "https://discord.com/invite/abc123",
    ]
    invalid_urls = [
        "https://example.com/invite",
        "http://discord.gg/abc123",
        "discord.gg/abc123",
    ]

    for url in valid_urls:
        assert DiscordWebhookHelper.validate_invite_url(url) is True

    for url in invalid_urls:
        assert DiscordWebhookHelper.validate_invite_url(url) is False


def test_webhook_instructions():
    """Test webhook instructions"""
    instructions = DiscordWebhookHelper.get_webhook_instructions()
    assert "Server Settings" in instructions
    assert "Webhook" in instructions
    assert "discord.com/api/webhooks" in instructions


def test_invite_instructions():
    """Test invite instructions"""
    instructions = DiscordWebhookHelper.get_invite_instructions()
    assert "voice channel" in instructions
    assert "Invite People" in instructions
    assert "discord.gg" in instructions


@pytest.mark.asyncio
async def test_clear_presence(discord):
    """Test clearing Rich Presence"""
    # Should not raise even if RPC not connected
    await discord.clear_presence()


class _FakeResponse:
    def __init__(self, status: int, body: str = ""):
        self.status = status
        self._body = body

    async def text(self):
        return self._body


class _FakeRequestContext:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, statuses: list[int]):
        self.statuses = statuses
        self.calls = 0

    async def close(self):
        return None

    def post(self, _url, json=None):
        status = self.statuses[min(self.calls, len(self.statuses) - 1)]
        self.calls += 1
        return _FakeRequestContext(_FakeResponse(status, body=f"status={status}"))


@pytest.mark.asyncio
async def test_send_webhook_retries_transient_status(discord, monkeypatch):
    """Transient 5xx errors should retry and eventually succeed."""
    discord.webhook_url = "https://discord.com/api/webhooks/123/abc"
    original_session = discord.session
    await original_session.close()
    discord.session = _FakeSession([503, 204])

    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr("core.discord_integration.asyncio.sleep", fake_sleep)

    await discord._send_webhook("Title", "Message")

    assert discord.session.calls == 2
    assert sleeps == [discord.webhook_retry_base_delay]


@pytest.mark.asyncio
async def test_send_webhook_does_not_retry_non_transient_status(discord, monkeypatch):
    """4xx (except 429) should not be retried."""
    discord.webhook_url = "https://discord.com/api/webhooks/123/abc"
    original_session = discord.session
    await original_session.close()
    discord.session = _FakeSession([400, 204])

    async def fake_sleep(_delay):
        raise AssertionError("sleep should not be called for non-transient errors")

    monkeypatch.setattr("core.discord_integration.asyncio.sleep", fake_sleep)

    await discord._send_webhook("Title", "Message")

    assert discord.session.calls == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
