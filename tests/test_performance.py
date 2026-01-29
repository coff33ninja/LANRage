"""Performance tests and benchmarks"""

import asyncio
import time

import psutil
import pytest

from core.config import Config
from core.metrics import MetricsCollector
from core.server_browser import ServerBrowser


@pytest.fixture
def config():
    """Create test config"""
    return Config.load()


def test_metrics_collection_performance(config):
    """Test metrics collection performance"""
    collector = MetricsCollector(config)

    # Add some peers
    for i in range(10):
        collector.add_peer(f"peer{i}", f"Peer {i}")

    # Measure time to record latencies
    start = time.time()
    for i in range(10):
        for j in range(100):
            collector.record_latency(f"peer{i}", 25.0 + j * 0.1)
    duration = time.time() - start

    # Should complete in reasonable time
    assert duration < 1.0, f"Metrics collection too slow: {duration:.2f}s"

    # Measure time to get summaries
    start = time.time()
    for _ in range(100):
        summaries = collector.get_all_peers_summary()
    duration = time.time() - start

    assert duration < 0.5, f"Summary generation too slow: {duration:.2f}s"
    assert len(summaries) == 10


@pytest.mark.asyncio
async def test_server_browser_performance(config):
    """Test server browser performance"""
    browser = ServerBrowser(config)
    await browser.start()

    try:
        # Register many servers
        start = time.time()
        for i in range(100):
            await browser.register_server(
                server_id=f"server-{i}",
                name=f"Server {i}",
                game="Minecraft" if i % 2 == 0 else "Terraria",
                host_peer_id=f"peer{i}",
                host_peer_name=f"Host {i}",
                host_ip=f"10.66.0.{i % 255}",
                max_players=10,
                current_players=i % 10,
            )
        duration = time.time() - start

        assert duration < 2.0, f"Server registration too slow: {duration:.2f}s"

        # Measure filtering performance
        start = time.time()
        for _ in range(100):
            servers = browser.list_servers(game="Minecraft")
        duration = time.time() - start

        assert duration < 0.5, f"Server filtering too slow: {duration:.2f}s"
        assert len(servers) == 50

        # Measure search performance
        start = time.time()
        for _ in range(100):
            servers = browser.list_servers(search="Server 1")
        duration = time.time() - start

        assert duration < 0.5, f"Server search too slow: {duration:.2f}s"

    finally:
        await browser.stop()


def test_memory_usage():
    """Test memory usage stays within limits"""
    process = psutil.Process()

    # Get baseline memory
    baseline = process.memory_info().rss / 1024 / 1024  # MB

    # Create some objects
    config = Config.load()
    collector = MetricsCollector(config)

    # Add peers and data
    for i in range(50):
        collector.add_peer(f"peer{i}", f"Peer {i}")
        for j in range(360):  # Fill the deque
            collector.record_latency(f"peer{i}", 25.0 + j * 0.1)

    # Check memory usage
    current = process.memory_info().rss / 1024 / 1024  # MB
    increase = current - baseline

    # Should not use more than 50MB for this test
    assert increase < 50, f"Memory usage too high: {increase:.1f}MB"


@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test performance under concurrent load"""
    config = Config.load()
    browser = ServerBrowser(config)
    await browser.start()

    try:
        # Register servers concurrently
        start = time.time()
        tasks = []
        for i in range(50):
            task = browser.register_server(
                server_id=f"server-{i}",
                name=f"Server {i}",
                game="Minecraft",
                host_peer_id=f"peer{i}",
                host_peer_name=f"Host {i}",
                host_ip=f"10.66.0.{i}",
                max_players=10,
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
        duration = time.time() - start

        assert duration < 1.0, f"Concurrent registration too slow: {duration:.2f}s"

        # Query concurrently
        start = time.time()
        tasks = []
        for _ in range(50):
            tasks.append(asyncio.create_task(asyncio.to_thread(browser.list_servers)))

        results = await asyncio.gather(*tasks)
        duration = time.time() - start

        assert duration < 1.0, f"Concurrent queries too slow: {duration:.2f}s"
        assert all(len(r) == 50 for r in results)

    finally:
        await browser.stop()


def test_latency_calculation_performance(config):
    """Test latency calculation performance"""
    collector = MetricsCollector(config)
    collector.add_peer("peer1", "Peer 1")

    # Fill with data
    for i in range(360):
        collector.record_latency("peer1", 20.0 + i * 0.1)

    # Measure summary calculation
    start = time.time()
    for _ in range(1000):
        summary = collector.get_peer_summary("peer1")
    duration = time.time() - start

    assert duration < 0.5, f"Latency calculation too slow: {duration:.2f}s"
    assert summary is not None


def test_network_quality_score_performance(config):
    """Test network quality score calculation performance"""
    collector = MetricsCollector(config)

    # Add peers with data
    for i in range(20):
        collector.add_peer(f"peer{i}", f"Peer {i}")
        for j in range(100):
            collector.record_latency(f"peer{i}", 20.0 + j * 0.1)

    # Measure score calculation
    start = time.time()
    for _ in range(100):
        score = collector.get_network_quality_score()
    duration = time.time() - start

    assert duration < 0.5, f"Quality score calculation too slow: {duration:.2f}s"
    assert 0 <= score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
