import threading

class WorkingMemory:
    """
    Session-level transient context.
    Stores active task status, step progress, active file, and intermediate results.
    Cleared/reset when session ends.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            "current_task": None,
            "current_step": None,
            "current_file": None,
            "latest_result": None,
            "context": {}
        }

    def set(self, key: str, value: any):
        """Sets a key-value pair in working memory context."""
        with self._lock:
            if key in self._state and key != "context":
                self._state[key] = value
            else:
                self._state["context"][key] = value

    def get(self, key: str, default: any = None) -> any:
        """Gets a value from working memory context."""
        with self._lock:
            if key in self._state and key != "context":
                return self._state[key]
            return self._state["context"].get(key, default)

    def update_task_state(self, task: str = None, step: str = None, active_file: str = None, result: any = None):
        """Updates core active task state attributes."""
        with self._lock:
            if task is not None:
                self._state["current_task"] = task
            if step is not None:
                self._state["current_step"] = step
            if active_file is not None:
                self._state["current_file"] = active_file
            if result is not None:
                self._state["latest_result"] = result

    def get_all(self) -> dict:
        """Returns a snapshot copy of all working memory state."""
        with self._lock:
            return {
                "current_task": self._state["current_task"],
                "current_step": self._state["current_step"],
                "current_file": self._state["current_file"],
                "latest_result": self._state["latest_result"],
                "context": self._state["context"].copy()
            }

    def set_website_session(self, session_data: dict):
        """Stores active transient website session context."""
        self.set("website_session", session_data)

    def get_website_session(self) -> dict | None:
        """Retrieves active transient website session context."""
        return self.get("website_session", None)

    def clear_website_session(self):
        """Clears transient website session context."""
        with self._lock:
            if "website_session" in self._state["context"]:
                del self._state["context"]["website_session"]

    def clear(self):
        """Clears working memory."""
        with self._lock:
            self._state = {
                "current_task": None,
                "current_step": None,
                "current_file": None,
                "latest_result": None,
                "context": {}
            }

