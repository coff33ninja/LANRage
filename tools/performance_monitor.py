"""
Performance monitoring tool for LANrage.

Real-time performance monitoring and analysis.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psutil

from core.profiler import get_profiler


class PerformanceMonitor:
    """Real-time performance monitor."""

    def __init__(self, interval: float = 1.0):
        """Initialize monitor."""
        self.interval = interval
        self.process = psutil.Process()
        self.running = False
        self.history = {
            "cpu": [],
            "memory": [],
            "threads": [],
            "timestamp": [],
        }

    async def start(self):
        """Start monitoring."""
        self.running = True
        print("🔍 Performance Monitor Started")
        print("Press Ctrl+C to stop and view report\n")

        try:
            while self.running:
                await self._collect_metrics()
                await asyncio.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop monitoring."""
        self.running = False
        self._print_report()

    async def _collect_metrics(self):
        """Collect current metrics."""
        cpu = self.process.cpu_percent(interval=0.1)
        memory = self.process.memory_info().rss / 1024 / 1024  # MB
        threads = self.process.num_threads()
        timestamp = time.time()

        self.history["cpu"].append(cpu)
        self.history["memory"].append(memory)
        self.history["threads"].append(threads)
        self.history["timestamp"].append(timestamp)

        # Print current stats
        print(
            f"\r⏱️  CPU: {cpu:5.1f}% | Memory: {memory:6.1f} MB | Threads: {threads:3d}",
            end="",
        )

    def _print_report(self):
        """Print monitoring report."""
        print("\n\n" + "=" * 80)
        print("Performance Monitoring Report")
        print("=" * 80)

        if not self.history["cpu"]:
            print("No data collected")
            return

        # Calculate statistics
        cpu_avg = sum(self.history["cpu"]) / len(self.history["cpu"])
        cpu_max = max(self.history["cpu"])
        cpu_min = min(self.history["cpu"])

        mem_avg = sum(self.history["memory"]) / len(self.history["memory"])
        mem_max = max(self.history["memory"])
        mem_min = min(self.history["memory"])

        thread_avg = sum(self.history["threads"]) / len(self.history["threads"])
        thread_max = max(self.history["threads"])

        duration = self.history["timestamp"][-1] - self.history["timestamp"][0]

        print(f"\n📊 Monitoring Duration: {duration:.1f}s")
        print(f"   Samples: {len(self.history['cpu'])}")

        print("\n💻 CPU Usage:")
        print(f"   Average: {cpu_avg:.1f}%")
        print(f"   Min: {cpu_min:.1f}%")
        print(f"   Max: {cpu_max:.1f}%")

        print("\n💾 Memory Usage:")
        print(f"   Average: {mem_avg:.1f} MB")
        print(f"   Min: {mem_min:.1f} MB")
        print(f"   Max: {mem_max:.1f} MB")
        print(f"   Growth: {mem_max - mem_min:.1f} MB")

        print("\n🧵 Threads:")
        print(f"   Average: {thread_avg:.1f}")
        print(f"   Max: {thread_max}")

        # Detect issues
        issues = []
        if cpu_avg > 50:
            issues.append(f"High average CPU usage: {cpu_avg:.1f}%")
        if cpu_max > 80:
            issues.append(f"CPU spikes detected: {cpu_max:.1f}%")
        if mem_max - mem_min > 100:
            issues.append(f"Significant memory growth: {mem_max - mem_min:.1f} MB")
        if mem_avg > 500:
            issues.append(f"High memory usage: {mem_avg:.1f} MB")

        if issues:
            print("\n⚠️  Issues Detected:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✅ No performance issues detected")

        print("\n" + "=" * 80)


class PerformanceBenchmark:
    """Run performance benchmarks."""

    @staticmethod
    async def benchmark_startup():
        """Benchmark startup time."""
        print("\n🚀 Benchmarking Startup Time...")

        start = time.perf_counter()

        # Import core modules
        from core.config import Config
        from core.ipam import IPAddressPool
        from core.metrics import MetricsCollector

        # Initialize components
        config = Config()
        _ = IPAddressPool()
        _ = MetricsCollector(config)

        end = time.perf_counter()
        startup_time = end - start

        print(f"   Startup time: {startup_time*1000:.2f}ms")

        if startup_time < 0.1:
            print("   ✅ Excellent startup time")
        elif startup_time < 0.5:
            print("   ✅ Good startup time")
        else:
            print("   ⚠️  Slow startup time")

        return startup_time

    @staticmethod
    async def benchmark_operations():
        """Benchmark common operations."""
        print("\n⚡ Benchmarking Common Operations...")

        from core.config import Config
        from core.ipam import IPAddressPool
        from core.metrics import MetricsCollector

        ipam = IPAddressPool()
        config = Config()
        collector = MetricsCollector(config)

        # Benchmark IP allocation
        iterations = 1000
        start = time.perf_counter()
        for i in range(iterations):
            ipam.allocate(f"peer_{i}")
        end = time.perf_counter()
        ip_alloc_time = (end - start) / iterations

        print(f"   IP allocation: {ip_alloc_time*1000000:.2f}µs per operation")

        # Benchmark metrics collection
        start = time.perf_counter()
        for _ in range(iterations):
            await collector.record_latency("test", 10.5)
        end = time.perf_counter()
        metrics_time = (end - start) / iterations

        print(f"   Metrics collection: {metrics_time*1000:.2f}ms per operation")

        # Overall assessment
        if ip_alloc_time < 0.0001 and metrics_time < 0.005:
            print("   ✅ Excellent operation performance")
        elif ip_alloc_time < 0.001 and metrics_time < 0.01:
            print("   ✅ Good operation performance")
        else:
            print("   ⚠️  Operations could be faster")

    @staticmethod
    async def benchmark_scaling():
        """Benchmark scaling with peer count."""
        print("\n📈 Benchmarking Scaling Performance...")

        from core.ipam import IPAddressPool

        peer_counts = [10, 50, 100, 500]

        for count in peer_counts:
            ipam = IPAddressPool()

            # Allocate peers
            for i in range(count):
                ipam.allocate(f"peer_{i}")

            # Measure lookup time
            test_peer = "peer_5"
            iterations = 1000
            start = time.perf_counter()
            for _ in range(iterations):
                _ = ipam.get_ip(test_peer)
            end = time.perf_counter()

            lookup_time = (end - start) / iterations
            print(f"   {count:4d} peers: {lookup_time*1000000:.2f}µs lookup time")

        print("   ✅ Scaling benchmark complete")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LANrage Performance Monitor")
    parser.add_argument(
        "command", choices=["monitor", "benchmark", "profile"], help="Command to run"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Monitoring interval in seconds (default: 1.0)",
    )

    args = parser.parse_args()

    if args.command == "monitor":
        monitor = PerformanceMonitor(interval=args.interval)
        await monitor.start()

    elif args.command == "benchmark":
        print("=" * 80)
        print("LANrage Performance Benchmarks")
        print("=" * 80)

        await PerformanceBenchmark.benchmark_startup()
        await PerformanceBenchmark.benchmark_operations()
        await PerformanceBenchmark.benchmark_scaling()

        print("\n" + "=" * 80)
        print("✅ All benchmarks complete")
        print("=" * 80)

    elif args.command == "profile":
        profiler = get_profiler()
        profiler.enable()

        print("=" * 80)
        print("LANrage Performance Profiler")
        print("=" * 80)
        print(
            "\nProfiler enabled. Run LANrage operations, then press Ctrl+C to view report.\n"
        )

        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            profiler.print_report()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")
