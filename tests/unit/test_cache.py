import time

from app.cache.memory import MemoryCache


def test_set_and_get():
    cache = MemoryCache()
    cache.set("k", {"a": 1})
    assert cache.get("k") == {"a": 1}


def test_missing_key_returns_none():
    assert MemoryCache().get("nope") is None


def test_ttl_expiry():
    cache = MemoryCache()
    cache.set("k", "v", ttl_seconds=0.05)
    assert cache.get("k") == "v"
    time.sleep(0.08)
    assert cache.get("k") is None


def test_delete():
    cache = MemoryCache()
    cache.set("k", "v")
    cache.delete("k")
    assert cache.get("k") is None


def test_purge_expired():
    cache = MemoryCache()
    cache.set("stale", "v", ttl_seconds=0.01)
    cache.set("fresh", "v", ttl_seconds=60)
    time.sleep(0.05)
    purged = cache.purge_expired()
    assert purged == 1
    assert cache.get("fresh") == "v"
