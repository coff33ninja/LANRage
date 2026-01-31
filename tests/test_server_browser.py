"""Tests for game server browser"""

import asyncio
import time

import pytest
import pytest_asyncio

from core.config import Config
from core.server_browser import GameServer, ServerBrowser


@pytest_asyncio.fixture
async def server_browser():
    """Create a server browser instance"""
    config = await Config.load()
    browser = ServerBrowser(config)
    await browser.start()
    yield browser
    await browser.stop()


@pytest.mark.asyncio
async def test_server_registration(server_browser):
    """Test server registration"""
    server = await server_browser.register_server(
        server_id="test-server-1",
        name="Test Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=5,
        map_name="Skyblock",
        game_mode="Survival",
        tags=["pvp", "hardcore"],
    )

    assert server.id == "test-server-1"
    assert server.name == "Test Server"
    assert server.game == "Minecraft"
    assert server.current_players == 5
    assert server.max_players == 10
    assert "pvp" in server.tags


@pytest.mark.asyncio
async def test_server_update(server_browser):
    """Test updating existing server"""
    # Register initial server
    await server_browser.register_server(
        server_id="test-server-1",
        name="Test Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=5,
    )

    # Update server
    updated = await server_browser.register_server(
        server_id="test-server-1",
        name="Updated Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=7,
    )

    assert updated.name == "Updated Server"
    assert updated.current_players == 7


@pytest.mark.asyncio
async def test_server_unregistration(server_browser):
    """Test server unregistration"""
    await server_browser.register_server(
        server_id="test-server-1",
        name="Test Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
    )

    success = await server_browser.unregister_server("test-server-1")
    assert success is True

    server = server_browser.get_server("test-server-1")
    assert server is None


@pytest.mark.asyncio
async def test_server_heartbeat(server_browser):
    """Test server heartbeat updates"""
    await server_browser.register_server(
        server_id="test-server-1",
        name="Test Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
    )

    server = server_browser.get_server("test-server-1")
    initial_heartbeat = server.last_heartbeat

    await asyncio.sleep(0.1)
    await server_browser.update_heartbeat("test-server-1")

    server = server_browser.get_server("test-server-1")
    assert server.last_heartbeat > initial_heartbeat


@pytest.mark.asyncio
async def test_player_count_update(server_browser):
    """Test updating player count"""
    await server_browser.register_server(
        server_id="test-server-1",
        name="Test Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=5,
    )

    success = await server_browser.update_player_count("test-server-1", 8)
    assert success is True

    server = server_browser.get_server("test-server-1")
    assert server.current_players == 8


@pytest.mark.asyncio
async def test_list_servers_no_filter(server_browser):
    """Test listing all servers"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=5,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Server 2",
        game="Terraria",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=8,
        current_players=3,
    )

    servers = server_browser.list_servers()
    assert len(servers) == 2


@pytest.mark.asyncio
async def test_list_servers_game_filter(server_browser):
    """Test filtering servers by game"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=5,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Server 2",
        game="Terraria",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=8,
        current_players=3,
    )

    servers = server_browser.list_servers(game="Minecraft")
    assert len(servers) == 1
    assert servers[0].game == "Minecraft"


@pytest.mark.asyncio
async def test_list_servers_hide_full(server_browser):
    """Test hiding full servers"""
    await server_browser.register_server(
        server_id="server-1",
        name="Full Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=10,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Not Full Server",
        game="Minecraft",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=10,
        current_players=5,
    )

    servers = server_browser.list_servers(hide_full=True)
    assert len(servers) == 1
    assert servers[0].name == "Not Full Server"


@pytest.mark.asyncio
async def test_list_servers_hide_empty(server_browser):
    """Test hiding empty servers"""
    await server_browser.register_server(
        server_id="server-1",
        name="Empty Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=0,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Active Server",
        game="Minecraft",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=10,
        current_players=5,
    )

    servers = server_browser.list_servers(hide_empty=True)
    assert len(servers) == 1
    assert servers[0].name == "Active Server"


@pytest.mark.asyncio
async def test_list_servers_hide_password(server_browser):
    """Test hiding password-protected servers"""
    await server_browser.register_server(
        server_id="server-1",
        name="Password Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        password_protected=True,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Public Server",
        game="Minecraft",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=10,
        password_protected=False,
    )

    servers = server_browser.list_servers(hide_password=True)
    assert len(servers) == 1
    assert servers[0].name == "Public Server"


@pytest.mark.asyncio
async def test_list_servers_search(server_browser):
    """Test searching servers"""
    await server_browser.register_server(
        server_id="server-1",
        name="Epic PvP Server",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Casual Building",
        game="Minecraft",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=10,
    )

    servers = server_browser.list_servers(search="pvp")
    assert len(servers) == 1
    assert servers[0].name == "Epic PvP Server"


@pytest.mark.asyncio
async def test_list_servers_tags(server_browser):
    """Test filtering by tags"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        tags=["pvp", "hardcore"],
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Server 2",
        game="Minecraft",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=10,
        tags=["pve", "casual"],
    )

    servers = server_browser.list_servers(tags=["pvp"])
    assert len(servers) == 1
    assert servers[0].name == "Server 1"


@pytest.mark.asyncio
async def test_favorites(server_browser):
    """Test favorites system"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
    )

    # Add to favorites
    server_browser.add_favorite("server-1")
    assert server_browser.is_favorite("server-1") is True

    favorites = server_browser.get_favorites()
    assert len(favorites) == 1
    assert favorites[0].id == "server-1"

    # Remove from favorites
    server_browser.remove_favorite("server-1")
    assert server_browser.is_favorite("server-1") is False


@pytest.mark.asyncio
async def test_games_list(server_browser):
    """Test getting list of games"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Server 2",
        game="Terraria",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=10,
    )

    games = server_browser.get_games_list()
    assert len(games) == 2
    assert "Minecraft" in games
    assert "Terraria" in games


@pytest.mark.asyncio
async def test_server_stats(server_browser):
    """Test server statistics"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=5,
    )

    await server_browser.register_server(
        server_id="server-2",
        name="Server 2",
        game="Terraria",
        host_peer_id="peer2",
        host_peer_name="Bob",
        host_ip="10.66.0.3",
        max_players=8,
        current_players=3,
    )

    stats = server_browser.get_stats()
    assert stats["total_servers"] == 2
    assert stats["total_players"] == 8
    assert stats["unique_games"] == 2


@pytest.mark.asyncio
async def test_server_expiration(server_browser):
    """Test server expiration after timeout"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
    )

    server = server_browser.get_server("server-1")
    assert server is not None

    # Manually set old heartbeat
    server.last_heartbeat = time.time() - 100

    # Check expiration
    assert server.is_expired(timeout=90) is True


@pytest.mark.asyncio
async def test_server_to_dict(server_browser):
    """Test server serialization"""
    await server_browser.register_server(
        server_id="server-1",
        name="Server 1",
        game="Minecraft",
        host_peer_id="peer1",
        host_peer_name="Alice",
        host_ip="10.66.0.2",
        max_players=10,
        current_players=5,
        map_name="Skyblock",
        tags=["pvp"],
    )

    server = server_browser.get_server("server-1")
    data = server.to_dict()

    # Verify it's a GameServer instance
    assert isinstance(server, GameServer)

    assert data["id"] == "server-1"
    assert data["name"] == "Server 1"
    assert data["game"] == "Minecraft"
    assert data["current_players"] == 5
    assert data["max_players"] == 10
    assert data["map_name"] == "Skyblock"
    assert "pvp" in data["tags"]
    assert "is_full" in data
    assert "age_seconds" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
