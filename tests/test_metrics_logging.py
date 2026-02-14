"""Tests for metrics logging integration"""

import pytest

from core.config import Config
from core.metrics import MetricsCollector


@pytest.fixture
def metrics_collector():
    """Set up metrics collector for testing"""
    config = Config()
    collector = MetricsCollector(config)
    yield collector


@pytest.mark.asyncio
async def test_metrics_start_logs_initialization(metrics_collector, caplog):
    """Test that MetricsCollector.start() logs initialization"""
    import logging

    caplog.set_level(logging.INFO)

    # Start metrics collection
    await metrics_collector.start()

    # Check logs
    log_text = caplog.text.lower()
    assert "start" in log_text or "metric" in log_text

    await metrics_collector.stop()


@pytest.mark.asyncio
async def test_metrics_stop_logs_shutdown(metrics_collector, caplog):
    """Test that MetricsCollector.stop() logs shutdown"""
    import logging

    caplog.set_level(logging.INFO)

    await metrics_collector.start()
    caplog.clear()

    # Stop metrics collection
    await metrics_collector.stop()

    # Check logs
    log_text = caplog.text.lower()
    assert "stop" in log_text or "metric" in log_text


@pytest.mark.asyncio
async def test_record_latency_logs_quality_events(metrics_collector, caplog):
    """Test that record_latency logs quality tracking"""
    import logging

    caplog.set_level(logging.DEBUG)

    peer_id = "metrics_test_peer"
    metrics_collector.add_peer(peer_id, "Test Peer")

    caplog.clear()

    # Record latency
    await metrics_collector.record_latency(peer_id, 50.0)

    # Check logs contain quality information
    log_text = caplog.text.lower()
    assert (
        "quality" in log_text or "latency" in log_text or peer_id in log_text
    ), "Expected latency/quality logging"


@pytest.mark.asyncio
async def test_game_session_logging(metrics_collector, caplog):
    """Test that game session events are logged"""
    import logging

    caplog.set_level(logging.INFO)

    game_id = "test_game_1"
    game_name = "Test Game"
    peers = ["peer1", "peer2"]

    # Start game session
    await metrics_collector.start_game_session(game_id, game_name, peers)

    # Check logs
    log_text = caplog.text.lower()
    assert "game" in log_text or game_id in log_text, "Expected game session logging"

    caplog.clear()

    # End game session
    await metrics_collector.end_game_session()

    # Check end logs
    log_text = caplog.text.lower()
    assert (
        "end" in log_text or "stop" in log_text or "game" in log_text
    ), "Expected game session end logging"
