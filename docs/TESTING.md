# Testing LANrage

## Testing Philosophy

1. **Real games** - Not synthetic benchmarks
2. **Real networks** - Not localhost
3. **Real latency** - Measure everything
4. **Real users** - Dogfood it

## Test Environments

### Local Testing (Phase 0)

**Setup**:
- 2 computers on same LAN
- Direct P2P connection
- No relay needed

**Goal**: Verify basic functionality

---

### NAT Testing (Phase 1)

**Setup**:
- 2 computers on different networks
- Behind NAT
- Relay fallback

**Goal**: Verify NAT traversal

---

### Geographic Testing (Phase 2)

**Setup**:
- Computers in different regions
- High latency baseline
- Multiple relay nodes

**Goal**: Verify relay selection

---

### Scale Testing (Phase 3)

**Setup**:
- 10+ concurrent parties
- 50+ total peers
- Multiple relay nodes

**Goal**: Verify scalability

---

## Test Games

### Tier 1: Must Work

These games are critical for success:

1. **Minecraft** (Java Edition)
   - LAN discovery
   - UDP broadcast
   - Low latency required

2. **Terraria**
   - Direct IP connection
   - Moderate latency tolerance

3. **Stardew Valley**
   - LAN discovery
   - Low bandwidth

4. **Age of Empires II**
   - LAN discovery
   - Low latency required

5. **Counter-Strike 1.6**
   - LAN server browser
   - Very low latency required

---

### Tier 2: Should Work

Nice to have:

1. **Factorio**
2. **Don't Starve Together**
3. **Risk of Rain 2**
4. **Valheim**
5. **Left 4 Dead 2**

---

### Tier 3: Would Be Cool

Stretch goals:

1. **Warcraft III**
2. **StarCraft: Brood War**
3. **Diablo II**
4. **Quake III Arena**
5. **Unreal Tournament**

---

## Test Scenarios

### Scenario 1: Happy Path

**Setup**:
- 2 peers
- Same region
- Good internet
- No firewall issues

**Expected**:
- Direct P2P connection
- <5ms latency overhead
- Instant discovery

**Test**:
```bash
# Peer A
python lanrage.py
# Create party, note ID

# Peer B
python lanrage.py
# Join party with ID

# Both
# Launch Minecraft
# Check LAN games
# Verify connection
```

---

### Scenario 2: NAT Hell

**Setup**:
- 2 peers
- Strict NAT
- Relay required

**Expected**:
- Relayed connection
- <15ms latency overhead
- Automatic fallback

**Test**:
```bash
# Same as Scenario 1
# Verify connection type is "relayed"
# Measure latency
```

---

### Scenario 3: High Latency

**Setup**:
- 2 peers
- Different continents
- 100ms+ baseline latency

**Expected**:
- Connection works
- Minimal overhead
- Playable (depends on game)

**Test**:
```bash
# Same as Scenario 1
# Measure baseline latency (ping)
# Measure LANrage latency
# Calculate overhead
```

---

### Scenario 4: Party of 10

**Setup**:
- 10 peers
- Mixed networks
- Various latencies

**Expected**:
- All peers connect
- Mesh topology
- Stable connections

**Test**:
```bash
# Create party
# 9 peers join
# Verify all see each other
# Play game with all 10
```

---

### Scenario 5: Relay Failure

**Setup**:
- 2 peers
- Relay goes down mid-game

**Expected**:
- Automatic failover
- Minimal disruption
- Connection maintained

**Test**:
```bash
# Start game with relay
# Kill relay process
# Verify failover to another relay
# Game continues
```

---

## Metrics to Measure

### Latency

**Baseline**: Direct ping between peers
**LANrage**: Ping through LANrage
**Overhead**: LANrage - Baseline

**Target**:
- Direct P2P: <5ms overhead
- Relayed: <15ms overhead

**Measure**:
```bash
# Baseline
ping peer_ip

# LANrage
ping 10.66.0.2  # Peer's virtual IP
```

---

### Throughput

**Baseline**: iperf between peers
**LANrage**: iperf through LANrage

**Target**: >90% of baseline

**Measure**:
```bash
# Baseline
iperf3 -c peer_ip

# LANrage
iperf3 -c 10.66.0.2
```

---

### Connection Time

