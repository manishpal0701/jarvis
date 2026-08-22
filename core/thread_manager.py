import threading
from typing import Callable, Any

class ThreadManager:
    def __init__(self):
        self._active_threads = []
        self._lock = threading.Lock()

    def run_in_background(self, target: Callable[..., Any], args: tuple = (), name: str = None) -> threading.Thread:
        """Runs a function in a background daemon thread."""
        thread = threading.Thread(target=target, args=args, name=name, daemon=True)
        with self._lock:
            # Clean up dead threads
            self._active_threads = [t for t in self._active_threads if t.is_alive()]
            self._active_threads.append(thread)
        thread.start()
        return thread
