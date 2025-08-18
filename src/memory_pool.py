"""
Memory Pool System

This module provides memory pooling for frequently used objects to reduce
allocation overhead and improve performance.

Author: Automation System
Version: 1.0
"""

import gc
import threading
from collections import deque
from typing import Any, Callable, Dict, List, Optional

# =============================================================================
# MEMORY POOL MANAGER
# =============================================================================


class MemoryPool:
    """
    Memory pool for frequently used objects.

    Reduces allocation overhead by reusing objects instead of creating new ones.
    """

    def __init__(self, max_pool_size: int = 100):
        """
        Initialize the memory pool.

        Args:
            max_pool_size: Maximum number of objects to keep in each pool
        """
        self.max_pool_size = max_pool_size
        self.pools: Dict[str, deque] = {}
        self.pool_locks: Dict[str, threading.Lock] = {}
        self.creation_functions: Dict[str, Callable] = {}
        self.reset_functions: Dict[str, Callable] = {}

        # Statistics
        self.stats = {
            "allocations": 0,
            "reuses": 0,
            "pool_hits": 0,
            "pool_misses": 0,
        }
        self.stats_lock = threading.Lock()

    def register_pool(
        self,
        pool_name: str,
        create_func: Callable,
        reset_func: Optional[Callable] = None,
    ) -> None:
        """
        Register a new object pool.

        Args:
            pool_name: Name of the pool
            create_func: Function to create new objects
            reset_func: Function to reset objects for reuse (optional)
        """
        self.pools[pool_name] = deque(maxlen=self.max_pool_size)
        self.pool_locks[pool_name] = threading.Lock()
        self.creation_functions[pool_name] = create_func
        self.reset_functions[pool_name] = reset_func

    def get_object(self, pool_name: str) -> Any:
        """
        Get an object from the pool or create a new one.

        Args:
            pool_name: Name of the pool

        Returns:
            Object from pool or newly created
        """
        if pool_name not in self.pools:
            raise ValueError("Pool '{}' not registered".format(pool_name))

        lock = self.pool_locks[pool_name]
        pool = self.pools[pool_name]

        with lock:
            if pool:
                # Reuse existing object
                obj = pool.popleft()
                self._update_stats("reuses")
                self._update_stats("pool_hits")

                # Reset object if reset function is provided
                if (
                    pool_name in self.reset_functions
                    and self.reset_functions[pool_name]
                ):
                    self.reset_functions[pool_name](obj)

                return obj
            # Create new object
            self._update_stats("pool_misses")
            return self.creation_functions[pool_name]()

    def return_object(self, pool_name: str, obj: Any) -> None:
        """
        Return an object to the pool for reuse.

        Args:
            pool_name: Name of the pool
            obj: Object to return
        """
        if pool_name not in self.pools:
            return  # Silently ignore if pool doesn't exist

        lock = self.pool_locks[pool_name]
        pool = self.pools[pool_name]

        with lock:
            if len(pool) < self.max_pool_size:
                pool.append(obj)

    def clear_pool(self, pool_name: str) -> None:
        """
        Clear a specific pool.

        Args:
            pool_name: Name of the pool to clear
        """
        if pool_name in self.pools:
            with self.pool_locks[pool_name]:
                self.pools[pool_name].clear()

    def clear_all_pools(self) -> None:
        """Clear all pools."""
        for pool_name in self.pools:
            self.clear_pool(pool_name)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        with self.stats_lock:
            stats = self.stats.copy()

        # Add pool-specific stats
        pool_stats = {}
        for pool_name, pool in self.pools.items():
            with self.pool_locks[pool_name]:
                pool_stats[pool_name] = {
                    "size": len(pool),
                    "max_size": self.max_pool_size,
                }

        stats["pools"] = pool_stats
        return stats

    def _update_stats(self, stat_name: str) -> None:
        """Update statistics thread-safely."""
        with self.stats_lock:
            if stat_name in self.stats:
                self.stats[stat_name] += 1


# =============================================================================
# GLOBAL MEMORY POOL INSTANCE
# =============================================================================

# Global memory pool instance
_memory_pool = MemoryPool()


def get_memory_pool() -> MemoryPool:
    """Get the global memory pool instance."""
    return _memory_pool


# =============================================================================
# POOL-SPECIFIC HELPERS
# =============================================================================


def create_string_pool() -> None:
    """Create a pool for frequently used strings."""

    def create_string():
        return ""

    def reset_string(_s: str):
        # Strings are immutable, so we can't reset them
        # Just return a new empty string
        return ""

    _memory_pool.register_pool("strings", create_string, reset_string)


def create_list_pool() -> None:
    """Create a pool for frequently used lists."""

    def create_list():
        return []

    def reset_list(lst: List):
        lst.clear()
        return lst

    _memory_pool.register_pool("lists", create_list, reset_list)


def create_dict_pool() -> None:
    """Create a pool for frequently used dictionaries."""

    def create_dict():
        return {}

    def reset_dict(d: Dict):
        d.clear()
        return d

    _memory_pool.register_pool("dicts", create_dict, reset_dict)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_string() -> str:
    """Get a string from the pool."""
    return _memory_pool.get_object("strings")


def return_string(s: str) -> None:
    """Return a string to the pool."""
    _memory_pool.return_object("strings", s)


def get_list() -> List:
    """Get a list from the pool."""
    return _memory_pool.get_object("lists")


def return_list(lst: List) -> None:
    """Return a list to the pool."""
    _memory_pool.return_object("lists", lst)


def get_dict() -> Dict:
    """Get a dictionary from the pool."""
    return _memory_pool.get_object("dicts")


def return_dict(d: Dict) -> None:
    """Return a dictionary to the pool."""
    _memory_pool.return_object("dicts", d)


# =============================================================================
# INITIALIZATION
# =============================================================================


def initialize_memory_pools() -> None:
    """Initialize all memory pools."""
    create_string_pool()
    create_list_pool()
    create_dict_pool()


def cleanup_memory_pools() -> None:
    """Clean up all memory pools."""
    _memory_pool.clear_all_pools()
    gc.collect()


# Initialize pools on module import
initialize_memory_pools()
