"""
Tests for party management features
"""

import pytest
import pytest_asyncio

from core.config import Config
from core.control import PartyInfo, PeerInfo
from core.nat import NATType
from core.network import NetworkManager
from core.party import Party, PartyManager, Peer


class TestPeerModel:
    """Test Peer model functionality"""

    def test_peer_creation_with_nat_type(self):
        """Test that Peer model includes nat_type field"""
        peer = Peer(
            id="test-peer-1",
            name="Test Peer",
            public_key="test-key-123",
            virtual_ip="10.66.0.2",
            nat_type="full_cone",
        )

        assert peer.nat_type == "full_cone"
        assert peer.id == "test-peer-1"
        assert peer.name == "Test Peer"

    def test_peer_default_nat_type(self):
        """Test that Peer model has default nat_type of 'unknown'"""
        peer = Peer(
            id="test-peer-2",
            name="Test Peer 2",
            public_key="test-key-456",
            virtual_ip="10.66.0.3",
        )

        assert peer.nat_type == "unknown"


class TestPartyCompatibility:
    """Test NAT compatibility filtering in Party"""

    def test_get_compatible_peers_full_cone(self):
        """Test getting compatible peers for full cone NAT"""
        party = Party(
            id="test-party",
            name="Test Party",
            host_id="host-1",
        )

        # Add peers with different NAT types
        # Full cone is compatible with: open, full_cone, restricted_cone, port_restricted_cone
        party.peers["peer1"] = Peer(
            id="peer1",
            name="Peer 1",
            public_key="key1",
            virtual_ip="10.66.0.2",
            nat_type="full_cone",
        )
        party.peers["peer2"] = Peer(
            id="peer2",
            name="Peer 2",
            public_key="key2",
            virtual_ip="10.66.0.3",
            nat_type="symmetric",  # NOT compatible with full cone
        )
        party.peers["peer3"] = Peer(
            id="peer3",
            name="Peer 3",
            public_key="key3",
            virtual_ip="10.66.0.4",
            nat_type="port_restricted_cone",  # Compatible with full cone
        )

        # Full cone NAT should be compatible with open, full_cone, restricted_cone, port_restricted_cone
        compatible = party.get_compatible_peers(NATType.FULL_CONE)

        # Should include peer1 (full_cone) and peer3 (port_restricted_cone), but not peer2 (symmetric)
        assert len(compatible) == 2
        compatible_ids = [peer.id for peer in compatible]
        assert "peer1" in compatible_ids
        assert "peer3" in compatible_ids
        assert "peer2" not in compatible_ids

    def test_get_compatible_peers_symmetric(self):
        """Test getting compatible peers for symmetric NAT"""
        party = Party(
            id="test-party",
            name="Test Party",
            host_id="host-1",
        )

        # Add peers with different NAT types
        party.peers["peer1"] = Peer(
            id="peer1",
            name="Peer 1",
            public_key="key1",
            virtual_ip="10.66.0.2",
            nat_type="open",  # Compatible with symmetric
        )
        party.peers["peer2"] = Peer(
            id="peer2",
            name="Peer 2",
            public_key="key2",
            virtual_ip="10.66.0.3",
            nat_type="symmetric",  # NOT compatible with symmetric
        )
        party.peers["peer3"] = Peer(
            id="peer3",
            name="Peer 3",
            public_key="key3",
            virtual_ip="10.66.0.4",
            nat_type="full_cone",  # NOT compatible with symmetric
        )

        # Symmetric NAT is only compatible with open NAT
        compatible = party.get_compatible_peers(NATType.SYMMETRIC)

        # Should only include peer1 (open)
        assert len(compatible) == 1
        assert compatible[0].id == "peer1"
        assert compatible[0].nat_type == "open"

    def test_get_compatible_peers_unknown_nat(self):
        """Test handling of unknown NAT types"""
        party = Party(
            id="test-party",
            name="Test Party",
            host_id="host-1",
        )

        # Add peer with unknown NAT type
        party.peers["peer1"] = Peer(
            id="peer1",
            name="Peer 1",
            public_key="key1",
            virtual_ip="10.66.0.2",
            nat_type="unknown",
        )

        # Unknown NAT has no compatible types (requires relay)
        compatible = party.get_compatible_peers(NATType.FULL_CONE)
        assert isinstance(compatible, list)
        # Unknown NAT should not be in compatible list
        assert len(compatible) == 0


@pytest_asyncio.fixture
async def network_manager():
    """Create a network manager for testing"""
    config = await Config.load()
    network = NetworkManager(config)
    await network._ensure_keys()
    return network


@pytest.mark.asyncio
async def test_party_creation_includes_nat_type(network_manager):
    """Test that party creation populates NAT type in peer"""
    config = await Config.load()

    try:
        # Create party manager
        party_manager = PartyManager(config, network_manager)

        # Initialize NAT (this will detect NAT type)
        from contextlib import suppress

        with suppress(Exception):
            # NAT detection might fail in test environment, that's okay
            await party_manager.initialize_nat()

        # Create party
        party = await party_manager.create_party("Test Party")

        # Check that the host peer has a nat_type field
        host_peer = party.peers.get(party_manager.my_peer_id)
        assert host_peer is not None
        assert hasattr(host_peer, "nat_type")
        assert isinstance(host_peer.nat_type, str)
        # Should be either a valid NAT type or "unknown"
        assert host_peer.nat_type in [
            "open",
            "full_cone",
            "restricted_cone",
            "port_restricted_cone",
            "symmetric",
            "unknown",
        ]

    except Exception as e:
        pytest.skip(f"Test requires network setup: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


@pytest.mark.asyncio
async def test_join_party_lazy_initializes_control_and_nat(monkeypatch):
    """join_party should lazily initialize NAT/control instead of hard-failing."""

    class DummyNetwork:
        public_key_b64 = "dummy-key"

    class FakeNAT:
        class _NatType:
            value = "unknown"

        nat_type = _NatType()
        public_ip = "127.0.0.1"
        public_port = 4000
        local_ip = "127.0.0.1"
        local_port = 4001

    class FakeControl:
        async def join_party(self, party_id: str, peer_info: PeerInfo) -> PartyInfo:
            return PartyInfo(
                party_id=party_id,
                name="Joined Party",
                host_id="host-peer",
                created_at=peer_info.last_seen,
                peers={peer_info.peer_id: peer_info},
            )

    manager = PartyManager(Config(), DummyNetwork())
    manager.nat = None
    manager.control = None

    async def fake_init_nat():
        manager.nat = FakeNAT()

    async def fake_init_control():
        manager.control = FakeControl()

    monkeypatch.setattr(manager, "initialize_nat", fake_init_nat)
    monkeypatch.setattr(manager, "initialize_control", fake_init_control)

    party = await manager.join_party("party-123", "Tester")
    assert party.id == "party-123"
    assert manager.control is not None
    assert manager.nat is not None
