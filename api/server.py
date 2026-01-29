"""FastAPI server for local control"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from core.config import Config
from core.party import PartyManager
from core.network import NetworkManager


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


# Global state (injected at startup)
party_manager: PartyManager | None = None
network_manager: NetworkManager | None = None


class CreatePartyRequest(BaseModel):
    name: str


class JoinPartyRequest(BaseModel):
    party_id: str
    peer_name: str


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
    except NotImplementedError:
        raise HTTPException(501, "Party joining not yet implemented")


@app.post("/party/leave")
async def leave_party():
    """Leave current party"""
    if not party_manager:
        raise HTTPException(500, "Party manager not initialized")
    
    await party_manager.leave_party()
    return {"status": "left"}


async def start_api_server(config: Config, party: PartyManager, network: NetworkManager):
    """Start the API server"""
    global party_manager, network_manager
    party_manager = party
    network_manager = network
    
    server_config = uvicorn.Config(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info"
    )
    server = uvicorn.Server(server_config)
    await server.serve()
