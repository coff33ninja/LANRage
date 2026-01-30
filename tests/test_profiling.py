"""
Performance profiling tests for LANrage.

Identifies bottlenecks and measures performance of critical operations.
"""

import asyncio
import time

import pytest

# Import core modules for profiling
from core.config import Config
from core.ipam import IPAddressPool
from core.metrics import MetricsCollector
from core.utils import calculate_latency, format_bandwidth, parse_port_range


class TestPerformanceProfiling:
    """Performance profiling test suite."""

    def test_config_load_performance(self, tmp_path):
        """Profile configuration loading time."""
        config_dir = tmp_path / ".lanrage"
        config_dir.mkdir()

        iterations = 100
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            _ = Config(config_dir=str(config_dir))
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print("\n📊 Config Load Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Min: {min_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")

        # Config load should be fast (<10ms average)
        assert avg_time < 0.01, f"Config load too slow: {avg_time*1000:.2f}ms"

    def test_ipam_allocation_performance(self):
        """Profile IP address allocation performance."""
        ipam = IPAddressPool()

        iterations = 1000
        times = []

        for i in range(iterations):
            start = time.perf_counter()
            _ = ipam.allocate(f"peer_{i}")
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print("\n📊 IPAM Allocation Performance:")
        print(f"  Average: {avg_time*1000000:.2f}µs")
        print(f"  Max: {max_time*1000000:.2f}µs")
        print(f"  Total IPs allocated: {iterations}")

        # IP allocation should be very fast (<400µs average, allowing for Python overhead and CI variability)
        assert avg_time < 0.0004, f"IP allocation too slow: {avg_time*1000000:.2f}µs"

    def test_ipam_lookup_performance(self):
        """Profile IP address lookup performance."""
        ipam = IPAddressPool()

        # Pre-allocate some IPs
        test_peers = []
        for i in range(100):
            peer_id = f"peer_{i}"
            ipam.allocate(peer_id)
            test_peers.append(peer_id)

        iterations = 10000
        times = []

        for i in range(iterations):
            test_peer = test_peers[i % len(test_peers)]
            start = time.perf_counter()
            _ = ipam.get_ip(test_peer)
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print("\n📊 IPAM Lookup Performance:")
        print(f"  Average: {avg_time*1000000:.2f}µs")
        print(f"  Max: {max_time*1000000:.2f}µs")
        print(f"  Lookups per second: {1/avg_time:.0f}")

        # Lookup should be very fast (<10µs average)
        assert avg_time < 0.00001, f"IP lookup too slow: {avg_time*1000000:.2f}µs"

    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self):
        """Profile metrics collection performance."""
        config = Config()
        collector = MetricsCollector(config)

        iterations = 1000
        times = []

        for i in range(iterations):
            start = time.perf_counter()
            await collector.record_latency("test_peer", 10.5)
            await collector.record_bandwidth("test_peer", 1024 * 1024)  # 1MB
            await collector.record_packet_loss("test_peer", 0.01)
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print("\n📊 Metrics Collection Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")
        print(f"  Collections per second: {1/avg_time:.0f}")

        # Metrics collection should be fast (<5ms average)
        assert avg_time < 0.005, f"Metrics collection too slow: {avg_time*1000:.2f}ms"

    def test_utility_functions_performance(self):
        """Profile utility function performance."""
        iterations = 10000

        # Test calculate_latency
        latency_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            _ = calculate_latency(100.0, 150.0)
            end = time.perf_counter()
            latency_times.append(end - start)

        # Test format_bandwidth
        bandwidth_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            _ = format_bandwidth(1024 * 1024 * 10)
            end = time.perf_counter()
            bandwidth_times.append(end - start)

        # Test parse_port_range
        port_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            _ = parse_port_range("7777-7780")
            end = time.perf_counter()
            port_times.append(end - start)

        latency_avg = sum(latency_times) / len(latency_times)
        bandwidth_avg = sum(bandwidth_times) / len(bandwidth_times)
        port_avg = sum(port_times) / len(port_times)

        print("\n📊 Utility Functions Performance:")
        print(f"  calculate_latency: {latency_avg * 1000000:.2f}µs")
        print(f"  format_bandwidth: {bandwidth_avg * 1000000:.2f}µs")
        print(f"  parse_port_range: {port_avg * 1000000:.2f}µs")

        # All utility functions should be very fast (<10µs)
        assert latency_avg < 0.00001
        assert bandwidth_avg < 0.00001
        assert port_avg < 0.00001

    def test_game_profile_loading_performance(self):
        """Profile game profile loading performance."""
        import json
        from pathlib import Path as ProfilePath

        profiles_dir = ProfilePath("game_profiles")

        # Test loading all profiles
        start = time.perf_counter()
        all_profiles = {}
        for json_file in profiles_dir.rglob("*.json"):
            with open(json_file, encoding="utf-8") as f:
                profile = json.load(f)
                all_profiles[json_file.stem] = profile
        end = time.perf_counter()

        total_time = end - start
        profile_count = len(all_profiles)
        avg_time = total_time / profile_count if profile_count > 0 else 0

        print("\n📊 Game Profile Loading Performance:")
        print(f"  Total profiles: {profile_count}")
        print(f"  Total time: {total_time*1000:.2f}ms")
        print(f"  Average per profile: {avg_time*1000:.2f}ms")

        # Loading all profiles should be fast (<100ms total)
        assert total_time < 0.1, f"Profile loading too slow: {total_time*1000:.2f}ms"

    def test_memory_usage_baseline(self):
        """Measure baseline memory usage of core components."""
        import sys

        # Measure Config memory
        _ = Config()
        config_size = sys.getsizeof(Config())

        # Measure IPAM memory
        ipam = IPAddressPool()
        ipam_size = sys.getsizeof(ipam)

        # Allocate 100 IPs and measure
        for i in range(100):
            ipam.allocate(f"peer_{i}")
        ipam_with_peers_size = sys.getsizeof(ipam)

        print("\n📊 Memory Usage Baseline:")
        print(f"  Config object: {config_size} bytes")
        print(f"  IPAM (empty): {ipam_size} bytes")
        print(f"  IPAM (100 peers): {ipam_with_peers_size} bytes")
        print(
            f"  Memory per peer: {(ipam_with_peers_size - ipam_size) / 100:.0f} bytes"
        )

        # Memory usage should be reasonable
        assert config_size < 10000, "Config using too much memory"
        assert ipam_size < 10000, "IPAM using too much memory"

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self):
        """Profile performance under concurrent load."""
        ipam = IPAddressPool()
        config = Config()
        collector = MetricsCollector(config)

        async def simulate_peer_operations():
            """Simulate typical peer operations."""
            peer_id = f"peer_{id(asyncio.current_task())}"
            ip = ipam.allocate(peer_id)
            await collector.record_latency(str(ip), 10.5)
            await collector.record_bandwidth(str(ip), 1024 * 1024)
            return ip

        # Run 100 concurrent operations
        iterations = 100
        start = time.perf_counter()
        tasks = [simulate_peer_operations() for _ in range(iterations)]
        _ = await asyncio.gather(*tasks)
        end = time.perf_counter()

        total_time = end - start
        avg_time = total_time / iterations
        ops_per_sec = iterations / total_time

        print("\n📊 Concurrent Operations Performance:")
        print(f"  Total operations: {iterations}")
        print(f"  Total time: {total_time*1000:.2f}ms")
        print(f"  Average per operation: {avg_time*1000:.2f}ms")
        print(f"  Operations per second: {ops_per_sec:.0f}")

        # Should handle concurrent operations efficiently
        assert (
            total_time < 1.0
        ), f"Concurrent operations too slow: {total_time*1000:.2f}ms"
        assert ops_per_sec > 50, f"Throughput too low: {ops_per_sec:.0f} ops/sec"


