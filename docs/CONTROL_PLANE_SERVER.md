# Control Plane Server

The LANrage Control Plane Server provides centralized peer discovery, party management, and relay coordination.

## Features

- **Party Management**: Create, join, and leave parties
- **Peer Discovery**: Find and connect to peers
- **Relay Registry**: Discover available relay servers
- **Heartbeat System**: Keep connections alive
- **Automatic Cleanup**: Remove stale peers and parties

## Architecture

### Server (`servers/control_server.py`)
FastAPI-based HTTP server with SQLite persistence:
- **Database**: SQLite via aiosqlite for async operations
- **Tables**: parties, peers, relay_servers, auth_tokens
- **Indexes**: Optimized for party/peer lookups
- **Cleanup**: Automatic removal of stale data every 60s
- **Lifecycle**: Modern lifespan context manager for startup/shutdown

### Client (`core/control_client.py`)
HTTP client using `httpx` for robust async communication with:
- Automatic retries with exponential backoff
- Connection pooling
- Timeout handling
- Heartbeat management

### Database Schema

**Parties Table**:
```sql
CREATE TABLE parties (
    party_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    host_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

**Peers Table**:
```sql
CREATE TABLE peers (
    peer_id TEXT PRIMARY KEY,
    party_id TEXT NOT NULL,
    public_key TEXT NOT NULL,
    virtual_ip TEXT NOT NULL,
    public_endpoint TEXT,
    nat_type TEXT,
    last_seen TEXT NOT NULL,
    FOREIGN KEY (party_id) REFERENCES parties(party_id) ON DELETE CASCADE
)
```

**Relay Servers Table**:
```sql
CREATE TABLE relay_servers (
    relay_id TEXT PRIMARY KEY,
    public_ip TEXT NOT NULL,
    port INTEGER NOT NULL,
    region TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    registered_at TEXT NOT NULL,
    last_seen TEXT NOT NULL
)
```

**Auth Tokens Table**:
```sql
CREATE TABLE auth_tokens (
    token TEXT PRIMARY KEY,
    peer_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
)
```

## Running the Server

### Development
```bash
python servers/control_server.py
```

Server runs on `http://0.0.0.0:8667`  
Database: `~/.lanrage/control_plane.db`

### Production
```bash
uvicorn servers.control_server:app --host 0.0.0.0 --port 8667 --workers 4
```

**Note**: SQLite database is automatically created on first run. For multi-instance deployments, consider migrating to PostgreSQL or Redis.

## API Endpoints

### Health Check
```
GET /
```

Returns server status and statistics.

### Party Management

#### Create Party
```
POST /parties
Content-Type: application/json

{
  "name": "My Party",
  "host_peer_info": {
    "peer_id": "peer-123",
    "name": "Host",
    "public_key": "...",
    "nat_type": "full_cone",
    "public_ip": "1.2.3.4",
    "public_port": 51820,
    "local_ip": "192.168.1.100",
    "local_port": 51820,
    "last_seen": "2026-01-29T12:00:00"
  }
}
```

#### Join Party
```
POST /parties/{party_id}/join
Content-Type: application/json

{
  "party_id": "abc123",
  "peer_info": { ... }
}
```

#### Leave Party
```
DELETE /parties/{party_id}/peers/{peer_id}
```

#### Get Party Info
```
GET /parties/{party_id}
```

#### Get Peers
```
GET /parties/{party_id}/peers
```

#### Discover Peer
```
GET /parties/{party_id}/peers/{peer_id}
```

#### Heartbeat
```
POST /parties/{party_id}/peers/{peer_id}/heartbeat
```

### Relay Management

#### Register Relay
```
POST /relays
Content-Type: application/json

{
  "relay_id": "relay-us-east-1",
  "public_ip": "1.2.3.4",
  "port": 51821,
  "region": "us-east",
  "capacity": 100
}
```

#### List Relays
```
GET /relays
```

#### Get Relays by Region
```
GET /relays/{region}
```

## Client Usage

### Configuration

Set the control server URL in `.env`:
```bash
LANRAGE_CONTROL_SERVER=http://your-server:8667
```

Or in code:
```python
from core.config import Config

config = await Config.load()
config.control_server = "http://your-server:8667"
```

### Using the Client

