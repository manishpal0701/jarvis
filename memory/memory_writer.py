import uuid
import time
from memory.memory_policy import MemoryPolicy
from memory.memory_store import MemoryStore

class MemoryWriter:
    """
    High-level memory writer pipeline.
    Enforces record schema formatting, runs policy evaluation, and persists to MemoryStore.
    """
    def __init__(self, store: MemoryStore, policy: MemoryPolicy = None):
        self.store = store
        self.policy = policy or MemoryPolicy()

    def generate_id(self, memory_type: str) -> str:
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:6]
        return f"mem_{memory_type}_{timestamp_str}_{short_uuid}"

    def write(self, content: str, memory_type: str = "semantic", importance: float = None,
              source: str = "agent", project: str = None, task_id: str = None,
              tags: list[str] = None, metadata: dict = None) -> tuple[str | None, str]:
        """
        Creates and stores a new memory record after policy verification.
        Returns (memory_id, status_message).
        """
        existing_records = self.store.get_all_records()
        should_store, reason = self.policy.should_remember(content, memory_type, existing_records)
        
        if not should_store:
            return None, reason

        print("\n[MEMORY WRITER]")
        print(f"Type: {memory_type}")
        print(f"Content: {content.strip()}")

        mem_id = self.generate_id(memory_type)
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        calc_importance = self.policy.evaluate_importance(content, memory_type, importance)

        record = {
            "id": mem_id,
            "user_id": "user_owner",
            "type": memory_type,
            "content": content.strip(),
            "source": source or "system",
            "confidence": 1.0,
            "created_at": now_str,
            "updated_at": now_str,
            "last_used_at": now_str,
            "importance": calc_importance,
            "project": project,
            "task_id": task_id,
            "tags": tags or [],
            "metadata": metadata or {}
        }

        success = self.store.save_record(record)
        if success:
            return mem_id, f"Successfully created memory '{mem_id}'."
        return None, "Failed to persist memory record to store."

    def update(self, memory_id: str, content: str = None, importance: float = None,
               tags: list[str] = None, metadata: dict = None) -> tuple[bool, str]:
        """Updates an existing memory record."""
        record = self.store.get_record(memory_id)
        if not record:
            return False, f"Memory record '{memory_id}' not found."

        if content is not None:
            if self.policy.contains_secret(content):
                return False, "Privacy violation: Updated content contains secrets."
            record["content"] = content.strip()

        if importance is not None:
            record["importance"] = max(0.0, min(1.0, float(importance)))

        if tags is not None:
            record["tags"] = tags

        if metadata is not None:
            record["metadata"].update(metadata)

        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        record["updated_at"] = now_str
        record["last_used_at"] = now_str
        success = self.store.save_record(record)
        return success, "Memory updated successfully." if success else "Failed to update memory."

