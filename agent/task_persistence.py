"""
agent/task_persistence.py
Thread-safe task persistence storage abstraction for JARVIS Agent Orchestrator.
Saves task state, step history, and execution telemetry to data/tasks.json.
"""

import os
import json
import threading
from typing import Dict, List, Optional
from agent.task_model import TaskModel

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

class TaskPersistence:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, storage_file: str = DEFAULT_TASKS_FILE):
        with cls._lock:
            if cls._instance is None:
                cls._instance = TaskPersistence(storage_file)
            return cls._instance

    def __init__(self, storage_file: str = DEFAULT_TASKS_FILE):
        self.storage_file = os.path.abspath(storage_file)
        self._file_lock = threading.Lock()
        self._cache: Dict[str, dict] = {}
        self._load()

    def _load(self):
        with self._file_lock:
            if not os.path.exists(self.storage_file):
                self._cache = {}
                return
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cache = data
                    else:
                        self._cache = {}
            except Exception as e:
                print(f"[TaskPersistence] Warning: Failed to load tasks ({e}). Starting clean.", flush=True)
                self._cache = {}

    def _flush(self):
        try:
            temp_file = f"{self.storage_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=4, ensure_ascii=False)
            os.replace(temp_file, self.storage_file)
        except Exception as e:
            print(f"[TaskPersistence] Error saving to disk: {e}", flush=True)

    def save_task(self, task: TaskModel) -> bool:
        with self._file_lock:
            self._cache[task.task_id] = task.to_dict()
            self._flush()
        return True

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._file_lock:
            data = self._cache.get(task_id)
            return data.copy() if data else None

    def load_task(self, task_id: str) -> Optional[dict]:
        return self.get_task(task_id)

    def list_tasks(self) -> List[dict]:
        with self._file_lock:
            return list(self._cache.values())

    def clear_all(self):
        with self._file_lock:
            self._cache = {}
            self._flush()
