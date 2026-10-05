import threading
import re
from memory.memory_store import MemoryStore
from memory.memory_policy import MemoryPolicy
from memory.memory_writer import MemoryWriter
from memory.memory_retriever import MemoryRetriever
from memory.working_memory import WorkingMemory
from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.user_memory import UserMemory
from memory.project_memory import ProjectMemory
from memory.task_memory import TaskMemory

class MemoryManager:
    """
    Central facade and public API interface for the Jarvis Memory Layer.
    Provides thread-safe access to Working, Episodic, Semantic, User, Project, and Task memory.
    Ensures no other module needs to directly manipulate underlying memory files or databases.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MemoryManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, store_file: str = None):
        with self._lock:
            if getattr(self, "_initialized", False) and store_file is None:
                return

            if store_file or not getattr(self, "_initialized", False):
                self._store_engine = MemoryStore(store_file=store_file) if store_file else MemoryStore()
                self.policy = MemoryPolicy()
                self.writer = MemoryWriter(store=self._store_engine, policy=self.policy)
                self.retriever = MemoryRetriever(store=self._store_engine)

                self.working = WorkingMemory()
                self.episodic = EpisodicMemory(writer=self.writer, retriever=self.retriever)
                self.semantic = SemanticMemory(writer=self.writer, retriever=self.retriever)
                self.user = UserMemory(writer=self.writer, retriever=self.retriever)
                self.project = ProjectMemory(writer=self.writer, retriever=self.retriever)
                self.task = TaskMemory(writer=self.writer, retriever=self.retriever)

                self._initialized = True

    # Generic Memory API
    def store(self, content: str, memory_type: str = "semantic", importance: float = None,
              source: str = "agent", project: str = None, task_id: str = None,
              tags: list[str] = None, metadata: dict = None) -> str | None:
        """Stores a piece of content into long-term memory after policy verification."""
        try:
            mem_id, msg = self.writer.write(
                content=content,
                memory_type=memory_type,
                importance=importance,
                source=source,
                project=project,
                task_id=task_id,
                tags=tags,
                metadata=metadata
            )
            return mem_id
        except Exception as e:
            print(f"[MemoryManager] Error storing memory: {e}")
            return None

    def retrieve(self, query: str = None, memory_type: str = None, limit: int = 10) -> list[dict]:
        """Retrieves memories filtered by query or type."""
        try:
            return self.retriever.retrieve_relevant(query=query, limit=limit, memory_type=memory_type)
        except Exception as e:
            print(f"[MemoryManager] Error retrieving memory: {e}")
            return []

    def retrieve_relevant(self, query: str, limit: int = 5, min_score: float = 1.0) -> list[dict]:
        """Retrieves top relevant memories for a natural language query."""
        try:
            return self.retriever.retrieve_relevant(query=query, limit=limit, min_score=min_score)
        except Exception as e:
            print(f"[MemoryManager] Error retrieving relevant memory: {e}")
            return []

    def update(self, memory_id: str, content: str = None, importance: float = None,
               tags: list[str] = None, metadata: dict = None) -> bool:
        """Updates an existing memory record."""
        try:
            success, _ = self.writer.update(memory_id, content=content, importance=importance, tags=tags, metadata=metadata)
            return success
        except Exception as e:
            print(f"[MemoryManager] Error updating memory '{memory_id}': {e}")
            return False

    def delete(self, memory_id: str) -> bool:
        """Deletes a memory record by ID."""
        try:
            return self._store_engine.delete_record(memory_id)
        except Exception as e:
            print(f"[MemoryManager] Error deleting memory '{memory_id}': {e}")
            return False

    def search(self, query: str, memory_type: str = None) -> list[dict]:
        """Searches memory records."""
        try:
            return self.retriever.search(query=query, memory_type=memory_type)
        except Exception as e:
            print(f"[MemoryManager] Error searching memory: {e}")
            return []

    # High-Level Explicit Memory API & Context Injection
    def remember(self, content: str, category: str = "user", key: str = None, value: str = None,
                 importance: float = 1.0, source: str = "explicit_user") -> tuple[str | None, str]:
        """
        Stores or updates an explicit memory statement with deduplication and conflict resolution.
        Returns (memory_id, status_message).
        """
        try:
            if not content or not isinstance(content, str):
                return None, "Empty content"

            # Check privacy & secret policy
            if self.policy.contains_secret(content):
                return None, "Privacy violation: Contains sensitive data."

            content_clean = content.strip()
            records = self._store_engine.get_all_records()

            # 1. Deduplication: Check if identical content already exists
            for rec in records:
                if rec.get("content", "").strip().lower() == content_clean.lower():
                    print(f"[MEMORY_DEDUPE] content='{content_clean[:30]}...' existing_id='{rec['id']}'")
                    # Refresh timestamp on existing record
                    self.writer.update(rec["id"], importance=importance)
                    return rec["id"], "Memory already exists (deduplicated)."

            # Infer key for common preference patterns if not provided
            inferred_key = key
            if not inferred_key:
                content_lower = content_clean.lower()
                if any(f in content_lower for f in ["flutter", "react", "vue", "riverpod", "provider"]):
                    inferred_key = "preferred_framework"
                elif any(l in content_lower for l in ["python", "javascript", "dart", "typescript", "hinglish"]):
                    inferred_key = "preferred_language"

            key_clean = inferred_key.lower() if inferred_key else None

            # 2. Conflict Resolution: If an existing memory has the same preference key, update it
            if key_clean:
                for rec in records:
                    rec_key = rec.get("metadata", {}).get("preference_key") or rec.get("metadata", {}).get("key")
                    tags = [t.lower() for t in rec.get("tags", [])]
                    matches_key = (rec_key and str(rec_key).lower() == key_clean) or (key_clean in tags)

                    if matches_key:
                        updated_content = content_clean if not value else f"User preference: {inferred_key} = {value}"
                        updated, msg = self.writer.update(
                            rec["id"],
                            content=updated_content,
                            importance=importance,
                            metadata={"key": inferred_key, "value": value, "preference_key": inferred_key, "preference_value": value, "source": source}
                        )
                        if updated:
                            print(f"[MEMORY_UPDATE] key={inferred_key} record_id={rec['id']}")
                            return rec["id"], f"Updated existing preference for '{inferred_key}'."

            # Direct set_preference if user preference key/value
            if category == "user" and key and value:
                mem_id = self.store_user_preference(key, value)
                if mem_id:
                    print(f"[MEMORY_STORE] category=PREFERENCE key={key}")
                    return mem_id, f"Stored preference '{key}'."

            mem_id, msg = self.writer.write(
                content=content_clean,
                memory_type=category if category in {"working", "episodic", "semantic", "user", "project", "task"} else "user",
                importance=importance,
                source=source,
                tags=["explicit", category] + ([key_clean] if key_clean else []),
                metadata={"key": inferred_key or key, "value": value} if (inferred_key or key) else {}
            )
            if mem_id:
                print(f"[MEMORY_STORE] category={category.upper()} key={inferred_key or key or 'statement'}")
            return mem_id, msg
        except Exception as e:
            print(f"[MemoryManager] Error in remember: {e}")
            return None, str(e)


    def forget(self, query_or_key: str) -> bool:
        """
        Removes stored memory matching a key or natural query.
        Returns True if any memory was deleted.
        """
        try:
            if not query_or_key or not isinstance(query_or_key, str):
                return False

            key_clean = query_or_key.strip().lower()
            stop_words = {"that", "i", "my", "prefer", "the", "a", "an", "about"}
            terms = [t for t in re.findall(r"\w+", key_clean) if t not in stop_words and len(t) >= 2]

            records = self._store_engine.get_all_records()
            deleted_any = False

            for rec in records:
                rec_key = rec.get("metadata", {}).get("preference_key") or rec.get("metadata", {}).get("key")
                rec_val = rec.get("metadata", {}).get("preference_value") or rec.get("metadata", {}).get("value")
                rec_content = rec.get("content", "").lower()
                tags = [t.lower() for t in rec.get("tags", [])]

                matches_key = rec_key and str(rec_key).lower() == key_clean
                matches_content = key_clean in rec_content or key_clean in tags
                matches_terms = bool(terms) and any(
                    (rec_key and t in str(rec_key).lower()) or
                    (rec_val and t in str(rec_val).lower()) or
                    (t in rec_content) or
                    any(t == tag or t in tag for tag in tags)
                    for t in terms
                )

                if matches_key or matches_content or matches_terms:
                    success = self._store_engine.delete_record(rec["id"])
                    if success:
                        deleted_any = True
                        print(f"[MEMORY_FORGET] key={rec_key or query_or_key}")

            return deleted_any
        except Exception as e:
            print(f"[MemoryManager] Error in forget: {e}")
            return False

    def recall(self, query: str = None, limit: int = 5) -> list[dict]:
        """
        Retrieves relevant long-term memories for a query or list of all user memories.
        """
        try:
            if not query or not query.strip():
                memories = self.user.get_user_memories()[:limit]
            else:
                memories = self.retriever.retrieve_relevant(query=query, limit=limit, min_score=0.5)

            print(f"[MEMORY_RECALL] query=\"{query or 'ALL'}\" results={len(memories)}")
            return memories
        except Exception as e:
            print(f"[MemoryManager] Error in recall: {e}")
            return []

    def get_memory_context_for_prompt(self, user_input: str, max_memories: int = 3) -> str:
        """
        Retrieves top relevant memories (<100ms) for prompt injection.
        Returns formatted memory context block or empty string.
        """
        try:
            if not user_input or not isinstance(user_input, str):
                return ""

            memories = self.retriever.retrieve_relevant(query=user_input, limit=max_memories, min_score=1.0)
            if not memories:
                # Fall back to user preferences if explicit question about user/preference
                if any(w in user_input.lower() for w in ["preference", "remember", "prefer", "like", "favorite", "about me"]):
                    memories = self.user.get_user_memories()[:max_memories]

            if not memories:
                print("[MEMORY_CONTEXT] injected=0")
                return ""

            lines = ["RELEVANT MEMORIES:"]
            for m in memories:
                content = m.get("content", "").strip()
                if content:
                    lines.append(f"- {content}")

            context_block = "\n".join(lines)
            print(f"[MEMORY_CONTEXT] injected={len(memories)}")
            return context_block
        except Exception as e:
            print(f"[MemoryManager] Error building memory context: {e}")
            return ""

    def clear_session_conversation(self):
        """Clears transient working memory session state."""
        self.working.clear()

    # Category Specific Methods
    def store_user_preference(self, key: str, value: str, importance: float = 1.0) -> str | None:
        mem_id, _ = self.user.set_preference(key, value, importance=importance)
        return mem_id


    def retrieve_user_memory(self) -> list[dict]:
        return self.user.get_user_memories()

    def store_project_info(self, project_name: str, key: str, value: str) -> str | None:
        mem_id, _ = self.project.record_project_info(project_name, key, value)
        return mem_id

    def retrieve_project(self, project_name: str) -> list[dict]:
        return self.project.get_project_memories(project_name)

    def store_task(self, task_id: str, description: str, status: str = "pending",
                   project: str = None, subtasks: list = None, notes: str = None) -> str | None:
        mem_id, _ = self.task.record_task(task_id, description, status=status, project=project, subtasks=subtasks, notes=notes)
        return mem_id

    def retrieve_task(self, task_id: str) -> dict | None:
        return self.task.get_task(task_id)

    def log_event(self, action: str, outcome: str = "success", details: str = None,
                  project: str = None, task_id: str = None) -> str | None:
        mem_id, _ = self.episodic.log_event(action, outcome=outcome, details=details, project=project, task_id=task_id)
        return mem_id

    def retrieve_recent_events(self, limit: int = 10) -> list[dict]:
        return self.episodic.get_recent_events(limit=limit)

    # Working Memory Methods
    def set_working_context(self, key: str, value: any):
        self.working.set(key, value)

    def get_working_context(self, key: str = None, default: any = None) -> any:
        if key is None:
            return self.working.get_all()
        return self.working.get(key, default)

    def set_website_session(self, session_data: dict):
        self.working.set_website_session(session_data)

    def get_website_session(self) -> dict | None:
        return self.working.get_website_session()

    def clear_website_session(self):
        self.working.clear_website_session()

    def clear_working_memory(self):
        self.working.clear()


# Global Backward Compatibility Functions (Rule 6)
def load_memory() -> dict:
    """Backward compatible loader for legacy memory storage consumers."""
    mgr = MemoryManager()
    records = mgr._store_engine.get_all_records()
    data = {}
    for r in records:
        key = r.get("metadata", {}).get("preference_key") or r.get("metadata", {}).get("key") or r.get("id")
        val = r.get("metadata", {}).get("preference_value") or r.get("metadata", {}).get("value") or r.get("content")
        data[key] = val
    return data

def save_memory(data: dict) -> bool:
    """Backward compatible saver for legacy memory storage consumers."""
    mgr = MemoryManager()
    if isinstance(data, dict):
        for k, v in data.items():
            mgr.remember(f"{k}: {v}", category="user", key=str(k), value=str(v), source="legacy_save_memory")
        return True
    return False


