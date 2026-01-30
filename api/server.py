"""FastAPI server for local control"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from core.config import Config
from core.network import NetworkManager
from core.party import PartyManager
from core.settings import get_settings_db, init_default_settings

app = FastAPI(title="LANrage API", version="0.1.0")

# Mount static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS for local web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreatePartyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="Party name")


class JoinPartyRequest(BaseModel):
    party_id: str = Field(min_length=1, max_length=20, description="Party ID to join")
    peer_name: str = Field(min_length=1, max_length=50, description="Your display name")


class DiscordWebhookRequest(BaseModel):
    webhook_url: str = Field(min_length=1, description="Discord webhook URL")


class DiscordInviteRequest(BaseModel):
    invite_url: str = Field(min_length=1, description="Discord invite URL")


class RegisterServerRequest(BaseModel):
    server_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100, description="Server name")
    game: str = Field(min_length=1, max_length=50, description="Game name")
    max_players: int = Field(ge=1, le=1000, description="Maximum players")
    current_players: int = Field(ge=0, description="Current player count")
    map_name: str | None = Field(None, max_length=100)
    game_mode: str | None = Field(None, max_length=50)
    password_protected: bool = False
    tags: list[str] | None = Field(None, max_items=10, description="Server tags")

    @field_validator("current_players")
    @classmethod
    def validate_player_count(cls, v, info):
        """Validate current_players doesn't exceed max_players"""
        max_players = info.data.get("max_players")
        if max_players is not None and v > max_players:
            raise ValueError("current_players cannot exceed max_players")
        return v


class UpdatePlayerCountRequest(BaseModel):
    current_players: int = Field(ge=0, description="Current player count")


class SettingsRequest(BaseModel):
    """Settings update request"""

    mode: str | None = None
    peer_name: str | None = None
    interface_name: str | None = None
    virtual_subnet: str | None = None
    wireguard_keepalive: int | None = None
    auto_optimize_games: bool | None = None
    enable_broadcast: bool | None = None
    enable_discord: bool | None = None
    enable_metrics: bool | None = None
    relay_public_ip: str | None = None
    relay_port: int | None = None
    max_clients: int | None = None
    api_host: str | None = None
    api_port: int | None = None
    control_server: str | None = None


class SaveConfigRequest(BaseModel):
    """Save configuration request"""

    name: str
    mode: str
    config: dict


@app.get("/api")
async def root():
    """Health check"""
    return {"status": "ok", "service": "LANrage"}


@app.get("/")
async def serve_ui():
    """Serve the web UI"""
    from fastapi.responses import FileResponse

    ui_path = Path(__file__).parent.parent / "static" / "index.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    return {"error": "UI not found"}


@app.get("/logo.png")
async def serve_logo():
    """Serve the LANrage logo"""
    from fastapi.responses import FileResponse

    logo_path = Path(__file__).parent.parent / "logo.png"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(404, "Logo not found")


@app.get("/status")
async def get_status():
    """Get current status"""
    if not party_manager:
        raise HTTPException(500, "Party manager not initialized")

    return await party_manager.get_party_status()


@app.post("/party/create")
async def create_party(req: CreatePartyRequest):
    """Create a new party"""
    if not party_manager:
        raise HTTPException(500, "Party manager not initialized")

    party = await party_manager.create_party(req.name)
    return {"party_id": party.id, "party": party.model_dump()}


@app.post("/party/join")
async def join_party(req: JoinPartyRequest):
    """Join an existing party"""
    if not party_manager:
        raise HTTPException(500, "Party manager not initialized")

    try:
        party = await party_manager.join_party(req.party_id, req.peer_name)
        return {"party": party.model_dump()}
    except NotImplementedError as e:
        raise HTTPException(501, "Party joining not yet implemented") from e


@app.post("/party/leave")
async def leave_party():
    """Leave current party"""
    if not party_manager:
        raise HTTPException(500, "Party manager not initialized")

    await party_manager.leave_party()
    return {"status": "left"}


# Metrics endpoints


