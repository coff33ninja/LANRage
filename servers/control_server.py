"""
Control Plane Server - Centralized peer discovery and signaling

This server provides:
- Party registry (create, join, leave)
- Peer discovery
- Relay server registry
- Basic authentication

Uses SQLite database for persistent storage via aiosqlite.
"""

import asyncio
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.control import PartyInfo, PeerInfo
from core.settings import get_settings_db

app = FastAPI(title="LANrage Control Plane", version="1.0.0")

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = Path.home() / ".lanrage" / "control_plane.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# Database initialization
async def init_database():
    """Initialize control plane database schema"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Parties table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS parties (
                party_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                host_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Peers table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS peers (
                peer_id TEXT PRIMARY KEY,
                party_id TEXT NOT NULL,
                public_key TEXT NOT NULL,
                virtual_ip TEXT NOT NULL,
                public_endpoint TEXT,
                nat_type TEXT,
                last_seen TEXT NOT NULL,
                FOREIGN KEY (party_id) REFERENCES parties(party_id) ON DELETE CASCADE
            )
        """)

        # Create index for faster party lookups
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_peers_party_id ON peers(party_id)
        """)

        # Relay servers table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS relay_servers (
                relay_id TEXT PRIMARY KEY,
                public_ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                region TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                registered_at TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)

        # Auth tokens table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                peer_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        # Create index for token expiration cleanup
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tokens_expires_at ON auth_tokens(expires_at)
        """)

        await db.commit()


# Request/Response Models
class CreatePartyRequest(BaseModel):
    """Request to create a party"""

    name: str = Field(..., min_length=1, max_length=100)
    host_peer_info: dict


class JoinPartyRequest(BaseModel):
    """Request to join a party"""

    party_id: str = Field(..., min_length=1)
    peer_info: dict


class UpdatePeerRequest(BaseModel):
    """Request to update peer info"""

    party_id: str
    peer_info: dict


class RegisterRelayRequest(BaseModel):
    """Request to register a relay server"""

    relay_id: str
    public_ip: str
    port: int
    region: str = "unknown"
    capacity: int = 100


class AuthResponse(BaseModel):
    """Authentication response"""

    token: str
    peer_id: str
    expires_at: str


# Authentication helpers
def generate_token() -> str:
    """Generate a secure authentication token"""
    return secrets.token_urlsafe(32)


async def verify_token(authorization: str | None = Header(None)) -> str:
    """Verify authentication token from database"""
    if not authorization:
        raise HTTPException(401, "Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format")

    token = authorization[7:]  # Remove "Bearer " prefix

    async with (
        aiosqlite.connect(DB_PATH) as db,
        db.execute(
            "SELECT peer_id, expires_at FROM auth_tokens WHERE token = ?", (token,)
        ) as cursor,
    ):
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(401, "Invalid or expired token")

        peer_id, expires_at = row
        expires_dt = datetime.fromisoformat(expires_at)

        if datetime.now() > expires_dt:
            # Delete expired token
            await db.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
            await db.commit()
            raise HTTPException(401, "Token expired")

        return peer_id


