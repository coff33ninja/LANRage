"""Tests for utility functions"""

import pytest

from core.utils import check_admin_rights, format_latency, get_connection_emoji


@pytest.mark.asyncio
async def test_check_admin_rights():
    """Test checking admin rights"""
    # Just verify it returns a boolean without error
    result = await check_admin_rights()
    assert isinstance(result, bool)


def test_format_latency_none():
    """Test latency formatting with None"""
    assert format_latency(None) == "N/A"


def test_format_latency_low():
    """Test latency formatting with low latency"""
    result = format_latency(5.5)
    assert "5.5ms" in result
    assert "✓" in result


def test_format_latency_medium():
    """Test latency formatting with medium latency"""
    result = format_latency(15.0)
    assert "15.0ms" in result
    assert "⚠" in result


def test_format_latency_high():
    """Test latency formatting with high latency"""
    result = format_latency(50.0)
    assert "50.0ms" in result
    assert "✗" in result


def test_get_connection_emoji_direct():
    """Test connection emoji for direct connection"""
    assert get_connection_emoji("direct") == "🔗"


def test_get_connection_emoji_relayed():
    """Test connection emoji for relayed connection"""
    assert get_connection_emoji("relayed") == "🔄"


def test_get_connection_emoji_connecting():
    """Test connection emoji for connecting"""
    assert get_connection_emoji("connecting") == "⏳"


def test_get_connection_emoji_host():
    """Test connection emoji for host"""
    assert get_connection_emoji("host") == "👑"


def test_get_connection_emoji_unknown():
    """Test connection emoji for unknown"""
    assert get_connection_emoji("unknown") == "❓"
    assert get_connection_emoji("invalid") == "❓"