@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Get overall metrics summary"""
    if not metrics_collector:
        raise HTTPException(500, "Metrics collector not initialized")

    return {
        "peers": await metrics_collector.get_all_peers_summary(),
        "system": metrics_collector.get_system_summary(),
        "network_quality": metrics_collector.get_network_quality_score(),
    }


@app.get("/api/metrics/peers")
async def get_peer_metrics():
    """Get metrics for all peers"""
    if not metrics_collector:
        raise HTTPException(500, "Metrics collector not initialized")

    return {"peers": await metrics_collector.get_all_peers_summary()}


@app.get("/api/metrics/peers/{peer_id}")
async def get_peer_metric(peer_id: str):
    """Get metrics for a specific peer"""
    if not metrics_collector:
        raise HTTPException(500, "Metrics collector not initialized")

    summary = metrics_collector.get_peer_summary(peer_id)
    if not summary:
        raise HTTPException(404, f"Peer {peer_id} not found")

    return summary


@app.get("/api/metrics/peers/{peer_id}/latency")
async def get_peer_latency_history(peer_id: str, duration: int = 3600):
    """Get latency history for a peer

    Args:
        peer_id: Peer ID
        duration: Duration in seconds (default 3600 = 1 hour)
    """
    if not metrics_collector:
        raise HTTPException(500, "Metrics collector not initialized")

    history = metrics_collector.get_latency_history(peer_id, duration)
    return {"peer_id": peer_id, "duration": duration, "data": history}


@app.get("/api/metrics/system")
async def get_system_metrics():
    """Get system metrics summary"""
    if not metrics_collector:
        raise HTTPException(500, "Metrics collector not initialized")

    return metrics_collector.get_system_summary()


@app.get("/api/metrics/system/history")
async def get_system_history(duration: int = 3600):
    """Get system metrics history

    Args:
        duration: Duration in seconds (default 3600 = 1 hour)
    """
    if not metrics_collector:
        raise HTTPException(500, "Metrics collector not initialized")

    history = metrics_collector.get_system_history(duration)
    return {"duration": duration, "data": history}


@app.get("/api/metrics/sessions")
async def get_game_sessions(limit: int = 10):
    """Get recent game sessions

    Args:
        limit: Maximum number of sessions to return (default 10)
    """
    if not metrics_collector:
        raise HTTPException(500, "Metrics collector not initialized")

    sessions = metrics_collector.get_game_sessions(limit)
    return {"sessions": sessions}


# Discord integration endpoints


@app.post("/api/discord/webhook")
async def set_discord_webhook(req: DiscordWebhookRequest):
    """Set Discord webhook URL for notifications"""
    if not discord_integration:
        raise HTTPException(500, "Discord integration not initialized")

    from core.discord_integration import DiscordWebhookHelper

    if not DiscordWebhookHelper.validate_webhook_url(req.webhook_url):
        raise HTTPException(400, "Invalid webhook URL format")

    discord_integration.set_webhook(req.webhook_url)
    return {"status": "ok", "message": "Discord webhook configured"}


@app.post("/api/discord/invite")
async def set_discord_invite(req: DiscordInviteRequest):
    """Set Discord invite URL for voice chat"""
    if not discord_integration:
        raise HTTPException(500, "Discord integration not initialized")

    from core.discord_integration import DiscordWebhookHelper

    if not DiscordWebhookHelper.validate_invite_url(req.invite_url):
        raise HTTPException(400, "Invalid invite URL format")

    discord_integration.set_party_invite(req.invite_url)
    return {"status": "ok", "message": "Discord invite configured"}


@app.get("/api/discord/status")
async def get_discord_status():
    """Get Discord integration status"""
    if not discord_integration:
        raise HTTPException(500, "Discord integration not initialized")

    return {
        "webhook_configured": discord_integration.webhook_url is not None,
        "invite_configured": discord_integration.party_invite_url is not None,
        "invite_url": discord_integration.get_party_invite_link(),
        "rich_presence": discord_integration.rpc_connected,
    }


@app.get("/api/discord/instructions")
async def get_discord_instructions():
    """Get instructions for setting up Discord integration"""
    from core.discord_integration import DiscordWebhookHelper

    return {
        "webhook": DiscordWebhookHelper.get_webhook_instructions(),
        "invite": DiscordWebhookHelper.get_invite_instructions(),
    }


@app.post("/api/discord/test")
async def test_discord_notification():
    """Send a test notification to Discord"""
    if not discord_integration:
        raise HTTPException(500, "Discord integration not initialized")

    if not discord_integration.webhook_url:
        raise HTTPException(400, "Discord webhook not configured")

    await discord_integration.send_notification(
        "🧪 Test Notification",
        "LANrage Discord integration is working!",
        color=0x4CAF50,
    )

    return {"status": "ok", "message": "Test notification sent"}


# Server browser endpoints


@app.get("/api/servers")
async def list_servers(
    game: str | None = None,
    hide_full: bool = False,
    hide_empty: bool = False,
    hide_password: bool = False,
    tags: str | None = None,
    search: str | None = None,
):
    """List all game servers with optional filtering"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    tag_list = tags.split(",") if tags else None
    servers = server_browser.list_servers(
        game=game,
        hide_full=hide_full,
        hide_empty=hide_empty,
        hide_password=hide_password,
        tags=tag_list,
        search=search,
    )

    return {
        "servers": [s.to_dict() for s in servers],
        "count": len(servers),
        "stats": server_browser.get_stats(),
    }


