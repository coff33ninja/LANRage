"""Tests for control-plane signaling queue behavior."""

from datetime import datetime

import pytest

from core.config import Config
from core.control_plane.control import ControlPlane, PeerInfo


@pytest.mark.asyncio
async def test_signal_connection_queues_and_polls():
    """Signal messages should queue for target peer and clear on poll."""
    control = ControlPlane(Config())

    host = PeerInfo(
        peer_id="host",
        name="Host",
        public_key="host_key",
        nat_type="open",
        public_ip="127.0.0.1",
        public_port=5000,
        local_ip="127.0.0.1",
        local_port=5000,
        last_seen=datetime.now(),
    )
    guest = PeerInfo(
        peer_id="guest",
        name="Guest",
        public_key="guest_key",
        nat_type="open",
        public_ip="127.0.0.1",
        public_port=5001,
        local_ip="127.0.0.1",
        local_port=5001,
        last_seen=datetime.now(),
    )

    await control.register_party("party1", "Test", host)
    await control.join_party("party1", guest)
    await control.signal_connection(
        "party1",
        "host",
        "guest",
        {"type": "offer", "sdp": "fake-sdp"},
    )

    signals = await control.poll_signals("party1", "guest")
    assert len(signals) == 1
    assert signals[0]["from_peer_id"] == "host"
    assert signals[0]["to_peer_id"] == "guest"
    assert signals[0]["signal_data"]["type"] == "offer"

    # Polling again should clear queue.
    assert await control.poll_signals("party1", "guest") == []
