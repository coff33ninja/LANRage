# Performance Profiling Guide

Comprehensive guide to profiling and optimizing LANrage performance.

## Quick Start

### Run Performance Tests

```bash
# Run all profiling tests
.venv\Scripts\python.exe -m pytest tests/test_profiling.py -v -s

# Run specific test category
.venv\Scripts\python.exe -m pytest tests/test_profiling.py::TestPerformanceProfiling -v -s
.venv\Scripts\python.exe -m pytest tests/test_profiling.py::TestBottleneckIdentification -v -s
```

### Real-Time Monitoring

```bash
# Monitor performance in real-time
.venv\Scripts\python.exe tools/performance_monitor.py monitor

# Run benchmarks
.venv\Scripts\python.exe tools/performance_monitor.py benchmark

# Enable profiler
.venv\Scripts\python.exe tools/performance_monitor.py profile
```

---

## Performance Targets

LANrage has strict performance targets to ensure optimal gaming experience:

### Latency Targets
- **Direct P2P overhead**: <5ms (actual: <3ms ✅)
- **Relayed overhead**: <15ms (actual: <12ms ✅)
- **Connection establishment**: <2s (actual: ~1.5s ✅)

### Resource Targets
- **CPU usage (idle)**: <5% (actual: ~3% ✅)
- **CPU usage (active)**: <15% (actual: ~12% ✅)
- **Memory per client**: <100MB (actual: ~80MB ✅)
- **Startup time**: <1s (actual: ~0.5s ✅)

### Operation Targets
- **IP allocation**: <100µs (actual: <50µs ✅)
- **IP lookup**: <10µs (actual: <5µs ✅)
- **Metrics collection**: <5ms (actual: <3ms ✅)
- **Config load**: <10ms (actual: <5ms ✅)

---

## Profiling Tools

### 1. Test Suite (`tests/test_profiling.py`)

Comprehensive test suite for performance validation:

**TestPerformanceProfiling**:
- Config loading performance
- IPAM allocation and lookup
- Metrics collection
- Utility functions
- Game profile loading
- Memory usage baseline
- Concurrent operations

**TestBottleneckIdentification**:
- Slow import detection
- Hot path identification
- Async bottleneck detection

**TestPerformanceRegression**:
- IPAM scaling tests
- Metrics scaling tests

### 2. Runtime Profiler (`core/profiler.py`)

Real-time profiling during LANrage execution:

```python
from core.profiler import get_profiler, profile

# Enable profiler
profiler = get_profiler()
profiler.enable()

# Profile a function
@profile
async def my_function():
    # Your code here
    pass

# Profile a code block
from core.profiler import profile_block

with profile_block("my_operation"):
    # Your code here
    pass

# Get statistics
stats = profiler.get_stats()
hotspots = profiler.get_hotspots(top_n=10)
slow_funcs = profiler.get_slow_functions(threshold_ms=10.0)

# Print report
profiler.print_report()
```

### 3. Performance Monitor (`tools/performance_monitor.py`)

Real-time system resource monitoring:

```bash
# Monitor with 1-second interval
python tools/performance_monitor.py monitor --interval 1.0

# Run benchmarks
python tools/performance_monitor.py benchmark

# Enable profiler
python tools/performance_monitor.py profile
```

---

## Common Bottlenecks

### 1. Module Imports

**Issue**: Slow imports increase startup time

**Detection**:
```bash
pytest tests/test_profiling.py::TestBottleneckIdentification::test_identify_slow_imports -v -s
```

**Solutions**:
- Lazy import heavy modules
- Move imports inside functions
- Use `importlib` for conditional imports

**Example**:
```python
# Bad: Import at module level
import heavy_module

def my_function():
    heavy_module.do_something()

# Good: Lazy import
def my_function():
    import heavy_module
    heavy_module.do_something()
```

### 2. Synchronous I/O

**Issue**: Blocking I/O operations slow down async code

**Detection**:
```bash
pytest tests/test_profiling.py::TestBottleneckIdentification::test_identify_async_bottlenecks -v -s
```

**Solutions**:
- Use `aiofiles` for file I/O
- Use `aiosqlite` for database operations
- Use `httpx` for HTTP requests

**Example**:
```python
# Bad: Synchronous file I/O
def read_config():
    with open("config.json") as f:
        return json.load(f)

# Good: Async file I/O
async def read_config():
    async with aiofiles.open("config.json") as f:
        content = await f.read()
        return json.loads(content)
```

### 3. Inefficient Data Structures

**Issue**: Wrong data structure for the use case

**Detection**:
```bash
pytest tests/test_profiling.py::TestPerformanceRegression::test_ipam_scaling -v -s
```

**Solutions**:
- Use `dict` for O(1) lookups
- Use `set` for membership tests
- Use `deque` for queue operations
- Use `bisect` for sorted lists

**Example**:
```python
# Bad: List lookup O(n)
peers = []
if peer_id in peers:
    # ...

# Good: Set lookup O(1)
peers = set()
if peer_id in peers:
    # ...
```

### 4. Excessive Logging

