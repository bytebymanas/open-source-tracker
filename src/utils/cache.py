"""
In-memory caching utility for the Open Source Contribution Tracker.

Provides a simple TTL-based (time-to-live) cache to reduce repeated
GitHub API calls for the same data. Cache entries expire after a
configurable duration (default: 300 seconds / 5 minutes).

Usage:
    cache = Cache(ttl=300)
    cache.set("user:torvalds", user_data)
    data = cache.get("user:torvalds")  # Returns None if expired
"""

import time
import logging

logger = logging.getLogger(__name__)


class Cache:
    """
    Simple in-memory key-value cache with TTL expiration.

    Each entry is stored with a timestamp. On read, if the entry
    is older than the configured TTL, it is treated as expired
    and removed from the cache.
    """

    def __init__(self, ttl=300):
        """
        Initialize the cache.

        Args:
            ttl (int): Time-to-live in seconds. Default is 300 (5 minutes).
        """
        self._store = {}
        self.ttl = ttl

    def set(self, key, value):
        """
        Store a value in the cache under the given key.

        Args:
            key (str): Cache key (e.g. 'user:bytebymanas')
            value (any): Value to store
        """
        self._store[key] = {
            "value": value,
            "stored_at": time.time(),
        }
        logger.debug("Cache SET: %s", key)

    def get(self, key):
        """
        Retrieve a value from the cache.

        Returns None if the key does not exist or the entry has expired.

        Args:
            key (str): Cache key

        Returns:
            any | None: Cached value, or None if missing/expired
        """
        entry = self._store.get(key)
        if entry is None:
            return None

        age = time.time() - entry["stored_at"]
        if age > self.ttl:
            logger.debug("Cache EXPIRED: %s (age=%.1fs)", key, age)
            del self._store[key]
            return None

        logger.debug("Cache HIT: %s (age=%.1fs)", key, age)
        return entry["value"]

    def delete(self, key):
        """
        Remove a key from the cache.

        Args:
            key (str): Cache key to delete
        """
        if key in self._store:
            del self._store[key]
            logger.debug("Cache DELETE: %s", key)

    def clear(self):
        """Remove all entries from the cache."""
        self._store.clear()
        logger.debug("Cache CLEARED")

    def size(self):
        """
        Return the number of entries currently in the cache
        (including potentially expired entries not yet evicted).

        Returns:
            int: Number of stored keys
        """
        return len(self._store)

    def stats(self):
        """
        Return a summary of cache state.

        Returns:
            dict: Cache statistics
        """
        now = time.time()
        active = sum(
            1 for e in self._store.values()
            if now - e["stored_at"] <= self.ttl
        )
        return {
            "total_keys": len(self._store),
            "active_keys": active,
            "expired_keys": len(self._store) - active,
            "ttl_seconds": self.ttl,
        }


# Module-level default cache instance (shared across the app)
default_cache = Cache(ttl=300)
