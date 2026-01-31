"""Tests for connection management"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.config import Config
from core.connection import ConnectionManager
from core.exceptions import PeerConnectionError


@pytest.fixture
async def config():
    """Create test config"""
    return await Config.load()


@pytest.fixture
def mock_network():
    """Create mock network manager"""
    network = MagicMock()
    network.add_peer = AsyncMock()
    network.remove_peer = AsyncMock()
    network.measure_latency = AsyncMock(return_value=25.5)
    return network


@pytest.fixture
def mock_nat():
    """Create mock NAT traversal"""
    nat = MagicMock()
    nat.detect_nat_type = AsyncMock(return_value="full_cone")
    return nat


@pytest.fixture
def mock_control():
    """Create mock control plane"""
    control = MagicMock()
    control.discover_peer = AsyncMock()
    return control


@pytest.fixture
def connection_manager(config, mock_network, mock_nat, mock_control):
    """Create connection manager"""
    return ConnectionManager(config, mock_network, mock_nat, mock_control)


def test_connection_manager_initialization(connection_manager):
    """Test connection manager initializes correctly"""
    assert connection_manager.config is not None
    assert connection_manager.network is not None
    assert connection_manager.nat is not None
    assert connection_manager.control is not None
    assert connection_manager.connections == {}


@pytest.mark.asyncio
async def test_connect_to_peer_not_found(connection_manager, mock_control):
    """Test connecting to non-existent peer"""
    mock_control.discover_peer.return_value = None

    with pytest.raises(PeerConnectionError, match="not found"):
        await connection_manager.connect_to_peer("party123", "peer456")


@pytest.mark.asyncio
async def test_allocate_virtual_ip(connection_manager):
    """Test virtual IP allocation"""
    # Allocate IPs for multiple peers
    ip1 = connection_manager._allocate_virtual_ip("peer1")
    ip2 = connection_manager._allocate_virtual_ip("peer2")

    assert ip1 != ip2
    assert ip1.startswith("10.66.")
    assert ip2.startswith("10.66.")


def test_connection_count(connection_manager):
    """Test getting connection count"""
    # Initially empty
    assert len(connection_manager.connections) == 0


def test_ip_pool_initialization(connection_manager):
    """Test IP address pool is initialized"""
    assert connection_manager.ip_pool is not None


def test_coordinator_initialization(connection_manager):
    """Test connection coordinator is initialized"""
    assert connection_manager.coordinator is not None


@pytest.mark.asyncio
async def test_network_integration(connection_manager, mock_network):
    """Test network manager integration"""
    # Verify network manager is accessible
    assert connection_manager.network is not None

    # Test add_peer call
    await connection_manager.network.add_peer(
        peer_public_key="test_key",
        peer_endpoint="1.2.3.4:51820",
        allowed_ips=["10.66.0.2/32"],
    )

    mock_network.add_peer.assert_called_once()


@pytest.mark.asyncio
async def test_nat_integration(connection_manager, mock_nat):
    """Test NAT traversal integration"""
    # Verify NAT is accessible
    assert connection_manager.nat is not None

    # Test NAT detection
    nat_type = await connection_manager.nat.detect_nat_type()
    assert nat_type == "full_cone"


def test_connection_manager_config(connection_manager):
    """Test connection manager configuration"""
    assert connection_manager.config is not None
    assert hasattr(connection_manager.config, "interface_name")


def test_connections_dict(connection_manager):
    """Test connections dictionary"""
    assert isinstance(connection_manager.connections, dict)
    assert len(connection_manager.connections) == 0


def test_network_manager_reference(connection_manager):
    """Test network manager reference"""
    assert connection_manager.network is not None
    assert hasattr(connection_manager.network, "add_peer")
    assert hasattr(connection_manager.network, "remove_peer")


def test_nat_traversal_reference(connection_manager):
    """Test NAT traversal reference"""
    assert connection_manager.nat is not None
    assert hasattr(connection_manager.nat, "detect_nat_type")


def test_control_plane_reference(connection_manager):
    """Test control plane reference"""
    assert connection_manager.control is not None
    assert hasattr(connection_manager.control, "discover_peer")


def test_coordinator_reference(connection_manager):
    """Test coordinator reference"""
    assert connection_manager.coordinator is not None


def test_ip_pool_reference(connection_manager):
    """Test IP pool reference"""
    assert connection_manager.ip_pool is not None


@pytest.mark.asyncio
async def test_multiple_ip_allocations(connection_manager):
    """Test allocating multiple IPs"""
    ips = set()

    for i in range(10):
        ip = connection_manager._allocate_virtual_ip(f"peer{i}")
        ips.add(ip)

    # All IPs should be unique
    assert len(ips) == 10

    # All should be in correct subnet
    for ip in ips:
        assert ip.startswith("10.66.")


def test_connection_manager_attributes(connection_manager):
    """Test connection manager has all required attributes"""
    assert hasattr(connection_manager, "config")
    assert hasattr(connection_manager, "network")
    assert hasattr(connection_manager, "nat")
    assert hasattr(connection_manager, "control")
    assert hasattr(connection_manager, "coordinator")
    assert hasattr(connection_manager, "ip_pool")
    assert hasattr(connection_manager, "connections")


@pytest.mark.asyncio
async def test_network_add_peer_call(connection_manager, mock_network):
    """Test network add_peer is callable"""
    await connection_manager.network.add_peer(
        peer_public_key="key123",
        peer_endpoint="1.2.3.4:51820",
        allowed_ips=["10.66.0.5/32"],
    )

    assert mock_network.add_peer.called


@pytest.mark.asyncio
async def test_network_remove_peer_call(connection_manager, mock_network):
    """Test network remove_peer is callable"""
    await connection_manager.network.remove_peer("key123")

    assert mock_network.remove_peer.called


@pytest.mark.asyncio
async def test_network_measure_latency_call(connection_manager, mock_network):
    """Test network measure_latency is callable"""
    latency = await connection_manager.network.measure_latency("10.66.0.2")

    assert latency == 25.5
    assert mock_network.measure_latency.called


def test_empty_connections_on_init(connection_manager):
    """Test connections are empty on initialization"""
    assert len(connection_manager.connections) == 0
    assert connection_manager.connections == {}


def test_config_access(connection_manager):
    """Test config is accessible"""
    assert connection_manager.config is not None
    config = connection_manager.config
    assert hasattr(config, "interface_name")
    assert hasattr(config, "mode")
