import threading
import time


class TTLCache:
    """Tiny in-process TTL cache. get() returns (value, hit) so None can be a cached value."""

    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item and item[0] > time.monotonic():
                return item[1], True
            return None, False

    def set(self, key, value, ttl):
        with self._lock:
            self._data[key] = (time.monotonic() + ttl, value)

    def clear(self):
        with self._lock:
            self._data.clear()


cache = TTLCache()