@app.post("/api/servers")
async def register_server(req: RegisterServerRequest):
    """Register a new game server"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    if not party_manager or not party_manager.current_party:
        raise HTTPException(400, "Must be in a party to register a server")

    # Get host info from party
    party = party_manager.current_party
    host_peer = party.peers.get(party.host_peer_id)
    if not host_peer:
        raise HTTPException(500, "Host peer not found")

    server = await server_browser.register_server(
        server_id=req.server_id,
        name=req.name,
        game=req.game,
        host_peer_id=party.host_peer_id,
        host_peer_name=host_peer.name,
        host_ip=host_peer.virtual_ip,
        max_players=req.max_players,
        current_players=req.current_players,
        map_name=req.map_name,
        game_mode=req.game_mode,
        password_protected=req.password_protected,
        tags=req.tags,
    )

    return {"status": "ok", "server": server.to_dict()}


@app.get("/api/servers/{server_id}")
async def get_server(server_id: str):
    """Get details for a specific server"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    server = server_browser.get_server(server_id)
    if not server:
        raise HTTPException(404, f"Server {server_id} not found")

    return server.to_dict()


@app.delete("/api/servers/{server_id}")
async def unregister_server(server_id: str):
    """Unregister a game server"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    success = await server_browser.unregister_server(server_id)
    if not success:
        raise HTTPException(404, f"Server {server_id} not found")

    return {"status": "ok", "message": "Server unregistered"}


@app.post("/api/servers/{server_id}/heartbeat")
async def server_heartbeat(server_id: str):
    """Update server heartbeat"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    success = await server_browser.update_heartbeat(server_id)
    if not success:
        raise HTTPException(404, f"Server {server_id} not found")

    return {"status": "ok", "message": "Heartbeat updated"}


