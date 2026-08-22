class EpisodicMemory:
    """
    Episodic Memory handler.
    Manages history of important past events, actions, user requests, and task outcomes.
    """
    def __init__(self, writer, retriever):
        self.writer = writer
        self.retriever = retriever

    def log_event(self, action: str, outcome: str = "success", details: str = None,
                  project: str = None, task_id: str = None, importance: float = 0.5) -> tuple[str | None, str]:
        """Logs an event to episodic memory."""
        content = f"Event: {action} | Outcome: {outcome}"
        if details:
            content += f" | Details: {details}"
        
        tags = ["event", outcome.lower()]
        if project:
            tags.append(project.lower())

        return self.writer.write(
            content=content,
            memory_type="episodic",
            importance=importance,
            source="event_logger",
            project=project,
            task_id=task_id,
            tags=tags,
            metadata={"action": action, "outcome": outcome, "details": details}
        )

    def get_recent_events(self, limit: int = 10) -> list[dict]:
        """Retrieves recent events."""
        return self.retriever.retrieve_recent_events(limit=limit)
