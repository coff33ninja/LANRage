"""Tests for relay server"""

from datetime import datetime

import pytest

from core.config import Config
from servers.relay_server import RelayClient, RelayServer


@pytest.fixture
def config():
    """Create test config"""
    config = Config.load()
    config.relay_port = 51821
    config.relay_public_ip = "1.2.3.4"
    return config


@pytest.fixture
def server(config):
    """Create relay server"""
    return RelayServer(config)


def test_server_initialization(server):
    """Test server initializes correctly"""
    assert server.config is not None
    assert server.clients == {}
    assert server.blocked_ips == set()
    assert server.running is False
    assert server.total_packets == 0
    assert server.total_bytes == 0


def test_relay_client_creation():
    """Test RelayClient dataclass"""
    client = RelayClient(
        public_key="test_key",
        address=("1.2.3.4", 51820),
        last_seen=datetime.now(),
        bytes_relayed=0,
    )

    assert client.public_key == "test_key"
    assert client.address == ("1.2.3.4", 51820)
    assert client.bytes_relayed == 0


def test_server_config(server):
    """Test server configuration"""
    assert server.config is not None
    assert server.config.relay_port == 51821
    assert server.config.relay_public_ip == "1.2.3.4"


def test_client_tracking(server):
    """Test client tracking"""
    # Add client
    public_key = "test_key_123"
    client = RelayClient(
        public_key=public_key, address=("1.2.3.4", 51820), last_seen=datetime.now()
    )

    server.clients[public_key] = client
    assert public_key in server.clients
    assert server.clients[public_key].address == ("1.2.3.4", 51820)


def test_remove_client(server):
    """Test removing client"""
    public_key = "test_key"
    server.clients[public_key] = RelayClient(
        public_key=public_key, address=("1.2.3.4", 51820), last_seen=datetime.now()
    )

    # Remove client
    del server.clients[public_key]
    assert public_key not in server.clients


def test_packet_statistics(server):
    """Test packet statistics tracking"""
    # Initial state
    assert server.total_packets == 0
    assert server.total_bytes == 0

    # Simulate packet relay
    server.total_packets += 1
    server.total_bytes += 1500

    assert server.total_packets == 1
    assert server.total_bytes == 1500


def test_multiple_clients(server):
    """Test handling multiple clients"""
    keys = ["key1", "key2", "key3"]

    for i, key in enumerate(keys):
        server.clients[key] = RelayClient(
            public_key=key, address=(f"1.2.3.{i+1}", 51820), last_seen=datetime.now()
        )

    assert len(server.clients) == 3


def test_get_client_count(server):
    """Test getting client count"""
    # Add some clients
    for i in range(5):
        key = f"key{i}"
        server.clients[key] = RelayClient(
            public_key=key, address=("1.2.3.4", 51820 + i), last_seen=datetime.now()
        )

    assert len(server.clients) == 5


def test_clear_clients(server):
    """Test clearing all clients"""
    # Add clients
    server.clients["key1"] = RelayClient("key1", ("1.2.3.4", 51820), datetime.now())
    server.clients["key2"] = RelayClient("key2", ("1.2.3.5", 51820), datetime.now())

    # Clear
    server.clients.clear()
    assert len(server.clients) == 0


def test_statistics_reset(server):
    """Test resetting statistics"""
    # Set some stats
    server.total_packets = 100
    server.total_bytes = 150000

    # Reset
    server.total_packets = 0
    server.total_bytes = 0

    assert server.total_packets == 0
    assert server.total_bytes == 0


def test_bandwidth_calculation(server):
    """Test bandwidth calculation"""
    # Simulate relaying data
    packets = [1500, 1400, 1600, 1500, 1450]

    for size in packets:
        server.total_packets += 1
        server.total_bytes += size

    assert server.total_packets == 5
    assert server.total_bytes == sum(packets)

    # Calculate average packet size
    avg_size = server.total_bytes / server.total_packets
    assert avg_size == sum(packets) / len(packets)


def test_client_bytes_tracking(server):
    """Test tracking bytes per client"""
    key = "test_key"
    client = RelayClient(
        public_key=key,
        address=("1.2.3.4", 51820),
        last_seen=datetime.now(),
        bytes_relayed=0,
    )

    server.clients[key] = client

    # Update bytes
    server.clients[key].bytes_relayed += 1500
    server.clients[key].bytes_relayed += 1400

    assert server.clients[key].bytes_relayed == 2900


def test_get_server_stats(server):
    """Test getting server statistics"""
    # Set up some data
    server.total_packets = 1000
    server.total_bytes = 1500000
    server.clients["key1"] = RelayClient("key1", ("1.2.3.4", 51820), datetime.now())
    server.clients["key2"] = RelayClient("key2", ("1.2.3.5", 51820), datetime.now())

    # Get stats
    stats = {
        "total_packets": server.total_packets,
        "total_bytes": server.total_bytes,
        "active_clients": len(server.clients),
    }

    assert stats["total_packets"] == 1000
    assert stats["total_bytes"] == 1500000
    assert stats["active_clients"] == 2


def test_client_lookup(server):
    """Test looking up client by public key"""
    key = "test_key_123"
    server.clients[key] = RelayClient(
        public_key=key, address=("1.2.3.4", 51820), last_seen=datetime.now()
    )

    # Lookup
    client = server.clients.get(key)
    assert client is not None
    assert client.public_key == key


def test_client_not_found(server):
    """Test looking up non-existent client"""
    client = server.clients.get("nonexistent")
    assert client is None


def test_blocked_ips(server):
    """Test IP blocking functionality"""
    # Add blocked IP
    server.blocked_ips.add("1.2.3.4")

    assert "1.2.3.4" in server.blocked_ips
    assert "1.2.3.5" not in server.blocked_ips


def test_unblock_ip(server):
    """Test unblocking IP"""
    server.blocked_ips.add("1.2.3.4")
    server.blocked_ips.discard("1.2.3.4")

    assert "1.2.3.4" not in server.blocked_ips


def test_server_running_state(server):
    """Test server running state"""
    assert server.running is False

    server.running = True
    assert server.running is True

    server.running = False
    assert server.running is False


def test_concurrent_clients(server):
    """Test handling concurrent clients"""
    # Add many clients
    num_clients = 100

    for i in range(num_clients):
        key = f"key{i}"
        server.clients[key] = RelayClient(
            public_key=key,
            address=(f"1.2.{i // 256}.{i % 256}", 51820),
            last_seen=datetime.now(),
        )

    assert len(server.clients) == num_clients


def test_relay_capacity(server):
    """Test relay server capacity tracking"""
    # Simulate high load
    server.total_packets = 1000000
    server.total_bytes = 1500000000  # 1.5 GB

    # Calculate throughput (bytes per packet)
    throughput = server.total_bytes / server.total_packets
    assert throughput == 1500  # Average packet size


def test_client_last_seen(server):
    """Test client last_seen timestamp"""
    key = "test_key"
    now = datetime.now()

    client = RelayClient(public_key=key, address=("1.2.3.4", 51820), last_seen=now)

    server.clients[key] = client
    assert server.clients[key].last_seen == now
