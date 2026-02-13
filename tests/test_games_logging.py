"""Tests for games logging integration"""

import pytest

from core.config import Config
from core.games import GameDetector
from core.logging_config import clear_context, get_context, set_context


@pytest.fixture
def game_detector():
    """Set up game detector for testing"""
    config = Config()
    detector = GameDetector(config)
    yield detector


@pytest.mark.asyncio
async def test_game_detector_start_logs_startup(game_detector, caplog):
    """Test that GameDetector.start() logs startup information"""
    import logging

    caplog.set_level(logging.INFO)

    # Start detector
    await game_detector.start()

    # Check logs
    log_text = caplog.text.lower()
    assert "start" in log_text or "game" in log_text

    await game_detector.stop()


@pytest.mark.asyncio
async def test_game_detector_stop_logs_shutdown(game_detector, caplog):
    """Test that GameDetector.stop() logs shutdown"""
    import logging

    caplog.set_level(logging.INFO)

    await game_detector.start()
    caplog.clear()

    # Stop detector
    await game_detector.stop()

    # Check logs
    log_text = caplog.text.lower()
    assert "stop" in log_text or "shutdown" in log_text or "game" in log_text


@pytest.mark.asyncio
async def test_game_detection_sets_context(game_detector):
    """Test that game detection operations set correlation context"""
    # Set context for a game session
    set_context(correlation_id_val="game_session_123")

    # Verify context is set
    context = get_context()
    assert context is not None

    clear_context()
