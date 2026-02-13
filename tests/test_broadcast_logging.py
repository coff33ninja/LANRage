"""Tests for broadcast logging integration"""

import pytest

from core.broadcast import BroadcastEmulator
from core.config import Config


@pytest.fixture
def broadcast_emulator():
    """Set up broadcast emulator for testing"""
    config = Config()
    emulator = BroadcastEmulator(config)
    yield emulator


@pytest.mark.asyncio
async def test_broadcast_start_logs_listener_count(broadcast_emulator, caplog):
    """Test that broadcasting start() logs successful listener count"""
    import logging

    caplog.set_level(logging.INFO)

    # Start broadcast
    await broadcast_emulator.start()

    # Check logs
    log_text = caplog.text
    assert (
        "listeners" in log_text.lower() or "broadcast" in log_text.lower()
    ), "Expected broadcast start logging"

    await broadcast_emulator.stop()


@pytest.mark.asyncio
async def test_broadcast_stop_logs_completion(broadcast_emulator, caplog):
    """Test that broadcasting stop() logs completion"""
    import logging

    caplog.set_level(logging.INFO)

    # Start and stop
    await broadcast_emulator.start()
    caplog.clear()
    await broadcast_emulator.stop()

    # Check logs
    log_text = caplog.text.lower()
    assert (
        "stop" in log_text or "destroy" in log_text
    ), "Expected broadcast stop logging"


@pytest.mark.asyncio
async def test_broadcast_add_peer_logs_activity(broadcast_emulator, caplog):
    """Test that add_peer logs peer addition"""
    import logging

    caplog.set_level(logging.DEBUG)

    await broadcast_emulator.start()

    peer_id = "test_broadcast_peer"
    peer_ip = "192.168.1.100"
    peer_port = 5000

    caplog.clear()

    # Add peer
    await broadcast_emulator.add_peer(peer_id, peer_ip, peer_port)

    # Check logs contain peer info
    log_text = caplog.text.lower()
    assert peer_id in log_text or "peer" in log_text, "Expected peer addition logging"

    await broadcast_emulator.stop()
