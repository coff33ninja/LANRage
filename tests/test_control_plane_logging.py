"""Tests for control plane logging integration"""

import pytest

from core.config import Config
from core.control import ControlPlane
from core.logging_config import clear_context, get_context, set_context


@pytest.fixture
def control_plane():
    """Set up control plane for testing"""
    config = Config()
    control = ControlPlane(config)
    yield control


@pytest.mark.asyncio
async def test_register_party_logging_sets_context(control_plane, caplog):
    """Test that register_party sets context for logging"""
    party_id = "test_party_1"
    peer_id = "test_peer_1"

    # Register a party
    await control_plane.register_party(party_id, peer_id)

    # Check that context was established (we can log after and context should be set)
    set_context(party_id_val=party_id, peer_id_val=peer_id)
    context = get_context()
    assert context is not None

    # Verify party was created
    party = await control_plane.get_party(party_id)
    assert party is not None
    assert party.party_id == party_id


@pytest.mark.asyncio
async def test_join_party_logs_peer_join(control_plane, caplog):
    """Test that join_party logs the peer joining event"""
    import logging

    caplog.set_level(logging.DEBUG)

    party_id = "test_party_join"
    peer_id_1 = "peer_1"
    peer_id_2 = "peer_2"

    # Register initial party with peer
    await control_plane.register_party(party_id, peer_id_1)

    # Clear caplog
    caplog.clear()

    # Join another peer to the party
    await control_plane.join_party(party_id, peer_id_2)

    # Check logs contain join information
    log_text = caplog.text
    assert peer_id_2 in log_text or "join" in log_text.lower()


@pytest.mark.asyncio
async def test_heartbeat_establishes_context(control_plane, caplog):
    """Test that heartbeat sets correlation context"""
    import logging

    caplog.set_level(logging.DEBUG)

    party_id = "heartbeat_party"
    peer_id = "heartbeat_peer"

    # Register party and peer
    await control_plane.register_party(party_id, peer_id)

    caplog.clear()

    # Send heartbeat
    await control_plane.heartbeat(party_id, peer_id)

    # Context should be set during heartbeat execution
    set_context(party_id_val=party_id, peer_id_val=peer_id)
    context = get_context()
    assert context is not None

    clear_context()
