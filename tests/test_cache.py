"""
Unit tests for the in-memory caching utility (src/utils/cache.py).
"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.cache import Cache


class TestCacheSetAndGet:
    """Tests for basic set/get operations."""

    def test_set_and_get_string_value(self):
        """Cache should store and return a string value."""
        cache = Cache(ttl=60)
        cache.set("key1", "hello")
        assert cache.get("key1") == "hello"

    def test_set_and_get_dict_value(self):
        """Cache should store and return a dict value."""
        cache = Cache(ttl=60)
        data = {"username": "bytebymanas", "score": 42}
        cache.set("user:bytebymanas", data)
        assert cache.get("user:bytebymanas") == data

    def test_get_nonexistent_key_returns_none(self):
        """Requesting a key that was never set should return None."""
        cache = Cache(ttl=60)
        assert cache.get("nonexistent") is None


class TestCacheExpiry:
    """Tests for TTL-based cache expiration."""

    def test_entry_expires_after_ttl(self):
        """Cache entry should expire and return None after TTL seconds."""
        cache = Cache(ttl=1)
        cache.set("temp_key", "temp_value")
        time.sleep(1.1)
        assert cache.get("temp_key") is None

    def test_entry_available_before_expiry(self):
        """Cache entry should still be available before TTL expires."""
        cache = Cache(ttl=10)
        cache.set("active_key", "active_value")
        assert cache.get("active_key") == "active_value"


class TestCacheDelete:
    """Tests for manual cache deletion."""

    def test_delete_removes_key(self):
        """Deleted key should return None on next get."""
        cache = Cache(ttl=60)
        cache.set("to_delete", "value")
        cache.delete("to_delete")
        assert cache.get("to_delete") is None

    def test_delete_nonexistent_key_does_not_raise(self):
        """Deleting a key that doesn't exist should not raise an exception."""
        cache = Cache(ttl=60)
        cache.delete("does_not_exist")  # Should not raise


class TestCacheClear:
    """Tests for clearing the entire cache."""

    def test_clear_removes_all_keys(self):
        """After clear(), all keys should be gone."""
        cache = Cache(ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.size() == 0


class TestCacheStats:
    """Tests for cache statistics."""

    def test_stats_returns_dict(self):
        """stats() should return a dictionary."""
        cache = Cache(ttl=60)
        assert isinstance(cache.stats(), dict)

    def test_stats_active_keys_count(self):
        """stats() should correctly report the number of active keys."""
        cache = Cache(ttl=60)
        cache.set("x", 1)
        cache.set("y", 2)
        stats = cache.stats()
        assert stats["active_keys"] == 2
