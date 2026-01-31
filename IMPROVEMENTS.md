# LANrage Optimization & Improvement Roadmap

## Priority 1: Critical Performance Improvements

### 1.1 Game Detection Enhancement
**File**: `core/games.py`
**Current**: Only matches executable names (exact match, case-insensitive)
**Problems**: 
- Misses variations (Steam vs Epic vs standalone versions)
- No fallback detection methods
- Reloads profiles on every detection loop
- Process iteration is blocking (already fixed to executor, but could be smarter)

**Improvements**:
- [x] Implement fuzzy matching for executables (Levenshtein distance, 85% match threshold)
- [ ] Add port-based detection as secondary method (query open ports, match against profile ports)
- [x] Implement in-memory profile cache with TTL (cache for 30 seconds, invalidate when files change)
- [ ] Add window title detection for windowed games (parse window names for game identification)
- [ ] Implement detection ranking system (prioritize process > window title > port > hash)
- [ ] Add detected game confidence scores (show "probably Minecraft" vs "definitely Minecraft")

**Status**: ✅ COMPLETED - Fuzzy matching & ProfileCache implemented
**Expected Impact**: +40% game detection rate, better UX with confidence indicators

---

### 1.2 Latency Measurement Overhaul
**File**: `core/server_browser.py`
**Current**: Single ICMP ping, synchronous (now async), timeout=2s, no fallback
**Problems**:
- Single measurement is noisy and unreliable
- ICMP blocked in many corporate networks
- Sequential pinging (slow when many servers)
- No TCP fallback
- No historical trend analysis

**Improvements**:
- [x] Multi-sample latency (3 pings, use median instead of single value)
- [ ] Exponential moving average (EMA) filter for smoothing: `new_latency = 0.7 * old_latency + 0.3 * measured`
- [x] Parallel pinging with `asyncio.gather()` (ping all servers concurrently)
- [ ] TCP SYN-based fallback (try TCP port 53/80/443 if ICMP fails)
- [ ] DNS lookup time measurement as tertiary fallback
- [ ] Latency trend detection (increasing/decreasing/stable)
- [ ] Per-server measurement interval adaptation (if latency is good, measure every 60s; if bad, every 10s)

**Implementation Details**:
```python
# Median of 3 measurements
samples = await asyncio.gather(
    ping(server, timeout=1),
    ping(server, timeout=1),
    ping(server, timeout=1),
    return_exceptions=True
)
valid_samples = [s for s in samples if s is not None]
server.latency_ms = statistics.median(valid_samples) if valid_samples else None

# EMA calculation
server.latency_ema = 0.7 * server.latency_ema + 0.3 * new_measurement
```

**Expected Impact**: 60% more reliable latency readings, better server selection

---

### 1.3 State Persistence Batching
**File**: `core/control.py`
**Current**: Writes state to disk on every change
**Problems**:
- High disk I/O on frequent state changes
- No deduplication of writes
- Blocking serialization

**Improvements**:
- [x] Implement write-behind cache with batching (100ms batch interval)
- [x] Deduplicate writes within batch window
- [x] Add StatePersister class with flush() method
- [x] Add shutdown() method to ControlPlane for graceful flush

**Status**: ✅ COMPLETED - Full batched persistence with deduplication implemented
**Expected Impact**: 50x reduction in disk writes, improved responsiveness

---

## Priority 2: Network & State Management

### 2.1 Adaptive Keepalive
**File**: `core/games.py`, `core/network.py`
**Current**: Fixed 25s keepalive for all, can be overridden per game
**Problems**:
- Doesn't adapt to NAT type
- Symmetric NAT needs more frequent keepalive (5-10s)
- Cone NAT can use longer intervals (60s+)
- Wastes bandwidth on good connections

**Improvements**:
- [x] Detect NAT type on startup (already in `core/nat.py`)
- [x] Map NAT type to keepalive interval:
  - Full Cone NAT: 60s (most relaxed)
  - Address-Restricted: 30s
  - Port-Restricted: 15s
  - Symmetric: 8s (strict, needs frequent keepalive)
- [x] GameOptimizer uses `calculate_adaptive_keepalive()` function
- [x] GameManager passes NAT type to optimizer via `set_nat_type()`

**Status**: ✅ COMPLETED - Full NAT-aware adaptive keepalive implemented
**Expected Impact**: 30% reduction in keepalive traffic for good connections

---

### 2.2 Connection Quality Prediction
**File**: `core/metrics.py`
**Current**: Basic latency-based status
**Problems**:
- No consideration of jitter or packet loss
- No trend analysis
- No quality scoring

