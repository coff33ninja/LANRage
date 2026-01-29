"""
Runtime performance profiler for LANrage.

Provides real-time performance monitoring and bottleneck detection.
"""

import asyncio
import functools
import time
from collections import defaultdict
from typing import Any, Callable

import psutil


class PerformanceProfiler:
    """Runtime performance profiler."""

    def __init__(self):
        """Initialize profiler."""
        self.function_stats = defaultdict(
            lambda: {
                "calls": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "errors": 0,
            }
        )
        self.enabled = False
        self.process = psutil.Process()

    def enable(self):
        """Enable profiling."""
        self.enabled = True

    def disable(self):
        """Disable profiling."""
        self.enabled = False

    def reset(self):
        """Reset all statistics."""
        self.function_stats.clear()

    def profile(self, func: Callable) -> Callable:
        """Decorator to profile a function."""

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)

            func_name = f"{func.__module__}.{func.__name__}"
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                self.function_stats[func_name]["errors"] += 1
                raise
            finally:
                elapsed = time.perf_counter() - start
                self._record_timing(func_name, elapsed)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not self.enabled:
                return await func(*args, **kwargs)

            func_name = f"{func.__module__}.{func.__name__}"
            start = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                self.function_stats[func_name]["errors"] += 1
                raise
            finally:
                elapsed = time.perf_counter() - start
                self._record_timing(func_name, elapsed)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def _record_timing(self, func_name: str, elapsed: float):
        """Record timing for a function call."""
        stats = self.function_stats[func_name]
        stats["calls"] += 1
        stats["total_time"] += elapsed
        stats["min_time"] = min(stats["min_time"], elapsed)
        stats["max_time"] = max(stats["max_time"], elapsed)

    def get_stats(self) -> dict[str, dict[str, Any]]:
        """Get all profiling statistics."""
        results = {}

        for func_name, stats in self.function_stats.items():
            avg_time = stats["total_time"] / stats["calls"] if stats["calls"] > 0 else 0
            results[func_name] = {
                "calls": stats["calls"],
                "total_time": stats["total_time"],
                "avg_time": avg_time,
                "min_time": (
                    stats["min_time"] if stats["min_time"] != float("inf") else 0
                ),
                "max_time": stats["max_time"],
                "errors": stats["errors"],
            }

        return results

    def get_hotspots(self, top_n: int = 10) -> list[tuple[str, dict]]:
        """Get top N hotspots by total time."""
        stats = self.get_stats()
        sorted_stats = sorted(
            stats.items(), key=lambda x: x[1]["total_time"], reverse=True
        )
        return sorted_stats[:top_n]

    def get_slow_functions(self, threshold_ms: float = 10.0) -> list[tuple[str, dict]]:
        """Get functions with average time above threshold."""
        stats = self.get_stats()
        threshold_sec = threshold_ms / 1000.0

        slow_funcs = [
            (name, stat)
            for name, stat in stats.items()
            if stat["avg_time"] > threshold_sec
        ]

        return sorted(slow_funcs, key=lambda x: x[1]["avg_time"], reverse=True)

    def get_system_stats(self) -> dict[str, Any]:
        """Get current system resource usage."""
        return {
            "cpu_percent": self.process.cpu_percent(interval=0.1),
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "memory_percent": self.process.memory_percent(),
            "num_threads": self.process.num_threads(),
            "num_fds": (
                self.process.num_fds() if hasattr(self.process, "num_fds") else None
            ),
        }

    def print_report(self, top_n: int = 20):
        """Print performance report."""
        print("\n" + "=" * 80)
        print("LANrage Performance Report")
        print("=" * 80)

        # System stats
        sys_stats = self.get_system_stats()
        print("\n📊 System Resources:")
        print(f"  CPU: {sys_stats['cpu_percent']:.1f}%")
        print(
            f"  Memory: {sys_stats['memory_mb']:.1f} MB ({sys_stats['memory_percent']:.1f}%)"
        )
        print(f"  Threads: {sys_stats['num_threads']}")
        if sys_stats["num_fds"]:
            print(f"  File Descriptors: {sys_stats['num_fds']}")

        # Hotspots
        hotspots = self.get_hotspots(top_n)
        if hotspots:
            print(f"\n🔥 Top {len(hotspots)} Hotspots (by total time):")
            for i, (func_name, stats) in enumerate(hotspots, 1):
                print(f"\n  {i}. {func_name}")
                print(f"     Calls: {stats['calls']}")
                print(f"     Total: {stats['total_time']*1000:.2f}ms")
                print(f"     Avg: {stats['avg_time']*1000:.2f}ms")
                print(f"     Min: {stats['min_time']*1000:.2f}ms")
                print(f"     Max: {stats['max_time']*1000:.2f}ms")
                if stats["errors"] > 0:
                    print(f"     ⚠️  Errors: {stats['errors']}")

        # Slow functions
        slow_funcs = self.get_slow_functions(threshold_ms=10.0)
        if slow_funcs:
            print("\n🐌 Slow Functions (avg > 10ms):")
            for func_name, stats in slow_funcs:
                print(f"  {func_name}: {stats['avg_time']*1000:.2f}ms avg")

        # Summary
        total_calls = sum(s["calls"] for s in self.function_stats.values())
        total_time = sum(s["total_time"] for s in self.function_stats.values())
        total_errors = sum(s["errors"] for s in self.function_stats.values())

        print("\n📈 Summary:")
        print(f"  Total function calls: {total_calls}")
        print(f"  Total profiled time: {total_time*1000:.2f}ms")
        print(f"  Total errors: {total_errors}")
        print(f"  Unique functions: {len(self.function_stats)}")

        print("\n" + "=" * 80)


# Global profiler instance
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _profiler


def profile(func: Callable) -> Callable:
    """Decorator to profile a function using the global profiler."""
    return _profiler.profile(func)


class ProfileContext:
    """Context manager for profiling a code block."""

    def __init__(self, name: str):
        """Initialize profile context."""
        self.name = name
        self.start_time = None

    def __enter__(self):
        """Enter context."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        elapsed = time.perf_counter() - self.start_time
        _profiler._record_timing(self.name, elapsed)


def profile_block(name: str) -> ProfileContext:
    """Profile a code block."""
    return ProfileContext(name)
