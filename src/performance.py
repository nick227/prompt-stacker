"""
Performance Monitoring and Optimization System

Monitors and optimizes performance for the Cursor automation system.
Addresses memory leaks, UI responsiveness, and resource usage.
"""

import gc
import threading
import time
import weakref
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import psutil

try:
    from .error_handler import log_error, log_info, log_warning
except ImportError:
    # Fallback for when running as script
    from error_handler import log_error, log_info, log_warning

# =============================================================================
# PERFORMANCE METRICS
# =============================================================================


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    # Memory usage
    memory_usage_mb: float = 0.0
    memory_percent: float = 0.0

    # CPU usage
    cpu_percent: float = 0.0
    cpu_count: int = 0

    # Timing
    execution_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    # UI metrics
    ui_responsiveness_ms: float = 0.0
    event_queue_size: int = 0

    # Custom metrics
    custom_metrics: Dict[str, float] = field(default_factory=dict)


# =============================================================================
# PERFORMANCE MONITOR
# =============================================================================


class PerformanceMonitor:
    """Monitors system and application performance."""

    def __init__(self, sample_interval: float = 1.0, max_samples: int = 100):
        """Initialize the performance monitor."""
        self.sample_interval = sample_interval
        self.max_samples = max_samples
        self.samples: deque = deque(maxlen=max_samples)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Performance thresholds
        self.memory_threshold_mb = 500.0  # 500MB
        self.cpu_threshold_percent = 80.0  # 80%
        self.ui_responsiveness_threshold_ms = 100.0  # 100ms

        # Callbacks
        self.threshold_callbacks: List[Callable[[PerformanceMetrics], None]] = []

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.stop_event.clear()

        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="PerformanceMonitor",
        )
        self.monitor_thread.start()

        log_info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.stop_event.set()

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)

        log_info("Performance monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self.stop_event.is_set():
            try:
                metrics = self._collect_metrics()
                self.samples.append(metrics)

                # Check thresholds
                self._check_thresholds(metrics)

                # Sleep until next sample
                self.stop_event.wait(self.sample_interval)

            except Exception as e:
                log_error(f"Error in performance monitoring: {e}")
                time.sleep(self.sample_interval)

    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        process = psutil.Process()

        # Memory metrics
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()

        # CPU metrics
        cpu_percent = process.cpu_percent()
        cpu_count = psutil.cpu_count()

        # System metrics
        # Removed unused variable

        return PerformanceMetrics(
            memory_usage_mb=memory_usage_mb,
            memory_percent=memory_percent,
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            timestamp=time.time(),
        )

    def _check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check performance thresholds and trigger callbacks."""
        warnings = []

        if metrics.memory_usage_mb > self.memory_threshold_mb:
            warnings.append(f"High memory usage: {metrics.memory_usage_mb:.1f}MB")

        if metrics.cpu_percent > self.cpu_threshold_percent:
            warnings.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        if warnings:
            log_warning(f"Performance warnings: {'; '.join(warnings)}")

            # Trigger callbacks
            for callback in self.threshold_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    log_error(f"Error in performance callback: {e}")

    def add_threshold_callback(
        self,
        callback: Callable[[PerformanceMetrics], None],
    ) -> None:
        """Add a callback for threshold violations."""
        self.threshold_callbacks.append(callback)

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics."""
        return self.samples[-1] if self.samples else None

    def get_average_metrics(
        self,
        window_seconds: float = 60.0,
    ) -> Optional[PerformanceMetrics]:
        """Get average metrics over a time window."""
        if not self.samples:
            return None

        cutoff_time = time.time() - window_seconds
        recent_samples = [s for s in self.samples if s.timestamp >= cutoff_time]

        if not recent_samples:
            return None

        # Calculate averages
        avg_memory = sum(s.memory_usage_mb for s in recent_samples) / len(
            recent_samples,
        )
        avg_cpu = sum(s.cpu_percent for s in recent_samples) / len(recent_samples)

        return PerformanceMetrics(
            memory_usage_mb=avg_memory,
            cpu_percent=avg_cpu,
            timestamp=time.time(),
        )


# =============================================================================
# MEMORY OPTIMIZER
# =============================================================================


class MemoryOptimizer:
    """Optimizes memory usage and prevents memory leaks."""

    def __init__(self):
        """Initialize the memory optimizer."""
        self.weak_refs: List[weakref.ref] = []
        self.cleanup_callbacks: List[Callable[[], None]] = []
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 30.0  # 30 seconds

    def register_weak_ref(
        self,
        obj: Any,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """Register a weak reference to an object for cleanup tracking."""

        def cleanup_callback(_ref):
            if callback:
                try:
                    callback()
                except Exception as e:
                    log_error(f"Error in cleanup callback: {e}")

        weak_ref = weakref.ref(obj, cleanup_callback)
        self.weak_refs.append(weak_ref)

    def add_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be executed during cleanup."""
        self.cleanup_callbacks.append(callback)

    def cleanup(self, force: bool = False) -> None:
        """Perform memory cleanup."""
        current_time = time.time()

        # Check if cleanup is needed
        if (
            not force
            and (current_time - self.last_cleanup_time) < self.cleanup_interval
        ):
            return

        self.last_cleanup_time = current_time

        # Execute cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                log_error(f"Error in cleanup callback: {e}")

        # Remove dead weak references
        self.weak_refs = [ref for ref in self.weak_refs if ref() is not None]

        # Force garbage collection
        collected = gc.collect()

        log_info(f"Memory cleanup completed: {collected} objects collected")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "weak_refs_count": len(self.weak_refs),
            "cleanup_callbacks_count": len(self.cleanup_callbacks),
        }


# =============================================================================
# UI PERFORMANCE OPTIMIZER
# =============================================================================


class UIPerformanceOptimizer:
    """Optimizes UI performance and responsiveness."""

    def __init__(self):
        """Initialize the UI performance optimizer."""
        self.update_callbacks: List[Callable[[], None]] = []
        self.last_update_time = time.time()
        self.update_interval = 0.016  # ~60 FPS
        self.batch_updates = True
        self.pending_updates: List[Callable[[], None]] = []

    def add_update_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback for UI updates."""
        self.update_callbacks.append(callback)

    def schedule_update(self, callback: Callable[[], None]) -> None:
        """Schedule a UI update."""
        if self.batch_updates:
            self.pending_updates.append(callback)
        else:
            self._execute_update(callback)

    def _execute_update(self, callback: Callable[[], None]) -> None:
        """Execute a UI update callback."""
        start_time = time.time()

        try:
            callback()
        except Exception as e:
            log_error(f"Error in UI update: {e}")
        finally:
            execution_time = (time.time() - start_time) * 1000
            if execution_time > 16:  # More than 16ms (60 FPS threshold)
                log_warning(f"Slow UI update: {execution_time:.1f}ms")

    def process_pending_updates(self) -> None:
        """Process all pending UI updates."""
        if not self.pending_updates:
            return

        current_time = time.time()
        if (current_time - self.last_update_time) < self.update_interval:
            return

        self.last_update_time = current_time

        # Execute all pending updates
        updates = self.pending_updates.copy()
        self.pending_updates.clear()

        for update in updates:
            self._execute_update(update)

    def optimize_widget_updates(self, widget, updates: Dict[str, Any]) -> None:
        """Optimize widget updates by batching them."""

        def update_widget():
            for attr, value in updates.items():
                try:
                    if hasattr(widget, attr):
                        setattr(widget, attr, value)
                except Exception as e:
                    log_error(f"Error updating widget {attr}: {e}")

        self.schedule_update(update_widget)


# =============================================================================
# PERFORMANCE DECORATORS
# =============================================================================


def measure_performance(func: Callable) -> Callable:
    """Decorator to measure function performance."""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            execution_time = (time.time() - start_time) * 1000
            if execution_time > 100:  # Log slow functions
                log_warning(f"Slow function {func.__name__}: {execution_time:.1f}ms")

    return wrapper


def cache_result(max_age: float = 60.0):
    """Decorator to cache function results."""

    def decorator(func: Callable) -> Callable:
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            current_time = time.time()

            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if (current_time - timestamp) < max_age:
                    return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)

            # Clean old entries
            if len(cache) > 100:  # Limit cache size
                old_keys = [
                    k for k, (_, t) in cache.items() if (current_time - t) > max_age
                ]
                for old_key in old_keys:
                    del cache[old_key]

            return result

        return wrapper

    return decorator


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Global performance monitoring instances
performance_monitor = PerformanceMonitor()
memory_optimizer = MemoryOptimizer()
ui_optimizer = UIPerformanceOptimizer()


# Convenience functions
def start_performance_monitoring() -> None:
    """Start performance monitoring."""
    performance_monitor.start_monitoring()


def stop_performance_monitoring() -> None:
    """Stop performance monitoring."""
    performance_monitor.stop_monitoring()


def cleanup_memory() -> None:
    """Perform memory cleanup."""
    memory_optimizer.cleanup()


def get_performance_stats() -> Dict[str, Any]:
    """Get current performance statistics."""
    current_metrics = performance_monitor.get_current_metrics()
    memory_stats = memory_optimizer.get_memory_stats()

    return {
        "performance": current_metrics.__dict__ if current_metrics else {},
        "memory": memory_stats,
    }
