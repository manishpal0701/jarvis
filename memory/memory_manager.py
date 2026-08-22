import threading
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

    # Category Specific Methods
    def store_user_preference(self, key: str, value: str) -> str | None:
        mem_id, _ = self.user.set_preference(key, value)
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