**Metric**: Time from "Join Party" to "Connected"

**Target**: <2 seconds

**Measure**: Stopwatch (for now)

---

### CPU Usage

**Metric**: CPU % while idle and active

**Target**:
- Idle: <5%
- Active: <15%

**Measure**:
```bash
# Windows
taskmgr

# Linux
top -p $(pgrep python)
```

---

### Memory Usage

**Metric**: RAM usage

**Target**: <100MB

**Measure**:
```bash
# Windows
taskmgr

# Linux
ps aux | grep python
```

---

## Automated Tests

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/

# Coverage
pytest --cov=core tests/unit/
```

---

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/

# Requires 2 machines or VMs
```

---

### Performance Tests

```bash
# Run performance tests
pytest tests/performance/

# Generates latency graphs
```

---

## Manual Test Checklist

### Pre-Release

- [ ] Create party
- [ ] Join party
- [ ] Leave party
- [ ] Measure latency
- [ ] Test with Minecraft
- [ ] Test with Terraria
- [ ] Test with 5+ peers
- [ ] Test NAT traversal
- [ ] Test relay fallback
- [ ] Test on Windows
- [ ] Test on Linux
- [ ] Check CPU usage
- [ ] Check memory usage
- [ ] Verify no crashes
- [ ] Verify no data loss

---

## Bug Reporting

### Template

```markdown
**Game**: Minecraft Java Edition
**LANrage Version**: 0.1.0
**OS**: Windows 11
**Network**: Behind NAT

**Expected**: Direct P2P connection
**Actual**: Relayed connection

**Steps to Reproduce**:
1. Create party
2. Friend joins
3. Check connection type

**Logs**: (attach logs)
```

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| Latency (direct) | <5ms | <10ms | >10ms |
| Latency (relayed) | <15ms | <30ms | >30ms |
| Throughput | >90% | >70% | <70% |
| Connection time | <2s | <5s | >5s |
| CPU (idle) | <5% | <10% | >10% |
| CPU (active) | <15% | <25% | >25% |
| Memory | <100MB | <200MB | >200MB |

---

## Stress Tests

### Test 1: Many Peers

- 50 peers in one party
- Measure connection time
- Measure latency
- Measure CPU/memory

### Test 2: Many Parties

- 100 concurrent parties
- 2 peers each
- Measure relay load

### Test 3: Long Duration

- 24 hour connection
- Monitor stability
- Check for memory leaks

### Test 4: Network Chaos

- Random packet loss
- Variable latency
- Relay failures
- Verify resilience

---

## Test Tools

### Latency Measurement

```python
# ping.py
import subprocess
import statistics

def measure_latency(ip, count=10):
    pings = []
    for _ in range(count):
        result = subprocess.run(
            ["ping", "-n", "1", ip],
            capture_output=True,
            text=True
        )
        # Parse ping time
        # ...
        pings.append(time)
    
    return {
        "min": min(pings),
        "max": max(pings),
        "avg": statistics.mean(pings),
        "stddev": statistics.stdev(pings)
    }
```

### Throughput Measurement

```bash
# Use iperf3
iperf3 -c 10.66.0.2 -t 30 -i 1
```

### Connection Monitor

```python
# monitor.py
import time
import requests

while True:
    status = requests.get("http://localhost:8666/status").json()
    print(f"Peers: {status['peer_count']}")
    for peer in status['party']['peers'].values():
        print(f"  {peer['name']}: {peer['latency_ms']}ms ({peer['connection_type']})")
    time.sleep(2)
```

---

## CI/CD Testing

### GitHub Actions

```yaml
name: Test LANrage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install uv
      - run: uv venv
      - run: uv pip install -r requirements.txt
      - run: pytest tests/
```

---

## User Acceptance Testing

### Beta Testers

- Recruit 10-20 gamers
- Various networks
- Various games
- Collect feedback

### Metrics

- Success rate
- Average latency
- User satisfaction
- Bug reports

### Feedback Form

```markdown
1. Did LANrage work for you? (Yes/No)
2. What game did you test?
3. What was your latency?
4. Any issues?
5. Would you use this again? (1-5)
6. Comments:
```

---

## Next Steps

1. Implement basic tests
2. Set up CI/CD
3. Recruit beta testers
4. Iterate based on feedback
5. Repeat until it works
