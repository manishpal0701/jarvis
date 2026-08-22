import os
import json
import threading
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_STORE_FILE = os.path.join(DATA_DIR, "memory.json")

class MemoryStore:
    """
    Thread-safe storage abstraction over persistent memory storage (JSON).
    Protects underlying file access and provides fast CRUD operations for memory records.
    """
    def __init__(self, store_file: str = DEFAULT_STORE_FILE):
        self.store_file = os.path.abspath(store_file)
        self._lock = threading.Lock()
        self._records = {}
        self._dirty = False
        self._load()

    def _load(self):
        with self._lock:
            print("\n[MEMORY INIT]")
            print("Loading persistent memories...")
            if not os.path.exists(self.store_file):
                self._records = {}
                print("[MEMORY STORE]")
                print("Loaded: 0")
                print(f"Storage path: {os.path.abspath(self.store_file)}")
                return

            try:
                with open(self.store_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                if isinstance(raw_data, dict):
                    is_record_store = True
                    for k, v in raw_data.items():
                        if not (isinstance(v, dict) and "id" in v and "type" in v and "content" in v):
                            is_record_store = False
                            break

                    if is_record_store:
                        self._records = raw_data
                    else:
                        self._records = {}
                        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
                        for k, v in raw_data.items():
                            rec_id = f"mem_legacy_{k}"
                            self._records[rec_id] = {
                                "id": rec_id,
                                "type": "user",
                                "content": f"{k}: {v}",
                                "source": "legacy_import",
                                "created_at": now_str,
                                "updated_at": now_str,
                                "importance": 0.5,
                                "project": None,
                                "task_id": None,
                                "tags": ["legacy", str(k)],
                                "metadata": {"key": k, "value": v}
                            }
                elif isinstance(raw_data, list):
                    self._records = {r["id"]: r for r in raw_data if isinstance(r, dict) and "id" in r}
                else:
                    self._records = {}
            except Exception as e:
                print(f"[MemoryStore] Warning: Failed to load store ({e}). Starting clean.")
                self._records = {}

            print("[MEMORY STORE]")
            print(f"Loaded: {len(self._records)}")
            print(f"Storage path: {os.path.abspath(self.store_file)}")

    def flush(self):
        """Flushes memory records to persistent file storage atomically under lock."""
        with self._lock:
            try:
                temp_file = f"{self.store_file}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self._records, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, self.store_file)
                self._dirty = False
            except Exception as e:
                print(f"[MemoryStore] Error flushing to disk: {e}")

    def save_record(self, record: dict, flush: bool = True) -> bool:
        """Saves or updates a memory record."""
        if not isinstance(record, dict) or "id" not in record:
            return False
        with self._lock:
            self._records[record["id"]] = record
            self._dirty = True
        if flush:
            self.flush()
        print("\n[MEMORY STORE]")
        print(f"Memory ID: {record['id']}")
        print("Persisted: YES")
        print(f"Storage path: {os.path.abspath(self.store_file)}")
        return True

    def get_record(self, memory_id: str) -> dict | None:
        """Retrieves a single memory record by ID."""
        with self._lock:
            rec = self._records.get(memory_id)
            return rec.copy() if rec else None

    def delete_record(self, memory_id: str) -> bool:
        """Deletes a memory record by ID."""
        with self._lock:
            if memory_id in self._records:
                del self._records[memory_id]
                self._dirty = True
                deleted = True
            else:
                deleted = False
        if deleted:
            self.flush()
        return deleted

    def query_records(self, filter_fn=None) -> list[dict]:
        """Queries memory records based on an optional filter predicate."""
        with self._lock:
            records = list(self._records.values())
        
        if filter_fn is None:
            return [r.copy() for r in records]
        
        results = []
        for r in records:
            try:
                if filter_fn(r):
                    results.append(r.copy())
            except Exception:
                pass
        return results

    def get_all_records(self) -> list[dict]:
        """Returns copies of all records."""
        return self.query_records()

    def clear_all(self):
        """Clears all stored records."""
        with self._lock:
            self._records = {}
            self._dirty = True
        self.flush()