class TestBottleneckIdentification:
    """Identify specific bottlenecks in the codebase."""

    def test_identify_slow_imports(self):
        """Identify slow module imports."""
        import importlib
        import sys

        modules_to_test = [
            "core.config",
            "core.network",
            "core.party",
            "core.nat",
            "core.broadcast",
            "core.metrics",
            "core.ipam",
            "core.utils",
        ]

        import_times = {}

        for module_name in modules_to_test:
            # Remove from cache if present
            if module_name in sys.modules:
                del sys.modules[module_name]

            start = time.perf_counter()
            importlib.import_module(module_name)
            end = time.perf_counter()

            import_times[module_name] = end - start

        print("\n📊 Module Import Times:")
        for module, import_time in sorted(
            import_times.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {module}: {import_time*1000:.2f}ms")

        # Identify slow imports (>100ms)
        slow_imports = {m: t for m, t in import_times.items() if t > 0.1}
        if slow_imports:
            print("\n⚠️  Slow imports detected:")
            for module, import_time in slow_imports.items():
                print(f"  {module}: {import_time*1000:.2f}ms")

    def test_identify_hot_paths(self):
        """Identify frequently called code paths."""
        import cProfile
        import pstats
        from io import StringIO

        # Profile a typical workflow
        profiler = cProfile.Profile()
        profiler.enable()

        # Simulate typical operations
        _ = Config()
        ipam = IPAddressPool()

        for i in range(100):
            ipam.allocate(f"peer_{i}")
            _ = ipam.get_ip(f"peer_{i}")

        profiler.disable()

        # Analyze results
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)  # Top 20 functions

        print("\n📊 Hot Paths (Top 20 by cumulative time):")
        print(stream.getvalue())

    @pytest.mark.asyncio
    async def test_identify_async_bottlenecks(self):
        """Identify bottlenecks in async operations."""
        config = Config()
        collector = MetricsCollector(config)

        # First, add test peer to metrics
        collector.add_peer("test", "Test Peer")

        # Profile async operations
        async_operations = {
            "record_latency": lambda: collector.record_latency("test", 10.5),
            "record_bandwidth": lambda: collector.record_bandwidth("test", 1024 * 1024),
            "record_packet_loss": lambda: collector.record_packet_loss("test", 0.01),
            "get_peer_summary": lambda: collector.get_peer_summary("test"),
        }

        # Profile sync operations separately
        sync_operations = {}

        results = {}

        # Test async operations
        for op_name, op_func in async_operations.items():
            times = []
            for _ in range(100):
                start = time.perf_counter()
                await op_func()
                end = time.perf_counter()
                times.append(end - start)

            results[op_name] = {
                "avg": sum(times) / len(times),
                "max": max(times),
                "min": min(times),
            }

        # Test sync operations
        for op_name, op_func in sync_operations.items():
            times = []
            for _ in range(100):
                start = time.perf_counter()
                _ = op_func()
                end = time.perf_counter()
                times.append(end - start)

            results[op_name] = {
                "avg": sum(times) / len(times),
                "max": max(times),
                "min": min(times),
            }

        print("\n📊 Async Operation Performance:")
        for op_name, stats in sorted(
            results.items(), key=lambda x: x[1]["avg"], reverse=True
        ):
            print(f"  {op_name}:")
            print(f"    Average: {stats['avg']*1000:.2f}ms")
            print(f"    Max: {stats['max']*1000:.2f}ms")
            print(f"    Min: {stats['min']*1000:.2f}ms")


