"""Tests for broadcast packet deduplication"""

import asyncio

import pytest

from core.broadcast import BroadcastDeduplicator, BroadcastPacket
from core.config import Config


@pytest.fixture
async def config():
    """Create test config"""
    return await Config.load()


@pytest.fixture
async def deduplicator():
    """Create a deduplicator instance"""
    return BroadcastDeduplicator(window_seconds=2.0, cleanup_interval=0.5)


@pytest.fixture
def sample_packet():
    """Create a sample broadcast packet"""
    return BroadcastPacket(
        data=b"MINECRAFT_CHALLENGE\x00\x00\x00\x00\x00",
        source_ip="192.168.1.100",
        source_port=12345,
        dest_port=4445,
        protocol="udp",
    )


@pytest.fixture
def different_packet():
    """Create a different broadcast packet"""
    return BroadcastPacket(
        data=b"DIFFERENT_DATA\x00\x00\x00\x00\x00\x00",
        source_ip="192.168.1.101",
        source_port=12346,
        dest_port=7777,
        protocol="udp",
    )


@pytest.mark.asyncio
async def test_same_packet_not_forwarded_twice(deduplicator, sample_packet):
    """Test that the same packet is not forwarded twice"""
    # First packet should be forwarded
    result1 = await deduplicator.should_forward(sample_packet)
    assert result1 is True

    # Identical packet should be deduplicated
    result2 = await deduplicator.should_forward(sample_packet)
    assert result2 is False


@pytest.mark.asyncio
async def test_different_packets_forwarded(
    deduplicator, sample_packet, different_packet
):
    """Test that different packets are both forwarded"""
    result1 = await deduplicator.should_forward(sample_packet)
    result2 = await deduplicator.should_forward(different_packet)

    assert result1 is True
    assert result2 is True


@pytest.mark.asyncio
async def test_packet_dedup_expires_after_window(deduplicator, sample_packet):
    """Test that deduplicated packets expire after the time window"""
    # First packet
    result1 = await deduplicator.should_forward(sample_packet)
    assert result1 is True

    # Duplicate within window
    result2 = await deduplicator.should_forward(sample_packet)
    assert result2 is False

    # Wait for window to expire
    await asyncio.sleep(deduplicator.window_seconds + 0.5)

    # Same packet should now be forwarded again
    result3 = await deduplicator.should_forward(sample_packet)
    assert result3 is True


@pytest.mark.asyncio
async def test_source_peer_prevention(deduplicator, sample_packet):
    """Test that packets are not sent back to source peer"""
    # First packet
    result1 = await deduplicator.should_forward(
        sample_packet, source_peer="192.168.1.100"
    )
    assert result1 is False  # Would not forward back to source

    # Different source - should forward
    result2 = await deduplicator.should_forward(
        sample_packet, source_peer="192.168.1.200"
    )
    assert result2 is True  # Forwards to different peer


@pytest.mark.asyncio
async def test_metrics_collection(deduplicator, sample_packet, different_packet):
    """Test that metrics are correctly tracked"""
    # Send packets
    await deduplicator.should_forward(sample_packet)
    await deduplicator.should_forward(sample_packet)  # Duplicate
    await deduplicator.should_forward(different_packet)
    await deduplicator.should_forward(sample_packet)  # Duplicate
    await deduplicator.should_forward(different_packet)  # Duplicate

    metrics = deduplicator.get_metrics()

    assert metrics["total_packets"] == 5
    assert metrics["forwarded_packets"] == 2
    assert metrics["deduplicated_packets"] == 3
    assert metrics["deduplicate_rate"] == pytest.approx(60.0, rel=0.1)


@pytest.mark.asyncio
async def test_metrics_empty(deduplicator):
    """Test metrics when no packets processed"""
    metrics = deduplicator.get_metrics()

    assert metrics["total_packets"] == 0
    assert metrics["forwarded_packets"] == 0
    assert metrics["deduplicated_packets"] == 0
    assert metrics["deduplicate_rate"] == 0.0


@pytest.mark.asyncio
async def test_disable_enable(deduplicator, sample_packet):
    """Test disabling and enabling deduplication"""
    # Normal dedup
    result1 = await deduplicator.should_forward(sample_packet)
    result2 = await deduplicator.should_forward(sample_packet)
    assert result1 is True
    assert result2 is False

    # Disable dedup
    deduplicator.disable()
    result3 = await deduplicator.should_forward(sample_packet)
    assert result3 is True

    # Re-enable dedup
    deduplicator.enable()
    result4 = await deduplicator.should_forward(sample_packet)
    assert result4 is False  # Still in dedup window