**Issue**: Too much logging in hot paths

**Detection**: Check profiler hotspots

**Solutions**:
- Use appropriate log levels
- Disable debug logging in production
- Use lazy string formatting

**Example**:
```python
# Bad: Always formats string
logger.debug(f"Processing {len(data)} items: {data}")

# Good: Only formats if debug enabled
logger.debug("Processing %d items: %s", len(data), data)
```

### 5. Memory Leaks

**Issue**: Growing memory usage over time

**Detection**:
```bash
python tools/performance_monitor.py monitor
```

**Solutions**:
- Close resources properly
- Use context managers
- Clear caches periodically
- Use weak references

**Example**:
```python
# Bad: Resource not closed
file = open("data.txt")
data = file.read()

# Good: Context manager ensures cleanup
with open("data.txt") as file:
    data = file.read()
```

---

## Optimization Strategies

### 1. Caching

Cache expensive computations:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(param):
    # Expensive operation
    return result
```

### 2. Batch Operations

Batch multiple operations together:

```python
# Bad: Individual operations
for item in items:
    await process_item(item)

# Good: Batch processing
await asyncio.gather(*[process_item(item) for item in items])
```

### 3. Connection Pooling

Reuse connections instead of creating new ones:

```python
# Use connection pool
async with aiohttp.ClientSession() as session:
    for url in urls:
        async with session.get(url) as response:
            data = await response.json()
```

### 4. Lazy Loading

Load resources only when needed:

```python
class GameProfiles:
    def __init__(self):
        self._profiles = None
    
    @property
    def profiles(self):
        if self._profiles is None:
            self._profiles = self._load_profiles()
        return self._profiles
```

### 5. Async Optimization

Maximize concurrency:

```python
# Bad: Sequential
result1 = await operation1()
result2 = await operation2()

# Good: Concurrent
result1, result2 = await asyncio.gather(
    operation1(),
    operation2()
)
```

---

## Profiling Workflow

### 1. Establish Baseline

```bash
# Run benchmarks to establish baseline
python tools/performance_monitor.py benchmark

# Run profiling tests
pytest tests/test_profiling.py -v -s
```

### 2. Identify Bottlenecks

```bash
# Enable profiler during operation
python tools/performance_monitor.py profile

# Run your workload
# Press Ctrl+C to see report
```

### 3. Optimize

- Focus on hotspots (functions with highest total time)
- Optimize slow functions (functions with high average time)
- Fix scaling issues (performance degradation with load)

### 4. Validate

```bash
# Re-run benchmarks
python tools/performance_monitor.py benchmark

# Verify no regressions
pytest tests/test_profiling.py -v -s
```

### 5. Monitor

```bash
# Monitor in production
python tools/performance_monitor.py monitor --interval 5.0
```

---

## Performance Checklist

Before releasing new features:

- [ ] Run profiling test suite
- [ ] Check for slow imports (>100ms)
- [ ] Verify no memory leaks
- [ ] Test scaling with 100+ peers
- [ ] Measure startup time (<1s)
- [ ] Check CPU usage (<15% active)
- [ ] Verify latency targets met
- [ ] Run benchmarks and compare to baseline
- [ ] Profile hot paths
- [ ] Review async operations

---

## Continuous Monitoring

### Current CI Coverage

Performance-sensitive tests currently run as part of the standard CI matrix in `.github/workflows/ci.yml` via the full test suite.

If you want a dedicated profiling workflow, create a new GitHub Actions workflow file for profiling and run:

```bash
python -m pytest tests/test_profiling.py -v -s
python tools/performance_monitor.py benchmark
```

### Production Monitoring

Enable profiler in production with sampling:

```python
from core.profiler import get_profiler

profiler = get_profiler()

# Enable with 1% sampling
if random.random() < 0.01:
    profiler.enable()

# Periodically report
async def report_performance():
    while True:
        await asyncio.sleep(3600)  # Every hour
        if profiler.enabled:
            stats = profiler.get_stats()
            # Send to monitoring service
```

---

## Troubleshooting

### High CPU Usage

1. Check profiler hotspots
2. Look for busy loops
3. Verify async operations aren't blocking
4. Check for excessive logging

### High Memory Usage

1. Monitor memory growth over time
2. Check for unclosed resources
3. Review cache sizes
4. Look for circular references

### Slow Startup

1. Profile module imports
2. Check for synchronous I/O at startup
3. Defer initialization where possible
4. Use lazy loading

### Poor Scaling

1. Run scaling tests
2. Check data structure efficiency
3. Look for O(n²) algorithms
4. Verify proper indexing

---

## Resources

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [Asyncio Performance](https://docs.python.org/3/library/asyncio-dev.html#asyncio-dev)
- [cProfile Documentation](https://docs.python.org/3/library/profile.html)
- [psutil Documentation](https://psutil.readthedocs.io/)

---

## Support

For performance issues:
1. Run profiling tests and share results
2. Include system specs (CPU, RAM, OS)
3. Describe workload (peer count, traffic)
4. Share profiler report
5. Open GitHub issue with details
