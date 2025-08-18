"""
Performance Profiler

This module provides performance profiling capabilities to identify
critical paths and bottlenecks in the application.

Author: Automation System
Version: 1.0
"""

import functools
import threading
import time
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional

import psutil

# =============================================================================
# PERFORMANCE PROFILER
# =============================================================================


class PerformanceProfiler:
    """
    Performance profiler for identifying bottlenecks and critical paths.
    """

    def __init__(self, max_samples: int = 1000):
        """
        Initialize the performance profiler.

        Args:
            max_samples: Maximum number of samples to keep per function
        """
        self.max_samples = max_samples
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "calls": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "samples": deque(maxlen=max_samples),
                "memory_before": 0.0,
                "memory_after": 0.0,
                "memory_delta": 0.0,
            },
        )
        self.active_profiles: Dict[int, Dict[str, Any]] = {}
        self.profiler_lock = threading.Lock()
        self.enabled = True

    def profile(self, func_name: Optional[str] = None):
        """
        Decorator to profile a function.

        Args:
            func_name: Optional custom name for the function
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                profile_name = func_name or f"{func.__module__}.{func.__name__}"
                return self._profile_function(profile_name, func, *args, **kwargs)

            return wrapper

        return decorator

    def _profile_function(self, func_name: str, func: Callable, *args, **kwargs) -> Any:
        """
        Profile a function execution.

        Args:
            func_name: Name of the function being profiled
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        thread_id = threading.get_ident()
        # profile_id = f"{thread_id}_{func_name}"  # Unused variable

        # Record start time and memory
        start_time = time.perf_counter()
        memory_before = self._get_memory_usage()

        # Execute function
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            raise
        finally:
            # Record end time and memory
            end_time = time.perf_counter()
            memory_after = self._get_memory_usage()

            # Calculate metrics
            execution_time = end_time - start_time
            memory_delta = memory_after - memory_before

            # Update statistics
            self._update_stats(
                func_name,
                execution_time,
                memory_before,
                memory_after,
                memory_delta,
                success,
            )

        return result

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def _update_stats(
        self,
        func_name: str,
        execution_time: float,
        memory_before: float,
        memory_after: float,
        memory_delta: float,
        success: bool,
    ) -> None:
        """Update function statistics."""
        with self.profiler_lock:
            stats = self.function_stats[func_name]
            stats["calls"] += 1
            stats["total_time"] += execution_time
            stats["min_time"] = min(stats["min_time"], execution_time)
            stats["max_time"] = max(stats["max_time"], execution_time)
            stats["samples"].append(
                {
                    "time": execution_time,
                    "memory_before": memory_before,
                    "memory_after": memory_after,
                    "memory_delta": memory_delta,
                    "success": success,
                    "timestamp": time.time(),
                },
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get profiling statistics.

        Returns:
            Dictionary with profiling statistics
        """
        with self.profiler_lock:
            stats = {}
            for func_name, func_stats in self.function_stats.items():
                if func_stats["calls"] > 0:
                    stats[func_name] = {
                        "calls": func_stats["calls"],
                        "total_time": func_stats["total_time"],
                        "avg_time": func_stats["total_time"] / func_stats["calls"],
                        "min_time": func_stats["min_time"],
                        "max_time": func_stats["max_time"],
                        "recent_samples": list(func_stats["samples"])[
                            -10:
                        ],  # Last 10 samples
                        "memory_avg_delta": sum(
                            s["memory_delta"] for s in func_stats["samples"]
                        )
                        / len(func_stats["samples"])
                        if func_stats["samples"]
                        else 0,
                    }
        return stats

    def get_slowest_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the slowest functions by average execution time.

        Args:
            limit: Maximum number of functions to return

        Returns:
            List of slowest functions with their stats
        """
        stats = self.get_stats()
        slowest = sorted(
            list(stats.items()),
            key=lambda x: x[1]["avg_time"],
            reverse=True,
        )[:limit]

        return [
            {
                "function": name,
                "avg_time_ms": data["avg_time"] * 1000,
                "total_time_ms": data["total_time"] * 1000,
                "calls": data["calls"],
                "memory_delta_mb": data["memory_avg_delta"],
            }
            for name, data in slowest
        ]

    def get_memory_intensive_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most memory-intensive functions.

        Args:
            limit: Maximum number of functions to return

        Returns:
            List of most memory-intensive functions
        """
        stats = self.get_stats()
        memory_intensive = sorted(
            list(stats.items()),
            key=lambda x: x[1]["memory_avg_delta"],
            reverse=True,
        )[:limit]

        return [
            {
                "function": name,
                "memory_delta_mb": data["memory_avg_delta"],
                "avg_time_ms": data["avg_time"] * 1000,
                "calls": data["calls"],
            }
            for name, data in memory_intensive
        ]

    def clear_stats(self) -> None:
        """Clear all profiling statistics."""
        with self.profiler_lock:
            self.function_stats.clear()

    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True

    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False


# =============================================================================
# GLOBAL PROFILER INSTANCE
# =============================================================================

# Global profiler instance
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _profiler


def profile(func_name: Optional[str] = None):
    """Decorator to profile a function using the global profiler."""
    return _profiler.profile(func_name)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def print_performance_report() -> None:
    """Print a performance report to console."""
    profiler = get_profiler()

    print("\n" + "=" * 60)
    print("PERFORMANCE PROFILING REPORT")
    print("=" * 60)

    # Slowest functions
    slowest = profiler.get_slowest_functions(5)
    if slowest:
        print("\n🐌 SLOWEST FUNCTIONS:")
        for func in slowest:
            print(
                f"  {func['function']}: {func['avg_time_ms']:.2f}ms avg ({func['calls']} calls)",
            )

    # Memory intensive functions
    memory_intensive = profiler.get_memory_intensive_functions(5)
    if memory_intensive:
        print("\n💾 MEMORY INTENSIVE FUNCTIONS:")
        for func in memory_intensive:
            print(
                f"  {func['function']}: {func['memory_delta_mb']:.2f}MB avg ({func['calls']} calls)",
            )

    # Overall stats
    stats = profiler.get_stats()
    if stats:
        total_calls = sum(s["calls"] for s in stats.values())
        total_time = sum(s["total_time"] for s in stats.values())
        print("\n📊 OVERALL STATS:")
        print(f"  Total function calls: {total_calls}")
        print(f"  Total execution time: {total_time*1000:.2f}ms")
        print(f"  Functions profiled: {len(stats)}")

    # Memory pool stats
    try:
        from .memory_pool import get_memory_pool

        pool = get_memory_pool()
        pool_stats = pool.get_stats()
        if pool_stats and pool_stats.get("pools"):
            print("\n🏊 MEMORY POOL STATS:")
            print(f"  Pool hits: {pool_stats.get('pool_hits', 0)}")
            print(f"  Pool misses: {pool_stats.get('pool_misses', 0)}")
            print(f"  Object reuses: {pool_stats.get('reuses', 0)}")
            for pool_name, pool_info in pool_stats["pools"].items():
                print(
                    f"  {pool_name}: {pool_info['size']}/{pool_info['max_size']} objects",
                )
    except ImportError:
        pass  # Memory pool not available

    print("=" * 60)


def clear_profiling_data() -> None:
    """Clear all profiling data."""
    get_profiler().clear_stats()


def enable_profiling() -> None:
    """Enable profiling."""
    get_profiler().enable()


def disable_profiling() -> None:
    """Disable profiling."""
    get_profiler().disable()