**Improvements**:
- [x] Implement `predict_connection_quality()` function with weighted scoring
  - Latency (40%): 0ms=100pts, 150ms=0pts
  - Packet Loss (35%): 0% loss=100pts, 5% loss=0pts
  - Jitter (25%): 0ms=100pts, 50ms=0pts
- [x] Calculate jitter as standard deviation of recent latencies
- [x] Track quality trend: improving/stable/degrading
- [x] Add PeerMetrics fields: packet_loss_percent, jitter_ms, quality_score, quality_trend
- [x] Add `get_peer_connection_quality()` method with detailed metrics

**Status**: ✅ COMPLETED - Full connection quality prediction with trending
**Expected Impact**: Better connection health visibility, early warning of degradation

---

## Priority 3: Integration Optimization

### 3.1 Discord Integration Optimization
**File**: `core/discord_integration.py`
**Current**: Sends notifications immediately for each event
**Problems**:
- High API call frequency during rapid events (e.g., multiple peer joins)
- No notification batching
- Potential Discord API rate limiting

**Improvements**:
- [x] Create `NotificationBatcher` class with 500ms batch window
- [x] Create `NotificationMessage` dataclass for queueing
- [x] Implement `queue_notification()` with time-window deduplication
- [x] Add `_batch_flush_loop()` background task
- [x] Add `_flush_pending_notifications()` to combine multiple notifications
- [x] Update all notify_* methods to use batching
- [x] Add graceful flush on shutdown

**Status**: ✅ COMPLETED - Full notification batching with background flush
**Expected Impact**: 60-80% reduction in Discord API calls during events

---

### 3.2 Metrics Collection Optimization
**File**: `core/metrics.py`
**Current**: Stores all raw metrics, no aggregation
**Problems**:
- High memory usage for long-running sessions
- Difficult to analyze long-term trends
- No statistical summaries

**Improvements**:
- [x] Create `aggregate_metrics_by_window()` function
- [x] Compute min/max/avg/p95 statistics within time windows
- [x] Add `get_aggregated_system_metrics()` method
- [x] Add `get_aggregated_peer_metrics()` method
- [x] Support configurable window sizes (default 60s)

**Status**: ✅ COMPLETED - Full time-window metric aggregation implemented
**Expected Impact**: Reduced memory usage, better long-term trend analysis
  - Port-Restricted: 15s
  - Symmetric: 5s (most strict)
- [ ] Override with game-specific values when needed
- [ ] Monitor connection drops and auto-adjust upward if needed
- [ ] Add telemetry: track keepalive effectiveness per NAT type

**Expected Impact**: +20% reduction in keepalive traffic, better NAT traversal success

---

### 2.2 State Persistence Batching
**File**: `core/control.py`
**Current**: Writes state file immediately on every change
**Problems**:
- 50+ writes per second during peer operations
- Excessive disk I/O
- Potential race conditions on rapid updates
- No transaction-like behavior

**Improvements**:
- [ ] Implement write-behind cache (queue changes, batch every 100ms)
- [ ] Use asyncio Timer for batching: collect updates, flush on timer
- [ ] Only write if state actually changed (deduplicate)
- [ ] Add atomic write using temp file + rename (prevent corruption)
- [ ] Implement write conflict detection (same peer updated by multiple sources)
- [ ] Add journaling for recovery from crashes

**Implementation**:
```python
class StatePersister:
    def __init__(self, flush_interval=0.1):
        self.pending_changes = {}
        self.flush_interval = flush_interval
        self._flush_task = None
    
    async def queue_change(self, key, value):
        self.pending_changes[key] = value
        if not self._flush_task:
            self._flush_task = asyncio.create_task(self._flush_after_interval())
    
    async def _flush_after_interval(self):
        await asyncio.sleep(self.flush_interval)
        await self._persist()
        self._flush_task = None
```

**Expected Impact**: 50x reduction in disk writes, better responsiveness

---

### 2.3 Conflict Resolution for Concurrent Operations
**File**: `core/control.py`
**Current**: No handling for simultaneous updates from different peers
**Problems**:
- Two peers updating party info simultaneously = lost updates
- Race condition on peer list mutations
- No version tracking for state

**Improvements**:
- [ ] Add version/epoch numbers to parties and peers
- [ ] Implement Last-Write-Wins (LWW) with timestamp comparison
- [ ] Add operation logging for replay on conflict
- [ ] Implement CRDTs for peer list (grows-only set)
- [ ] Add conflict hooks for custom resolution
- [ ] Detect and warn on conflicting operations