class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_ipam_scaling(self):
        """Test IPAM performance with increasing peer count."""
        ipam = IPAddressPool()

        peer_counts = [10, 50, 100, 500, 1000]
        results = {}

        for count in peer_counts:
            # Allocate peers
            for i in range(count):
                ipam.allocate(f"peer_{i}")

            # Measure lookup performance
            times = []
            for _ in range(1000):
                test_peer = f"peer_{count % 100}"
                start = time.perf_counter()
                _ = ipam.get_ip(test_peer)
                end = time.perf_counter()
                times.append(end - start)

            results[count] = sum(times) / len(times)

            # Reset for next iteration
            ipam = IPAddressPool()

        print("\n📊 IPAM Scaling Performance:")
        for count, avg_time in results.items():
            print(f"  {count} peers: {avg_time*1000000:.2f}µs")

        # Performance should not degrade significantly with scale
        # Allow 2x slowdown from 10 to 1000 peers
        assert (
            results[1000] < results[10] * 2
        ), "IPAM performance degrades too much with scale"

    @pytest.mark.asyncio
    async def test_metrics_scaling(self):
        """Test metrics collection performance with increasing data."""
        config = Config()
        collector = MetricsCollector(config)

        data_points = [100, 500, 1000, 5000]
        results = {}

        for count in data_points:
            # Pre-populate with data
            for i in range(count):
                await collector.record_latency(f"peer_{i % 10}", 10.5)

            # Measure collection performance
            times = []
            for _ in range(100):
                start = time.perf_counter()
                await collector.record_latency("test_peer", 10.5)
                end = time.perf_counter()
                times.append(end - start)

            results[count] = sum(times) / len(times)

            # Reset for next iteration
            config = Config()
            collector = MetricsCollector(config)

        print("\n📊 Metrics Scaling Performance:")
        for count, avg_time in results.items():
            print(f"  {count} data points: {avg_time*1000:.2f}ms")

        # Performance should remain relatively stable
        assert (
            results[5000] < results[100] * 3
        ), "Metrics performance degrades too much with data"


def run_full_profile():
    """Run comprehensive performance profile."""
    print("\n" + "=" * 80)
    print("LANrage Performance Profile")
    print("=" * 80)

    pytest.main(
        [
            __file__,
            "-v",
            "-s",  # Show print statements
            "--tb=short",
        ]
    )


if __name__ == "__main__":
    run_full_profile()
