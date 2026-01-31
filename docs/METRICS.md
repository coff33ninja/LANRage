# Metrics Collection and Statistics

The metrics system (`core/metrics.py`) provides comprehensive monitoring of network performance, peer connections, system resources, and game sessions.

## Overview

The `MetricsCollector` class tracks:
- **Peer Metrics**: Latency, bandwidth, packet counts, connection status
- **System Metrics**: CPU, memory, network usage over time
- **Game Sessions**: Session history with performance statistics
- **Network Quality**: Overall quality scoring (0-100)

All metrics are stored in memory with configurable retention (default: 360 data points = 1 hour at 10s intervals).

---

## Classes

### MetricPoint

Single metric data point with timestamp.

**Attributes:**
- `timestamp` (float): Unix timestamp
- `value` (float): Metric value

### PeerMetrics

Metrics for a specific peer connection.

**Attributes:**
- `peer_id` (str): Unique peer identifier
- `peer_name` (str): Human-readable peer name
- `latency` (Deque[MetricPoint]): Latency history (max 360 points)
- `bytes_sent` (int): Total bytes sent to peer
- `bytes_received` (int): Total bytes received from peer
- `packets_sent` (int): Total packets sent
- `packets_received` (int): Total packets received
- `connection_uptime` (float): Connection duration in seconds
- `last_seen` (float): Last activity timestamp
- `status` (str): Connection status ("connected", "degraded", "disconnected")

**Status Logic:**
- `connected`: Latency ≤ 200ms
- `degraded`: Latency > 200ms or no recent latency data
- `disconnected`: Peer removed from tracking

### SystemMetrics

System-level resource metrics.

**Attributes:**
- `cpu_percent` (Deque[MetricPoint]): CPU usage history (0-100%)
- `memory_percent` (Deque[MetricPoint]): Memory usage history (0-100%)
- `network_sent` (Deque[MetricPoint]): Network send rate (bytes/sec)
- `network_received` (Deque[MetricPoint]): Network receive rate (bytes/sec)

### GameSession

Record of a completed or active game session.

**Attributes:**
- `game_id` (str): Unique game identifier
- `game_name` (str): Human-readable game name
- `started_at` (float): Session start timestamp
- `ended_at` (Optional[float]): Session end timestamp (None if active)
- `duration` (Optional[float]): Session duration in seconds
- `peers` (List[str]): List of peer IDs in session
- `avg_latency` (Optional[float]): Average latency during session
- `max_latency` (Optional[float]): Maximum latency during session
- `min_latency` (Optional[float]): Minimum latency during session

---

## MetricsCollector

Main metrics collection and storage class.

### Initialization

```python
from core.config import Config
from core.metrics import MetricsCollector

config = await Config.load()
metrics = MetricsCollector(config)
```

**Parameters:**
- `config` (Config): LANrage configuration

**Attributes:**
- `collection_interval` (int): Seconds between system metric collections (default: 10)
- `peer_metrics` (Dict[str, PeerMetrics]): Per-peer metrics storage
- `system_metrics` (SystemMetrics): System resource metrics
- `game_sessions` (Deque[GameSession]): Game session history (max 100)
- `active_session` (Optional[GameSession]): Currently active game session

### Methods

#### start()

Start metrics collection background tasks.

```python
await metrics.start()
```

**Behavior:**
- Initializes network baseline for delta calculations
- Starts system metrics collection loop (every 10 seconds)
- Collects CPU, memory, and network usage

**Returns:** None

---

#### stop()

Stop metrics collection.

```python
await metrics.stop()
```

**Behavior:**
- Stops collection loop
- Preserves collected data in memory

**Returns:** None

---

#### add_peer(peer_id, peer_name)

Add a peer to track.

```python
metrics.add_peer("peer-123", "Alice")
```

**Parameters:**
- `peer_id` (str): Unique peer identifier
- `peer_name` (str): Human-readable name

**Behavior:**
- Creates new `PeerMetrics` instance
- Initializes with "connected" status
- Idempotent (safe to call multiple times)

**Returns:** None

---

#### remove_peer(peer_id)

Remove a peer from tracking.

```python
metrics.remove_peer("peer-123")
```

**Parameters:**
- `peer_id` (str): Peer identifier

**Behavior:**
- Sets peer status to "disconnected"
- Preserves historical data

**Returns:** None

---

#### record_latency(peer_id, latency)

Record latency measurement for a peer.

```python
metrics.record_latency("peer-123", 45.2)  # 45.2ms
```

**Parameters:**
- `peer_id` (str): Peer identifier
- `latency` (Optional[float]): Latency in milliseconds (None = connection issue)

**Behavior:**
- Appends latency to peer's history (max 360 points)
- Updates `last_seen` timestamp
- Updates status: "connected" if ≤200ms, "degraded" if >200ms or None