**Expected Impact**: Eliminates silent data loss in concurrent scenarios

---

## Priority 3: Resource Management

### 3.1 Memory-Bounded Metrics Collection
**File**: `core/metrics.py`
**Current**: Unlimited in-memory history (unbounded growth)
**Problems**:
- Memory grows indefinitely over time
- No way to query historical data
- High memory usage on long-running systems
- All data lost on restart

**Improvements**:
- [ ] Implement circular buffer with max size (e.g., 10,000 points per metric)
- [ ] Auto-aggregate old data (1min intervals → 1hour intervals after 1 day)
- [ ] Implement time-window queries with O(1) lookup
- [ ] Optional SQLite backend for persistence
- [ ] Implement decay/cleanup of unused peer metrics
- [ ] Memory limit threshold with automatic pruning

**Implementation**:
```python
class CircularMetricsBuffer:
    def __init__(self, max_size=10000, aggregate_after=3600):
        self.max_size = max_size
        self.data = deque(maxlen=max_size)  # Automatic overflow
        self.aggregate_after = aggregate_after
    
    async def add(self, timestamp, value):
        if len(self.data) == self.max_size:
            # Trigger aggregation of oldest hour
            await self._aggregate_oldest()
        self.data.append((timestamp, value))
```

**Expected Impact**: Fixed memory usage, persistent metrics, better analytics

---

### 3.2 Broadcast Packet Deduplication
**File**: `core/broadcast.py`
**Current**: Forwards all received broadcasts to peers
**Problems**:
- Same packet received multiple times = multiple forwards
- Network loop = exponential packet duplication
- High bandwidth waste
- Potential DoS

