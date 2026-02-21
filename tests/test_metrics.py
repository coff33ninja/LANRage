"""Tests for metrics collector"""

import asyncio
import platform
import time
from collections import deque

import pytest

from core.config import Config
from core.metrics import ConnectionQualityMonitor, MetricsCollector


@pytest.fixture
async def metrics():
    """Create a metrics collector instance"""
    config = await Config.load()
    collector = MetricsCollector(config)
    # Use platform-specific event loop policy for optimal performance
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        # Linux/Unix: Use SelectorEventLoopPolicy explicitly for consistency
        # This is the default on Unix, but we set it explicitly to match Windows pattern
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    return collector


def test_metrics_initialization(metrics):
    """Test metrics collector initialization"""
    assert metrics.peer_metrics == {}
    assert isinstance(metrics.system_metrics.cpu_percent, deque)
    assert isinstance(metrics.game_sessions, deque)


@pytest.mark.asyncio
async def test_record_peer_latency(metrics):
    """Test recording peer latency"""
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_latency("peer1", 25.5)

    summary = await metrics.get_peer_summary("peer1")
    assert summary is not None
    assert summary["peer_id"] == "peer1"
    assert summary["latency"]["average"] == 25.5
    assert summary["latency"]["min"] == 25.5
    assert summary["latency"]["max"] == 25.5


@pytest.mark.asyncio
async def test_record_multiple_latencies(metrics):
    """Test recording multiple latencies"""
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_latency("peer1", 20.0)
    await metrics.record_latency("peer1", 30.0)
    await metrics.record_latency("peer1", 25.0)

    summary = await metrics.get_peer_summary("peer1")
    assert summary["latency"]["average"] == 25.0
    assert summary["latency"]["min"] == 20.0
    assert summary["latency"]["max"] == 30.0


@pytest.mark.asyncio
async def test_record_peer_bandwidth(metrics):
    """Test recording peer bandwidth"""
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_bandwidth("peer1", 1024, 512)

    summary = await metrics.get_peer_summary("peer1")
    assert summary is not None
    assert summary["bandwidth"]["sent"] == 1024
    assert summary["bandwidth"]["received"] == 512


@pytest.mark.asyncio
async def test_record_peer_status(metrics):
    """Test peer status tracking"""
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_latency("peer1", 25.0)

    summary = await metrics.get_peer_summary("peer1")
    assert summary is not None
    assert summary["status"] == "connected"

    # Test degraded status with high latency
    await metrics.record_latency("peer1", 250.0)
    summary = await metrics.get_peer_summary("peer1")
    assert summary["status"] == "degraded"


@pytest.mark.asyncio
async def test_get_all_peers_summary(metrics):
    """Test getting all peers summary"""
    metrics.add_peer("peer1", "Peer 1")
    metrics.add_peer("peer2", "Peer 2")
    await metrics.record_latency("peer1", 25.0)
    await metrics.record_latency("peer2", 30.0)

    summaries = await metrics.get_all_peers_summary()
    assert len(summaries) == 2
    assert any(s["peer_id"] == "peer1" for s in summaries)
    assert any(s["peer_id"] == "peer2" for s in summaries)


@pytest.mark.asyncio
async def test_latency_history(metrics):
    """Test latency history retrieval"""
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_latency("peer1", 20.0)
    await asyncio.sleep(0.1)
    await metrics.record_latency("peer1", 25.0)
    await asyncio.sleep(0.1)
    await metrics.record_latency("peer1", 30.0)

    history = metrics.get_latency_history("peer1", duration=10)
    assert len(history) == 3
    assert all("timestamp" in point for point in history)
    assert all("value" in point for point in history)


@pytest.mark.asyncio
async def test_latency_history_duration_filter(metrics):
    """Test latency history duration filtering"""
    metrics.add_peer("peer1", "Peer 1")

    # Record old latency
    await metrics.record_latency("peer1", 20.0)

    # Manually set old timestamp
    if "peer1" in metrics.peer_metrics and metrics.peer_metrics["peer1"].latency:
        metrics.peer_metrics["peer1"].latency[0].timestamp = time.time() - 100

    # Record new latency
    await metrics.record_latency("peer1", 30.0)

    # Get recent history (last 10 seconds)
    history = metrics.get_latency_history("peer1", duration=10)
    assert len(history) == 1
    assert history[0]["value"] == 30.0


def test_record_system_metrics(metrics):
    """Test recording system metrics"""
    # System metrics are collected automatically, so we just check the structure
    summary = metrics.get_system_summary()
    assert "cpu" in summary
    assert "memory" in summary
    assert "network" in summary
    assert "current" in summary["cpu"]
    assert "average" in summary["cpu"]


def test_system_history(metrics):
    """Test system metrics history"""
    # System metrics are collected automatically
    history = metrics.get_system_history(duration=10)
    assert "cpu" in history
    assert "memory" in history
    assert "network_sent" in history
    assert "network_received" in history
    assert isinstance(history["cpu"], list)
    assert isinstance(history["memory"], list)


@pytest.mark.asyncio
async def test_start_game_session(metrics):
    """Test starting a game session"""
    await metrics.start_game_session("minecraft", "Minecraft", ["Alice", "Bob"])

    assert metrics.active_session is not None
    assert metrics.active_session.game_name == "Minecraft"
    assert metrics.active_session.peers == ["Alice", "Bob"]
    assert metrics.active_session.ended_at is None