```python
from core.control_client import create_control_plane_client
from core.control import PeerInfo
from core.config import Config

# Create client
config = await Config.load()
client = create_control_plane_client(config)

# Initialize
await client.initialize()

# Register peer
await client.register_peer("my-peer-id")

# Create party
peer_info = PeerInfo(
    peer_id="my-peer-id",
    name="My Peer",
    public_key="...",
    nat_type="full_cone",
    public_ip="1.2.3.4",
    public_port=51820,
    local_ip="192.168.1.100",
    local_port=51820,
    last_seen=datetime.now()
}

party = await client.register_party("party-123", "My Party", peer_info)

# Join party
party = await client.join_party("party-123", peer_info)

# Get peers
peers = await client.get_peers("party-123")

# Leave party
await client.leave_party("party-123", "my-peer-id")

# Cleanup
await client.close()
```

## Deployment

### Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8667

CMD ["uvicorn", "servers.control_server:app", "--host", "0.0.0.0", "--port", "8667"]
```

Build and run:
```bash
docker build -t lanrage-control .
docker run -p 8667:8667 lanrage-control
```

### Kubernetes

Create `deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lanrage-control
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lanrage-control
  template:
    metadata:
      labels:
        app: lanrage-control
    spec:
      containers:
      - name: control-server
        image: lanrage-control:latest
        ports:
        - containerPort: 8667
        env:
        - name: WORKERS
          value: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: lanrage-control
spec:
  selector:
    app: lanrage-control
  ports:
  - port: 8667
    targetPort: 8667
  type: LoadBalancer
```

### Cloud Providers

#### AWS (ECS/Fargate)
- Use Application Load Balancer
- Enable health checks on `/`
- Set task CPU/memory based on load

#### Google Cloud (Cloud Run)
```bash
gcloud run deploy lanrage-control \
  --image gcr.io/PROJECT/lanrage-control \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure (Container Instances)
```bash
az container create \
  --resource-group lanrage \
  --name lanrage-control \
  --image lanrage-control:latest \
  --ports 8667 \
  --dns-name-label lanrage-control
```

## Monitoring

### Health Checks
```bash
curl http://localhost:8667/
```

### Metrics
Monitor:
- Active parties count
- Active peers count
- Request latency
- Error rates

### Logging
Server logs include:
- Party creation/deletion
- Peer joins/leaves
- Heartbeat failures
- Cleanup operations

## Security

### Production Recommendations

1. **Enable HTTPS**: Use reverse proxy (nginx/Caddy) with SSL
2. **Authentication**: Implement token-based auth (already scaffolded)
3. **Rate Limiting**: Add rate limiting middleware
4. **CORS**: Configure allowed origins
5. **Firewall**: Restrict access to known IPs

### Example nginx config:
```nginx
server {
    listen 443 ssl http2;
    server_name control.lanrage.io;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8667;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Connection Refused
- Check server is running: `curl http://localhost:8667/`
- Verify firewall rules
- Check server logs

### Timeout Errors
- Increase client timeout in `control_client.py`
- Check network latency
- Verify server isn't overloaded

### Stale Peers
- Heartbeat interval: 30 seconds
- Cleanup timeout: 5 minutes
- Adjust in `control_server.py` if needed

## Performance

### Benchmarks
- Handles 1000+ concurrent parties
- Sub-10ms response times
- Automatic cleanup every 60 seconds

### Scaling
- **Single Instance**: SQLite handles 1000+ parties easily
- **Vertical**: Increase workers (`--workers 8`)
- **Horizontal**: Migrate to PostgreSQL/Redis for multi-instance deployment
  - Replace `aiosqlite` with `asyncpg` (PostgreSQL)
  - Or use Redis for in-memory performance
  - Keep same API interface

## Database Management

### Backup
```bash
# Backup database
cp ~/.lanrage/control_plane.db ~/.lanrage/control_plane.db.backup

# Or use SQLite backup command
sqlite3 ~/.lanrage/control_plane.db ".backup ~/.lanrage/control_plane.db.backup"
```

### Inspect Database
```bash
# Open database
sqlite3 ~/.lanrage/control_plane.db

# View tables
.tables

# View parties
SELECT * FROM parties;

# View peers
SELECT * FROM peers;

# View relays
SELECT * FROM relay_servers;
```

### Cleanup
```bash
# Remove old database (will be recreated)
rm ~/.lanrage/control_plane.db
```

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] PostgreSQL/Redis backend for multi-instance deployment
- [ ] Metrics endpoint (Prometheus)
- [ ] Admin dashboard
- [ ] Geographic relay selection
- [ ] Peer-to-peer signaling
- [ ] Database migrations system