**Returns:** None

---

#### record_bandwidth(peer_id, bytes_sent, bytes_received)

Record bandwidth usage for a peer.

```python
metrics.record_bandwidth("peer-123", bytes_sent=1024, bytes_received=2048)
```

**Parameters:**
- `peer_id` (str): Peer identifier
- `bytes_sent` (int): Bytes sent since last call (default: 0)
- `bytes_received` (int): Bytes received since last call (default: 0)

**Behavior:**
- Accumulates to peer's total bandwidth counters

**Returns:** None

---

#### start_game_session(game_id, game_name, peers)

Start tracking a game session.

```python
metrics.start_game_session(
    game_id="minecraft-123",
    game_name="Minecraft",
    peers=["peer-1", "peer-2", "peer-3"]
)
```

**Parameters:**
- `game_id` (str): Unique game session identifier
- `game_name` (str): Human-readable game name
- `peers` (List[str]): List of peer IDs in session

**Behavior:**
- Creates new `GameSession` instance
- Sets as `active_session`
- Records start timestamp

**Returns:** None

---

#### end_game_session()

End the current game session.

```python
metrics.end_game_session()
```

**Behavior:**
- Records end timestamp and calculates duration
- Calculates latency statistics (avg, min, max) from peer data
- Stores session in history (max 100 sessions)
- Clears `active_session`

**Returns:** None

---

#### get_peer_summary(peer_id)

Get summary statistics for a peer.

```python
summary = metrics.get_peer_summary("peer-123")
```

**Parameters:**
- `peer_id` (str): Peer identifier

**Returns:** Optional[dict] with structure:
```python
{
    "peer_id": "peer-123",
    "peer_name": "Alice",
    "status": "connected",
    "latency": {
        "current": 45.2,      # Most recent latency (ms)
        "average": 48.5,      # Average latency (ms)
        "min": 42.1,          # Minimum latency (ms)
        "max": 67.3           # Maximum latency (ms)
    },
    "bandwidth": {
        "sent": 1048576,      # Total bytes sent
        "received": 2097152   # Total bytes received
    },
    "packets": {
        "sent": 1024,         # Total packets sent
        "received": 2048      # Total packets received
    },
    "uptime": 3600.0,         # Seconds since last seen
    "last_seen": 1706544000.0 # Unix timestamp
}
```

Returns `None` if peer not found.

---

#### get_all_peers_summary()

Get summary for all tracked peers.

```python
summaries = metrics.get_all_peers_summary()
```

**Returns:** List[dict] - List of peer summaries (see `get_peer_summary` format)

---

#### get_system_summary()

Get system metrics summary.

```python
summary = metrics.get_system_summary()
```

**Returns:** dict with structure:
```python
{
    "cpu": {
        "current": 15.2,      # Current CPU usage (%)
        "average": 12.8,      # Average CPU usage (%)
        "max": 45.6           # Maximum CPU usage (%)
    },
    "memory": {
        "current": 42.3,      # Current memory usage (%)
        "average": 40.1,      # Average memory usage (%)
        "max": 48.9           # Maximum memory usage (%)
    },
    "network": {
        "sent_rate": 102400,  # Current send rate (bytes/sec)
        "recv_rate": 204800,  # Current receive rate (bytes/sec)
        "total_sent": 3686400,    # Total bytes sent (estimated)
        "total_recv": 7372800     # Total bytes received (estimated)
    }
}
```

---

#### get_latency_history(peer_id, duration)

Get latency history for a peer.

```python
history = metrics.get_latency_history("peer-123", duration=3600)  # Last hour
```

**Parameters:**
- `peer_id` (str): Peer identifier
- `duration` (int): Duration in seconds (default: 3600 = 1 hour)

**Returns:** List[dict] with structure:
```python
[
    {"timestamp": 1706544000.0, "value": 45.2},
    {"timestamp": 1706544010.0, "value": 46.1},
    ...
]
```

Returns empty list if peer not found or no data in timeframe.

---

#### get_system_history(duration)

Get system metrics history.

```python
history = metrics.get_system_history(duration=3600)  # Last hour
```

**Parameters:**
- `duration` (int): Duration in seconds (default: 3600 = 1 hour)

**Returns:** dict with structure:
```python
{
    "cpu": [
        {"timestamp": 1706544000.0, "value": 15.2},
        ...
    ],
    "memory": [
        {"timestamp": 1706544000.0, "value": 42.3},
        ...
    ],
    "network_sent": [
        {"timestamp": 1706544000.0, "value": 102400},
        ...
    ],
    "network_received": [
        {"timestamp": 1706544000.0, "value": 204800},
        ...
    ]
}
```

---

#### get_game_sessions(limit)

Get recent game sessions.

```python
sessions = metrics.get_game_sessions(limit=10)
```

