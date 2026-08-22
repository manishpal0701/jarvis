class TaskMemory:
    """
    Task Memory handler.
    Tracks work performed, task descriptions, subtasks, progress status (pending, in_progress, completed, failed).
    """
    def __init__(self, writer, retriever):
        self.writer = writer
        self.retriever = retriever

    def record_task(self, task_id: str, description: str, status: str = "pending",
                    project: str = None, subtasks: list = None, notes: str = None, importance: float = 0.7) -> tuple[str | None, str]:
        """Creates or updates a task memory record."""
        existing = self.retriever.retrieve_task(task_id)
        content = f"Task '{task_id}': {description} [Status: {status}]"
        if notes:
            content += f" | Notes: {notes}"

        metadata = {
            "task_id": task_id,
            "description": description,
            "status": status,
            "subtasks": subtasks or [],
            "notes": notes
        }
        tags = ["task", status.lower()]
        if project:
            tags.append(project.lower())

        if existing:
            success, msg = self.writer.update(
                memory_id=existing["id"],
                content=content,
                importance=importance,
                tags=tags,
                metadata=metadata
            )
            return existing["id"] if success else None, msg

        return self.writer.write(
            content=content,
            memory_type="task",
            importance=importance,
            source="task_tracker",
            project=project,
            task_id=task_id,
            tags=tags,
            metadata=metadata
        )

    def get_task(self, task_id: str) -> dict | None:
        """Retrieves task memory for task_id."""
        return self.retriever.retrieve_task(task_id)

    def list_tasks(self, status: str = None) -> list[dict]:
        """Lists task memories, optionally filtered by status."""
        tasks = self.retriever.retrieve_by_type("task", limit=50)
        if status:
            s_lower = status.lower()
            return [t for t in tasks if t.get("metadata", {}).get("status", "").lower() == s_lower]
        return tasks
