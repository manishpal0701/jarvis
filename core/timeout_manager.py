import time
import threading

class TimeoutManager:
    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout_seconds = timeout_seconds
        self._last_active = time.time()
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._last_active = time.time()

    def time_remaining(self) -> float:
        with self._lock:
            elapsed = time.time() - self._last_active
            return max(0.0, self.timeout_seconds - elapsed)

    def is_timed_out(self) -> bool:
        return self.time_remaining() <= 0