# Health check
@app.get("/")
async def root():
    """Health check"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Count parties
        async with db.execute("SELECT COUNT(*) FROM parties") as cursor:
            party_count = (await cursor.fetchone())[0]

        # Count relays
        async with db.execute("SELECT COUNT(*) FROM relay_servers") as cursor:
            relay_count = (await cursor.fetchone())[0]

    return {
        "service": "LANrage Control Plane",
        "version": "1.0.0",
        "status": "ok",
        "parties": party_count,
        "relays": relay_count,
    }


# Authentication endpoints
@app.post("/auth/register", response_model=AuthResponse)
async def register_peer(peer_id: str):
    """Register a peer and get authentication token"""
    token = generate_token()
    now = datetime.now()
    expires_at = now + timedelta(hours=24)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO auth_tokens (token, peer_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, peer_id, now.isoformat(), expires_at.isoformat()),
        )
        await db.commit()

    return AuthResponse(
        token=token,
        peer_id=peer_id,
        expires_at=expires_at.isoformat(),
    )


# Party management endpoints
@app.post("/parties")
async def create_party(req: CreatePartyRequest, peer_id: str = Header(None)):
    """Create a new party"""
    try:
        # Create peer info
        host_peer_info = PeerInfo.from_dict(req.host_peer_info)

        # Generate party ID
        party_id = PartyInfo.generate_party_id()
        now = datetime.now()

        async with aiosqlite.connect(DB_PATH) as db:
            # Insert party
            await db.execute(
                """
                INSERT INTO parties (party_id, name, host_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    party_id,
                    req.name,
                    host_peer_info.peer_id,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )

            # Insert host peer
            await db.execute(
                """
                INSERT INTO peers (peer_id, party_id, public_key, virtual_ip, public_endpoint, nat_type, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    host_peer_info.peer_id,
                    party_id,
                    host_peer_info.public_key,
                    host_peer_info.virtual_ip,
                    host_peer_info.public_endpoint,
                    host_peer_info.nat_type,
                    now.isoformat(),
                ),
            )

            await db.commit()

        # Create party object for response
        party = PartyInfo(
            party_id=party_id,
            name=req.name,
            host_id=host_peer_info.peer_id,
            created_at=now,
            peers={host_peer_info.peer_id: host_peer_info},
        )

        return {"party_id": party_id, "party": party.to_dict()}

    except Exception as e:
        raise HTTPException(500, f"Failed to create party: {e}") from e


@app.post("/parties/{party_id}/join")
async def join_party(party_id: str, req: JoinPartyRequest):
    """Join an existing party"""
    try:
        peer_info = PeerInfo.from_dict(req.peer_info)
        now = datetime.now()

        async with aiosqlite.connect(DB_PATH) as db:
            # Check if party exists
            async with db.execute(
                "SELECT party_id FROM parties WHERE party_id = ?", (party_id,)
            ) as cursor:
                if not await cursor.fetchone():
                    raise HTTPException(404, f"Party {party_id} not found")

            # Insert peer
            await db.execute(
                """
                INSERT INTO peers (peer_id, party_id, public_key, virtual_ip, public_endpoint, nat_type, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(peer_id) DO UPDATE SET
                    public_endpoint = excluded.public_endpoint,
                    nat_type = excluded.nat_type,
                    last_seen = excluded.last_seen
                """,
                (
                    peer_info.peer_id,
                    party_id,
                    peer_info.public_key,
                    peer_info.virtual_ip,
                    peer_info.public_endpoint,
                    peer_info.nat_type,
                    now.isoformat(),
                ),
            )

            # Update party timestamp
            await db.execute(
                "UPDATE parties SET updated_at = ? WHERE party_id = ?",
                (now.isoformat(), party_id),
            )

            await db.commit()

        # Get updated party info
        return await get_party(party_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to join party: {e}") from e


@app.delete("/parties/{party_id}/peers/{peer_id}")
async def leave_party(party_id: str, peer_id: str):
    """Leave a party"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if party exists
        async with db.execute(
            "SELECT host_id FROM parties WHERE party_id = ?", (party_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, f"Party {party_id} not found")
            host_id = row[0]

        # Check if peer exists
        async with db.execute(
            "SELECT peer_id FROM peers WHERE party_id = ? AND peer_id = ?",
            (party_id, peer_id),
        ) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(404, f"Peer {peer_id} not in party")

        # Remove peer
        await db.execute(
            "DELETE FROM peers WHERE party_id = ? AND peer_id = ?", (party_id, peer_id)
        )

        # Check if party is empty or host left
        async with db.execute(
            "SELECT COUNT(*) FROM peers WHERE party_id = ?", (party_id,)
        ) as cursor:
            peer_count = (await cursor.fetchone())[0]

        if peer_count == 0 or peer_id == host_id:
            # Delete party
            await db.execute("DELETE FROM parties WHERE party_id = ?", (party_id,))
            await db.commit()
            return {"status": "party_deleted"}

        await db.commit()
        return {"status": "left"}


@app.get("/parties/{party_id}")
async def get_party(party_id: str) -> PartyInfo | None:
    """Get party information"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get party
        async with db.execute(
            "SELECT name, host_id, created_at FROM parties WHERE party_id = ?",
            (party_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, f"Party {party_id} not found")

            name, host_id, created_at = row

        # Get all peers
        peers = {}
        async with db.execute(
            "SELECT peer_id, public_key, virtual_ip, public_endpoint, nat_type, last_seen FROM peers WHERE party_id = ?",
            (party_id,),
        ) as cursor:
            async for row in cursor:
                (
                    peer_id,
                    public_key,
                    virtual_ip,
                    public_endpoint,
                    nat_type,
                    last_seen,
                ) = row
                peers[peer_id] = PeerInfo(
                    peer_id=peer_id,
                    public_key=public_key,
                    virtual_ip=virtual_ip,
                    public_endpoint=public_endpoint,
                    nat_type=nat_type,
                    last_seen=datetime.fromisoformat(last_seen),
                )

        party = PartyInfo(
            party_id=party_id,
            name=name,
            host_id=host_id,
            created_at=datetime.fromisoformat(created_at),
            peers=peers,
        )

        return {"party": party.to_dict()}


@app.get("/parties/{party_id}/peers")
async def get_peers(party_id: str):
    """Get all peers in a party"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if party exists
        async with db.execute(
            "SELECT party_id FROM parties WHERE party_id = ?", (party_id,)
        ) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(404, f"Party {party_id} not found")

        # Get all peers
        peers = {}
        async with db.execute(
            "SELECT peer_id, public_key, virtual_ip, public_endpoint, nat_type, last_seen FROM peers WHERE party_id = ?",
            (party_id,),
        ) as cursor:
            async for row in cursor:
                (
                    peer_id,
                    public_key,
                    virtual_ip,
                    public_endpoint,
                    nat_type,
                    last_seen,
                ) = row
                peer = PeerInfo(
                    peer_id=peer_id,
                    public_key=public_key,
                    virtual_ip=virtual_ip,
                    public_endpoint=public_endpoint,
                    nat_type=nat_type,
                    last_seen=datetime.fromisoformat(last_seen),
                )
                peers[peer_id] = peer.to_dict()

        return {"peers": peers}


@app.get("/parties/{party_id}/peers/{peer_id}")
async def discover_peer(party_id: str, peer_id: str):
    """Discover a specific peer"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if party exists
        async with db.execute(
            "SELECT party_id FROM parties WHERE party_id = ?", (party_id,)
        ) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(404, f"Party {party_id} not found")

        # Get peer
        async with db.execute(
            "SELECT public_key, virtual_ip, public_endpoint, nat_type, last_seen FROM peers WHERE party_id = ? AND peer_id = ?",
            (party_id, peer_id),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, f"Peer {peer_id} not found")

            public_key, virtual_ip, public_endpoint, nat_type, last_seen = row

            peer = PeerInfo(
                peer_id=peer_id,
                public_key=public_key,
                virtual_ip=virtual_ip,
                public_endpoint=public_endpoint,
                nat_type=nat_type,
                last_seen=datetime.fromisoformat(last_seen),
            )

            return {"peer": peer.to_dict()}


@app.post("/parties/{party_id}/peers/{peer_id}/heartbeat")
async def heartbeat(party_id: str, peer_id: str):
    """Send heartbeat to keep peer alive"""
    now = datetime.now()

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if party exists
        async with db.execute(
            "SELECT party_id FROM parties WHERE party_id = ?", (party_id,)
        ) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(404, f"Party {party_id} not found")

        # Update peer last_seen
        async with db.execute(
            "UPDATE peers SET last_seen = ? WHERE party_id = ? AND peer_id = ?",
            (now.isoformat(), party_id, peer_id),
        ) as cursor:
            if cursor.rowcount == 0:
                raise HTTPException(404, f"Peer {peer_id} not found")

        await db.commit()

    return {"status": "ok"}


# Relay server registry
@app.post("/relays")
async def register_relay(req: RegisterRelayRequest):
    """Register a relay server"""
    now = datetime.now()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO relay_servers (relay_id, public_ip, port, region, capacity, registered_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(relay_id) DO UPDATE SET
                public_ip = excluded.public_ip,
                port = excluded.port,
                region = excluded.region,
                capacity = excluded.capacity,
                last_seen = excluded.last_seen
            """,
            (
                req.relay_id,
                req.public_ip,
                req.port,
                req.region,
                req.capacity,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        await db.commit()

    return {"status": "registered", "relay_id": req.relay_id}


@app.get("/relays")
async def list_relays():
    """List available relay servers"""
    relays = []

    async with (
        aiosqlite.connect(DB_PATH) as db,
        db.execute(
            "SELECT relay_id, public_ip, port, region, capacity, registered_at FROM relay_servers ORDER BY region, relay_id"
        ) as cursor,
    ):
        async for row in cursor:
            relay_id, public_ip, port, region, capacity, registered_at = row
            relays.append(
                {
                    "relay_id": relay_id,
                    "public_ip": public_ip,
                    "port": port,
                    "region": region,
                    "capacity": capacity,
                    "registered_at": registered_at,
                }
            )

    return {"relays": relays}


@app.get("/relays/{region}")
async def get_relays_by_region(region: str):
    """Get relay servers in a specific region"""
    relays = []

    async with (
        aiosqlite.connect(DB_PATH) as db,
        db.execute(
            "SELECT relay_id, public_ip, port, region, capacity, registered_at FROM relay_servers WHERE region = ? ORDER BY relay_id",
            (region,),
        ) as cursor,
    ):
        async for row in cursor:
            relay_id, public_ip, port, region, capacity, registered_at = row
            relays.append(
                {
                    "relay_id": relay_id,
                    "public_ip": public_ip,
                    "port": port,
                    "region": region,
                    "capacity": capacity,
                    "registered_at": registered_at,
                }
            )

    return {"relays": relays}


# Cleanup task
async def cleanup_task():
    """Cleanup stale peers, parties, and expired tokens"""
    while True:
        await asyncio.sleep(60)  # Run every minute

        now = datetime.now()
        peer_timeout = timedelta(minutes=5)
        relay_timeout = timedelta(minutes=10)

        async with aiosqlite.connect(DB_PATH) as db:
            # Delete stale peers
            cutoff_time = (now - peer_timeout).isoformat()
            await db.execute("DELETE FROM peers WHERE last_seen < ?", (cutoff_time,))

            # Delete empty parties
            await db.execute("""
                DELETE FROM parties
                WHERE party_id NOT IN (SELECT DISTINCT party_id FROM peers)
            """)

            # Delete expired tokens
            await db.execute(
                "DELETE FROM auth_tokens WHERE expires_at < ?", (now.isoformat(),)
            )

            # Delete stale relay servers
            relay_cutoff = (now - relay_timeout).isoformat()
            await db.execute(
                "DELETE FROM relay_servers WHERE last_seen < ?", (relay_cutoff,)
            )

            await db.commit()


@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    await init_database()
    asyncio.create_task(cleanup_task())
    print("✓ Control plane server initialized")


async def main():
    """Main entry point"""
    # Load settings from database
    db = await get_settings_db()
    settings = await db.get_all_settings()

    # Create config from settings
    config = Config(
        mode="control",
        api_host=settings.get("api_host", "0.0.0.0"),
        api_port=settings.get("control_plane_port", 8667),
    )

    print("🔥 LANrage Control Plane Server")
    print("=" * 60)
    print(f"Listening on: {config.api_host}:{config.api_port}")
    print(f"Database: {DB_PATH}")
    print("=" * 60)

    # Initialize database
    await init_database()
    print("✓ Database initialized")

    # Start cleanup task
    asyncio.create_task(cleanup_task())
    print("✓ Cleanup task started")

    print("\nControl plane ready for connections...")

    # Run server
    import uvicorn

    uvicorn_config = uvicorn.Config(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info",
    )
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