**Parameters:**
- `limit` (int): Maximum sessions to return (default: 10)

**Returns:** List[dict] with structure:
```python
[
    {
        "game_id": "minecraft-123",
        "game_name": "Minecraft",
        "started_at": 1706544000.0,
        "ended_at": 1706547600.0,
        "duration": 3600.0,
        "peers": ["peer-1", "peer-2", "peer-3"],
        "latency": {
            "average": 48.5,
            "min": 42.1,
            "max": 67.3
        }
    },
    ...
]
```

---

#### get_network_quality_score()

Calculate overall network quality score.

```python
score = metrics.get_network_quality_score()  # Returns 0-100
```

**Returns:** float (0-100)

**Calculation:**
- **Peer Latency Score**: 100 at 0ms, 0 at 500ms (linear)
- **CPU Score**: 100 at 0%, 0 at 100% (linear)
- **Final Score**: Average of all component scores

**Interpretation:**
- 90-100: Excellent
- 75-89: Good
- 60-74: Fair
- 40-59: Poor
- 0-39: Critical

---

## Usage Examples

### Basic Setup

```python
from core.config import Config
from core.metrics import MetricsCollector

# Initialize
config = await Config.load()
metrics = MetricsCollector(config)

# Start collection
await metrics.start()

# Add peers
metrics.add_peer("peer-1", "Alice")
metrics.add_peer("peer-2", "Bob")

# Record metrics
metrics.record_latency("peer-1", 45.2)
metrics.record_bandwidth("peer-1", bytes_sent=1024, bytes_received=2048)

# Get summaries
peer_summary = metrics.get_peer_summary("peer-1")
system_summary = metrics.get_system_summary()
quality_score = metrics.get_network_quality_score()

# Stop collection
await metrics.stop()
```

### Game Session Tracking

```python
# Start game session
metrics.start_game_session(
    game_id="minecraft-session-1",
    game_name="Minecraft",
    peers=["peer-1", "peer-2", "peer-3"]
)

# ... game plays ...

# End session
metrics.end_game_session()

# Get session history
sessions = metrics.get_game_sessions(limit=5)
for session in sessions:
    print(f"{session['game_name']}: {session['duration']}s, "
          f"avg latency: {session['latency']['average']}ms")
```

### Real-time Monitoring

```python
import asyncio

async def monitor_network():
    while True:
        # Get current stats
        peers = metrics.get_all_peers_summary()
        system = metrics.get_system_summary()
        quality = metrics.get_network_quality_score()
        
        print(f"Network Quality: {quality:.1f}/100")
        print(f"CPU: {system['cpu']['current']:.1f}%")
        print(f"Memory: {system['memory']['current']:.1f}%")
        
        for peer in peers:
            print(f"  {peer['peer_name']}: {peer['latency']['current']:.1f}ms "
                  f"({peer['status']})")
        
        await asyncio.sleep(5)

# Run monitoring
asyncio.create_task(monitor_network())
```

---

## Performance Characteristics

### Memory Usage

- **Per Peer**: ~50KB (360 latency points + metadata)
- **System Metrics**: ~100KB (4 metrics × 360 points)
- **Game Sessions**: ~5KB per session (max 100 = 500KB)
- **Total**: ~1-2MB for typical usage (10 peers)

### CPU Usage

- **Collection Loop**: <1% CPU (runs every 10 seconds)
- **Metric Recording**: <0.1ms per call
- **Summary Generation**: <1ms per peer

### Data Retention

- **Latency History**: 360 points = 1 hour at 10s intervals
- **System Metrics**: 360 points = 1 hour at 10s intervals
- **Game Sessions**: Last 100 sessions (typically days/weeks of history)

---

## Integration with API

The metrics system integrates with the REST API (`api/server.py`):

### Endpoints

- `GET /api/metrics/summary` - Overall metrics summary
- `GET /api/metrics/peers` - All peer metrics
- `GET /api/metrics/peers/{peer_id}` - Specific peer metrics
- `GET /api/metrics/peers/{peer_id}/latency?duration=3600` - Peer latency history
- `GET /api/metrics/system` - System metrics summary
- `GET /api/metrics/system/history?duration=3600` - System metrics history
- `GET /api/metrics/sessions?limit=10` - Game session history

See `docs/API.md` for full API documentation.

---

## Future Enhancements

1. **Persistent Storage**: Save metrics to SQLite for long-term analysis
2. **Alerting**: Trigger alerts on quality degradation
3. **Bandwidth Tracking**: Automatic bandwidth measurement per peer
4. **Packet Loss**: Track packet loss rates
5. **Jitter**: Measure latency variance
6. **Export**: Export metrics to CSV/JSON for external analysis
7. **Grafana Integration**: Prometheus exporter for Grafana dashboards
8. **Predictive Analysis**: ML-based quality prediction
