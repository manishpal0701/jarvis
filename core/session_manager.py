import threading

class SessionManager:
    def __init__(self, state_machine):
        self.state_machine = state_machine
        self._lock = threading.Lock()
        self._session_active = False

    @property
    def is_active(self):
        with self._lock:
            return self._session_active

    def start_session(self):
        with self._lock:
            self._session_active = True

    def end_session(self):
        with self._lock:
            self._session_active = False