@pytest.mark.asyncio
async def test_end_game_session(metrics):
    """Test ending a game session"""
    await metrics.start_game_session("minecraft", "Minecraft", ["Alice", "Bob"])
    await asyncio.sleep(0.1)
    await metrics.end_game_session()

    sessions = metrics.get_game_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0]["ended_at"] is not None
    assert sessions[0]["duration"] > 0


@pytest.mark.asyncio
async def test_get_game_sessions_limit(metrics):
    """Test game sessions limit"""
    for i in range(15):
        await metrics.start_game_session(f"game{i}", f"Game{i}", ["Player1"])
        await metrics.end_game_session()

    sessions = metrics.get_game_sessions(limit=10)
    assert len(sessions) == 10


@pytest.mark.asyncio
async def test_network_quality_score(metrics):
    """Test network quality score calculation"""
    # Good network
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_latency("peer1", 20.0)

    score = metrics.get_network_quality_score()
    assert score >= 80  # Should be "Excellent" or "Good"

    # Bad network
    metrics.add_peer("peer2", "Peer 2")
    await metrics.record_latency("peer2", 200.0)

    score = metrics.get_network_quality_score()
    assert score < 80  # Should be lower with bad peer


@pytest.mark.asyncio
async def test_peer_connection_status(metrics):
    """Test peer connection status"""
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_latency("peer1", 25.0)

    summary = await metrics.get_peer_summary("peer1")
    assert summary["status"] == "connected"


@pytest.mark.asyncio
async def test_peer_uptime(metrics):
    """Test peer uptime calculation"""
    metrics.add_peer("peer1", "Peer 1")
    await metrics.record_latency("peer1", 25.0)
    await asyncio.sleep(0.2)

    summary = await metrics.get_peer_summary("peer1")
    # Uptime is calculated as time.time() - last_seen, which should be small
    assert summary["uptime"] < 1.0


@pytest.mark.asyncio
async def test_empty_peer_summary(metrics):
    """Test getting summary for non-existent peer"""
    summary = await metrics.get_peer_summary("nonexistent")
    assert summary is None


def test_empty_latency_history(metrics):
    """Test getting history for non-existent peer"""
    history = metrics.get_latency_history("nonexistent", duration=10)
    assert history == []


@pytest.mark.asyncio
async def test_metrics_cleanup(metrics):
    """Test metrics cleanup (old data removal)"""
    metrics.add_peer("peer1", "Peer 1")

    # Record old latency
    await metrics.record_latency("peer1", 20.0)

    # Manually set very old timestamp
    if "peer1" in metrics.peer_metrics and metrics.peer_metrics["peer1"].latency:
        metrics.peer_metrics["peer1"].latency[0].timestamp = time.time() - 10000

    # Get recent history
    history = metrics.get_latency_history("peer1", duration=3600)
    assert len(history) == 0  # Old data should be filtered out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


def test_connection_quality_monitor_perfect_score():
    """Perfect conditions should produce top quality score."""
    monitor = ConnectionQualityMonitor()
    score, grade = monitor.calculate_quality_score(
        latency_ms=0.0,
        jitter_ms=0.0,
        packet_loss_percent=0.0,
        bandwidth_mbps=100.0,
        stability_percent=100.0,
    )
    assert score == 100.0
    assert grade == "A"


def test_connection_quality_monitor_latency_spike_degrades_score():
    """Higher latency should lower quality score."""
    monitor = ConnectionQualityMonitor()
    high_score, _ = monitor.calculate_quality_score(
        latency_ms=15.0,
        jitter_ms=2.0,
        packet_loss_percent=0.0,
        bandwidth_mbps=50.0,
        stability_percent=100.0,
    )
    low_score, _ = monitor.calculate_quality_score(
        latency_ms=250.0,
        jitter_ms=20.0,
        packet_loss_percent=0.0,
        bandwidth_mbps=50.0,
        stability_percent=100.0,
    )
    assert low_score < high_score


def test_connection_quality_monitor_packet_loss_impact():
    """Packet loss must impact score significantly."""
    monitor = ConnectionQualityMonitor()
    no_loss, _ = monitor.calculate_quality_score(
        latency_ms=30.0,
        jitter_ms=4.0,
        packet_loss_percent=0.0,
        bandwidth_mbps=20.0,
        stability_percent=100.0,
    )
    with_loss, _ = monitor.calculate_quality_score(
        latency_ms=30.0,
        jitter_ms=4.0,
        packet_loss_percent=30.0,
        bandwidth_mbps=20.0,
        stability_percent=100.0,
    )
    assert with_loss < no_loss


def test_connection_quality_monitor_stability_integration():
    """Failed measurements should reduce stability and score."""
    monitor = ConnectionQualityMonitor()
    peer_id = "peer-stability"
    monitor.record_measurement(peer_id, latency_ms=20.0)
    monitor.record_failed_measurement(peer_id)
    monitor.record_failed_measurement(peer_id)
    sample = monitor.record_measurement(peer_id, latency_ms=25.0)
    assert sample.stability_percent < 100.0
    assert sample.quality_score < 100.0


def test_connection_quality_monitor_rolling_average():
    """Rolling average should aggregate recent samples."""
    monitor = ConnectionQualityMonitor()
    peer_id = "peer-rolling"
    monitor.record_measurement(peer_id, latency_ms=20.0)
    monitor.record_measurement(peer_id, latency_ms=30.0)
    rolling = monitor.get_rolling_average(peer_id)
    assert rolling is not None
    assert rolling["sample_count"] == 2.0
    assert rolling["avg_score"] > 0
