"""Tests for control plane client"""

from datetime import datetime

import pytest

from core.control import PeerInfo
from core.config import Config
from core.control_client import RemoteControlPlaneClient


@pytest.fixture
async def config():
    """Create test config"""
    return await Config.load()


@pytest.fixture
def client(config):
    """Create control client"""
    return RemoteControlPlaneClient(config)


def test_client_initialization(client):
    """Test client initializes correctly"""
    assert client.config is not None
    assert client.server_url is not None
    assert client.client is None
    assert client.auth_token is None
    assert client.my_peer_id is None
    assert client.my_party_id is None


@pytest.mark.asyncio
async def test_client_initialization_async(client):
    """Test async client initialization"""
    await client.initialize()

    assert client.client is not None

    # Cleanup
    await client.close()


@pytest.mark.asyncio
async def test_client_cleanup(client):
    """Test client cleanup"""
    await client.initialize()
    await client.close()

    # Client should be closed
    assert client.client is None or client.client.is_closed


def test_heartbeat_interval(client):
    """Test heartbeat interval setting"""
    assert client.heartbeat_interval == 30

    client.heartbeat_interval = 60
    assert client.heartbeat_interval == 60


@pytest.mark.asyncio
async def test_close_without_heartbeat(client):
    """Test closing client without heartbeat task"""
    await client.initialize()
    assert client.heartbeat_task is None
    await client.close()


@pytest.mark.asyncio
async def test_close_with_heartbeat(client):
    """Test closing client with active heartbeat"""
    import asyncio

    await client.initialize()

    # Create a mock heartbeat task
    async def mock_heartbeat():
        await asyncio.sleep(100)

    client.heartbeat_task = asyncio.create_task(mock_heartbeat())
    task = client.heartbeat_task  # Keep reference before close()

    await client.close()

    # Task should be cancelled and heartbeat_task should be None
    assert task.cancelled()
    assert client.heartbeat_task is None


def test_server_url_configuration(client):
    """Test server URL is configured"""
    assert client.server_url is not None
    assert isinstance(client.server_url, str)


def test_auth_token_initially_none(client):
    """Test auth token is initially None"""
    assert client.auth_token is None


def test_peer_id_initially_none(client):
    """Test peer ID is initially None"""
    assert client.my_peer_id is None


def test_party_id_initially_none(client):
    """Test party ID is initially None"""
    assert client.my_party_id is None


def test_config_reference(client):
    """Test config is accessible"""
    assert client.config is not None
    assert hasattr(client.config, "control_server")


@pytest.mark.asyncio
async def test_close_idempotent(client):
    """Test close can be called multiple times"""
    await client.initialize()
    await client.close()
    await client.close()  # Should not raise


def test_client_attributes(client):
    """Test client has all required attributes"""
    assert hasattr(client, "config")
    assert hasattr(client, "server_url")
    assert hasattr(client, "client")
    assert hasattr(client, "auth_token")
    assert hasattr(client, "my_peer_id")
    assert hasattr(client, "my_party_id")
    assert hasattr(client, "heartbeat_task")
    assert hasattr(client, "heartbeat_interval")


def test_heartbeat_interval_value(client):
    """Test heartbeat interval has correct value"""
    assert client.heartbeat_interval == 30
    assert isinstance(client.heartbeat_interval, int)


def test_client_initial_state(client):
    """Test client initial state"""
    assert client.client is None
    assert client.auth_token is None
    assert client.my_peer_id is None
    assert client.my_party_id is None
    assert client.heartbeat_task is None
    assert client.heartbeat_interval == 30


@pytest.mark.asyncio
async def test_multiple_initialize_calls(client):
    """Test multiple initialize calls"""
    await client.initialize()
    _first_client = client.client

    # Second initialize should work
    await client.initialize()
    assert client.client is not None

    await client.close()


def test_config_control_server(client):
    """Test config has control server"""
    assert hasattr(client.config, "control_server")
    assert client.config.control_server is not None


def test_client_not_initialized_initially(client):
    """Test client is not initialized on creation"""
    assert client.client is None


@pytest.mark.asyncio
async def test_initialize_creates_client(client):
    """Test initialize creates httpx client"""
    await client.initialize()
    assert client.client is not None
    await client.close()


def test_heartbeat_task_initially_none(client):
    """Test heartbeat task is initially None"""
    assert client.heartbeat_task is None


def test_server_url_from_config(client):
    """Test server URL comes from config"""
    assert client.server_url == client.config.control_server


@pytest.mark.asyncio
async def test_register_party_auto_authenticates(client, monkeypatch):
    """Client should auto-register peer token before protected requests."""
    called_peer_ids = []

    async def fake_register_peer(peer_id: str):
        called_peer_ids.append(peer_id)
        client.auth_token = "token-123"
        client.my_peer_id = peer_id
        return "token-123"

    async def fake_request(method: str, endpoint: str, json_data=None, retry_count=3):
        del retry_count, method, endpoint, json_data
        return {
            "party": {
                "party_id": "party-1",
                "name": "My Party",
                "host_id": "peer-a",
                "created_at": datetime.now().isoformat(),
                "peers": {
                    "peer-a": {
                        "peer_id": "peer-a",
                        "name": "Alice",
                        "public_key": "key",
                        "nat_type": "open",
                        "public_ip": "127.0.0.1",
                        "public_port": 5000,
                        "local_ip": "127.0.0.1",
                        "local_port": 5001,
                        "last_seen": datetime.now().isoformat(),
                    }
                },
            }
        }

    monkeypatch.setattr(client, "register_peer", fake_register_peer)
    monkeypatch.setattr(client, "_request", fake_request)

    host = PeerInfo(
        peer_id="peer-a",
        name="Alice",
        public_key="key",
        nat_type="open",
        public_ip="127.0.0.1",
        public_port=5000,
        local_ip="127.0.0.1",
        local_port=5001,
        last_seen=datetime.now(),
    )

    party = await client.register_party("party-1", "My Party", host)
    assert party.party_id == "party-1"
    assert called_peer_ids == ["peer-a"]