@pytest.mark.asyncio
async def test_memory_efficiency(deduplicator):
    """Test that memory usage doesn't grow unbounded"""
    # Create many unique packets in a loop
    unique_packets = set()
    for i in range(1000):
        packet = BroadcastPacket(
            data=bytes([i % 256]) * 100,  # Unique data
            source_ip=f"192.168.1.{i % 256}",
            source_port=10000 + (i % 65000),
            dest_port=4445,
            protocol="udp",
        )
        await deduplicator.should_forward(packet)
        # Count unique combinations
        unique_packets.add((packet.source_ip, packet.source_port, packet.dest_port))

    # After window expires, hashes should be cleaned up
    await asyncio.sleep(deduplicator.cleanup_interval + 1.0)

    metrics = deduplicator.get_metrics()
    # Should have very few tracked hashes after cleanup (cleanup removes expired ones)
    # With 256 unique source IPs (i % 256), we expect roughly 256 unique packets
    # But with timing variance and port collisions, we might have 256-500 packets
    # The deduplicator should keep hashes for only window_seconds (2.0 sec)
    assert metrics["tracked_hashes"] < len(unique_packets) * 0.5  # Less than half


@pytest.mark.asyncio
async def test_hash_function_consistency(deduplicator, sample_packet):
    """Test that packet hash is consistent"""
    # Hash same packet twice
    hash1 = deduplicator._hash_packet(sample_packet)
    hash2 = deduplicator._hash_packet(sample_packet)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex digest is 64 chars


@pytest.mark.asyncio
async def test_hash_sensitivity_to_changes(deduplicator, sample_packet):
    """Test that tiny changes to packet create different hashes"""
    hash_original = deduplicator._hash_packet(sample_packet)

    # Change data
    modified_packet = BroadcastPacket(
        data=b"MINECRAFT_CHALLENGE\x00\x00\x00\x00\x01",  # Last byte changed
        source_ip=sample_packet.source_ip,
        source_port=sample_packet.source_port,
        dest_port=sample_packet.dest_port,
        protocol=sample_packet.protocol,
    )
    hash_data_changed = deduplicator._hash_packet(modified_packet)
    assert hash_original != hash_data_changed

    # Change source IP
    modified_packet = BroadcastPacket(
        data=sample_packet.data,
        source_ip="192.168.1.101",  # Different IP
        source_port=sample_packet.source_port,
        dest_port=sample_packet.dest_port,
        protocol=sample_packet.protocol,
    )
    hash_ip_changed = deduplicator._hash_packet(modified_packet)
    assert hash_original != hash_ip_changed

    # Change port
    modified_packet = BroadcastPacket(
        data=sample_packet.data,
        source_ip=sample_packet.source_ip,
        source_port=sample_packet.source_port,
        dest_port=4446,  # Different port
        protocol=sample_packet.protocol,
    )
    hash_port_changed = deduplicator._hash_packet(modified_packet)
    assert hash_original != hash_port_changed


@pytest.mark.asyncio
async def test_concurrent_deduplication(deduplicator):
    """Test deduplication with concurrent packet checking"""
    packet = BroadcastPacket(
        data=b"CONCURRENT_TEST",
        source_ip="192.168.1.100",
        source_port=12345,
        dest_port=4445,
        protocol="udp",
    )

    # Send same packet concurrently from multiple "threads"
    tasks = [deduplicator.should_forward(packet) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # First one should be True, rest should be False (due to dedup)
    assert results[0] is True
    assert all(r is False for r in results[1:])


@pytest.mark.asyncio
async def test_cleanup_task_cancellation(deduplicator, sample_packet):
    """Test that cleanup task is properly cancelled on flush"""
    # Start a cleanup task
    await deduplicator.should_forward(sample_packet)

    # Ensure cleanup task exists
    assert deduplicator._cleanup_task is not None

    # Flush should cancel it
    await deduplicator.flush()

    # Task should be cancelled
    assert deduplicator._cleanup_task.cancelled()


@pytest.mark.asyncio
async def test_broadcast_emulator_integration(config):
    """Test integration with BroadcastEmulator"""
    from core.broadcast import BroadcastEmulator

    emulator = BroadcastEmulator(config)

    # Verify deduplicator is initialized
    assert emulator.deduplicator is not None
    assert isinstance(emulator.deduplicator, BroadcastDeduplicator)
    assert emulator.deduplicator.enabled is True


@pytest.mark.asyncio
async def test_zero_division_protection(deduplicator):
    """Test that metrics don't cause zero division errors"""
    # Get metrics with no packets
    metrics = deduplicator.get_metrics()

    # Should not raise, deduplicate_rate should be 0
    assert metrics["deduplicate_rate"] == 0.0
    assert metrics["total_packets"] == 0