@app.post("/api/servers/{server_id}/players")
async def update_player_count(server_id: str, req: UpdatePlayerCountRequest):
    """Update server player count"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    success = await server_browser.update_player_count(server_id, req.current_players)
    if not success:
        raise HTTPException(404, f"Server {server_id} not found")

    return {"status": "ok", "message": "Player count updated"}


@app.post("/api/servers/{server_id}/join")
async def join_server(server_id: str):
    """Join a game server (connects to host's party)"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    if not party_manager:
        raise HTTPException(500, "Party manager not initialized")

    server = server_browser.get_server(server_id)
    if not server:
        raise HTTPException(404, f"Server {server_id} not found")

    if server.current_players >= server.max_players:
        raise HTTPException(400, "Server is full")

    # Automatic party joining
    try:
        # Use the server_id as party_id (they should match)
        party = await party_manager.join_party(
            party_id=server_id, peer_name=party_manager.config.peer_name
        )

        return {
            "status": "ok",
            "message": f"Successfully joined {server.name}",
            "server": server.to_dict(),
            "party": party.model_dump(),
        }
    except NotImplementedError as e:
        # Fallback if control plane not initialized
        raise HTTPException(501, f"Party joining not available: {e}") from e
    except Exception as e:
        # Handle other errors gracefully
        raise HTTPException(500, f"Failed to join party: {e}") from e


@app.post("/api/servers/{server_id}/favorite")
async def add_favorite(server_id: str):
    """Add server to favorites"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    server = server_browser.get_server(server_id)
    if not server:
        raise HTTPException(404, f"Server {server_id} not found")

    server_browser.add_favorite(server_id)
    return {"status": "ok", "message": "Server added to favorites"}


@app.delete("/api/servers/{server_id}/favorite")
async def remove_favorite(server_id: str):
    """Remove server from favorites"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    server_browser.remove_favorite(server_id)
    return {"status": "ok", "message": "Server removed from favorites"}


@app.get("/api/servers/{server_id}/latency")
async def measure_server_latency(server_id: str):
    """Measure latency to a server"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    latency = await server_browser.measure_latency(server_id)
    if latency is None:
        raise HTTPException(500, "Failed to measure latency")

    return {"server_id": server_id, "latency_ms": latency}


@app.get("/api/servers/stats")
async def get_server_stats():
    """Get server browser statistics"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    return server_browser.get_stats()


@app.get("/api/games")
async def list_games():
    """Get list of games with active servers"""
    if not server_browser:
        raise HTTPException(500, "Server browser not initialized")

    games = server_browser.get_games_list()
    return {"games": games, "count": len(games)}


# Settings endpoints


@app.get("/api/settings")
async def get_settings():
    """Get all settings"""
    db = await get_settings_db()
    return await db.get_all_settings()


@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    """Update settings"""
    db = await get_settings_db()

    # Update each provided setting
    updates = req.model_dump(exclude_none=True)
    for key, value in updates.items():
        await db.set_setting(key, value)

    return {
        "status": "ok",
        "message": "Settings updated",
        "updated": list(updates.keys()),
    }


@app.post("/api/settings/reset")
async def reset_settings():
    """Reset settings to defaults"""
    db = await get_settings_db()

    # Get all current settings
    current = await db.get_all_settings()

    # Delete all settings
    for key in current:
        await db.delete_setting(key)

    # Reinitialize defaults
    await init_default_settings()

    return {"status": "ok", "message": "Settings reset to defaults"}


@app.get("/api/settings/configs")
async def get_saved_configs():
    """Get all saved configurations"""
    db = await get_settings_db()
    return await db.get_all_server_configs()


@app.post("/api/settings/configs")
async def save_config(req: SaveConfigRequest):
    """Save a new configuration"""
    db = await get_settings_db()
    config_id = await db.save_server_config(req.name, req.mode, req.config)
    return {"status": "ok", "message": "Configuration saved", "id": config_id}


@app.post("/api/settings/configs/{config_id}/activate")
async def activate_config(config_id: int):
    """Activate a saved configuration"""
    db = await get_settings_db()

    # Get the configuration
    config = await db.get_server_config(config_id)
    if not config:
        raise HTTPException(404, f"Configuration {config_id} not found")

    # Apply all settings from the config
    for key, value in config["config"].items():
        await db.set_setting(key, value)

    # Set mode
    await db.set_setting("mode", config["mode"])

    # Enable this config, disable others
    all_configs = await db.get_all_server_configs()
    for cfg in all_configs:
        await db.toggle_server_config(cfg["id"], cfg["id"] == config_id)

    return {"status": "ok", "message": "Configuration activated"}


@app.delete("/api/settings/configs/{config_id}")
async def delete_config(config_id: int):
    """Delete a saved configuration"""
    db = await get_settings_db()
    await db.delete_server_config(config_id)
    return {"status": "ok", "message": "Configuration deleted"}


async def start_api_server(
    config: Config,
    party: PartyManager,
    network: NetworkManager,
    metrics=None,
    discord=None,
    browser=None,
):
    """Start the API server"""
    global party_manager, network_manager, metrics_collector, discord_integration, server_browser
    party_manager = party
    network_manager = network
    metrics_collector = metrics
    discord_integration = discord
    server_browser = browser

    server_config = uvicorn.Config(
        app, host=config.api_host, port=config.api_port, log_level="info"
    )
    server = uvicorn.Server(server_config)
    await server.serve()