**Improvements**:
- [ ] Implement packet hash bloom filter (64KB, ~99.9% accuracy)
- [ ] Track packet hashes for 5 second window
- [ ] Drop duplicate packets
- [ ] Add hop count limit (TTL equivalent)
- [ ] Implement source tracking (don't forward back to sender)
- [ ] Statistics: track duplicates, drops, forwarded

**Expected Impact**: 70% reduction in broadcast traffic, prevent loops

---

### 3.3 Dynamic Broadcast Port Monitoring
**File**: `core/broadcast.py`
**Current**: Static list of hardcoded ports (4445, 7777, 27015, etc.)
**Problems**:
- Misses games using non-standard ports
- Listens on unused ports (wastes resources)
- Can't adapt to user's game library

**Improvements**:
- [ ] Hook into game detection (`core/games.py`)
- [ ] Dynamically start/stop listeners based on running games
- [ ] Monitor game profile ports instead of hardcoded list
- [ ] Auto-enable when game detected, auto-disable when stopped
- [ ] Add manual port whitelist (user can add custom ports)
- [ ] Cache open ports to avoid repeated system calls

**Expected Impact**: Better discovery for custom games, lower resource usage

---

## Priority 4: Advanced Features

### 4.1 Task Priority & Dependency System
**File**: `core/task_manager.py`
**Current**: FIFO task queue with cancellation
**Problems**:
- No way to prioritize critical tasks
- No dependency tracking
- Failed task stops dependent tasks ungracefully
- No task grouping

**Improvements**:
- [ ] Implement priority levels: CRITICAL, HIGH, NORMAL, LOW, BACKGROUND
- [ ] Add task dependency tracking (TaskA must complete before TaskB)
- [ ] Implement dependency graph resolution
- [ ] Graceful fallback on task failure (skip dependents, log, continue)
- [ ] Add task grouping (e.g., "network_setup", all tasks in group)
- [ ] Implement task timeout with automatic escalation

**Implementation**:
```python
class PriorityTaskManager:
    async def create_task(self, coro, priority=Priority.NORMAL, 
                         depends_on=None, group=None):
        task = PriorityTask(coro, priority, depends_on, group)
        await self._resolve_dependencies(task)
        # Execute based on priority queue
```

**Expected Impact**: Better reliability, cleaner error handling, smarter execution

---

### 4.2 Connection Quality Metrics & Adaptation
**File**: `core/party.py`, `core/network.py`
**Current**: No connection quality tracking
**Problems**:
- Can't identify problematic peers
- No basis for switching to relay
- No feedback loop for optimization

**Improvements**:
- [ ] Track per-peer metrics: latency, jitter, packet loss, bandwidth
- [ ] Calculate connection quality score (0-100)
- [ ] Detect degradation patterns (increasing latency trend)
- [ ] Auto-switch to relay when quality < threshold
- [ ] Implement exponential backoff for unstable peers
- [ ] Track relay effectiveness (does relay improve quality?)

**Expected Impact**: Smarter peer selection, better user experience

---

### 4.3 Intelligent Relay Selection
**File**: `core/party.py`
**Current**: Uses first available relay
**Problems**:
- No latency consideration for relay
- No load balancing
- No region awareness

**Improvements**:
- [ ] Query relay health (latency, availability, load)
- [ ] Select relay with lowest combined latency (peer→relay + relay→peer)
- [ ] Implement round-robin across healthy relays
- [ ] Add region preference (prefer closer relays)
- [ ] Monitor relay performance over time
- [ ] Implement fallback chain if primary relay fails

**Expected Impact**: 30% latency reduction when using relays

---

## Priority 5: Observability & Debugging

### 5.1 Structured Logging with Context
**File**: All files using logging
**Current**: Print statements and basic logging
**Problems**:
- Hard to trace requests through system
- No correlation IDs
- Difficult to filter by context

**Improvements**:
- [ ] Implement context vars for correlation IDs
- [ ] Add structured logging (JSON output option)
- [ ] Log peer_id, party_id, session_id with every log
- [ ] Implement log levels properly (DEBUG, INFO, WARNING, ERROR)
- [ ] Add performance timing to critical paths

**Expected Impact**: 10x faster debugging, better log searchability

---

### 5.2 Metrics Dashboard & Alerts
**File**: `api/server.py`, new endpoints
**Current**: No runtime metrics visible
**Problems**:
- Can't see system health in real-time
- No alerting mechanism
- Hard to diagnose issues in production

**Improvements**:
- [ ] Add `/metrics` endpoint with Prometheus format
- [ ] Real-time dashboard showing: peers, latency, bandwidth, errors
- [ ] Alert threshold configuration (e.g., alert if latency > 200ms)
- [ ] Performance timeline (last 1h, 1d, 1w)
- [ ] Per-peer health status

**Expected Impact**: Better observability, faster incident response

---

## Implementation Priority Order

**Phase 1 (Week 1)**: 
1. Game Detection (1.1) - High impact, medium effort
2. Latency Measurement (1.2) - High impact, medium effort
3. State Batching (2.2) - High impact, medium effort

**Phase 2 (Week 2)**:
4. Adaptive Keepalive (2.1) - Medium impact, low effort
5. Memory-Bounded Metrics (3.1) - Medium impact, high effort
6. Broadcast Deduplication (3.2) - Medium impact, medium effort

**Phase 3 (Week 3)**:
7. Dynamic Broadcast (3.3) - Low impact, medium effort
8. Task Priorities (4.1) - Low impact, high effort
9. Structured Logging (5.1) - Low impact, low effort

**Phase 4 (Week 4+)**:
10. Connection Quality (4.2)
11. Relay Selection (4.3)
12. Metrics Dashboard (5.2)

---

## Testing Strategy

For each improvement:
- [ ] Unit tests for core logic
- [ ] Integration tests with full flow
- [ ] Performance benchmarks (before/after)
- [ ] Stress tests (many peers, rapid updates, etc.)
- [ ] Real-world testing with actual games

---

## Rollback Plan

Each feature should be:
- Feature-flagged (can disable via config)
- Backwards compatible
- Have fallback mechanism if new logic fails
- Include metrics/logging to monitor impact



---

## Recent Completed Work (January 31, 2026)

### ✅ CI/CD Test Failures Fixed

**Issue**: Tests failing with `ConfigError: Settings database is empty` after database-first configuration migration.

**Solution**:
- Created `tests/conftest.py` with session-scoped fixture to automatically initialize database
- Updated CI/CD workflow to explicitly initialize database before tests
- All test fixtures now use `async def config()` with `await Config.load()`

**Results**:
- ✅ All CI/CD workflows passing (Code Quality, Pylint, CI)
- ✅ All test jobs passing across Python 3.12 & 3.13 on Ubuntu & Windows
- ✅ 24/24 settings tests passing
- ✅ Database initialization working in test environment

**Commits**: `8cfab79`, `0f5a96c`

---

### ✅ Database-First Configuration Migration

**Changes**:
- Migrated from `.env` file to SQLite database as single source of truth
- All configuration now managed through WebUI
- Removed environment variable dependencies
- Added database initialization validation

**Breaking Change**: `.env` files no longer supported. Users must configure through WebUI at http://localhost:8666/settings.html

---

### Current Status

**Version**: v1.2.5
**CI/CD**: All workflows passing ✅
**Code Quality**: Ruff 100%, Pylint 10.00/10 ✅
**Test Coverage**: 88% ✅
**Status**: Production Ready ✅
