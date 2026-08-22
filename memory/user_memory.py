class UserMemory:
    """
    User Memory handler.
    Manages long-term user preferences, communication styles, identity rules, and owner settings.
    """
    def __init__(self, writer, retriever):
        self.writer = writer
        self.retriever = retriever

    def set_preference(self, key: str, value: str, importance: float = 0.9) -> tuple[str | None, str]:
        """Sets a user preference in memory."""
        content = f"User preference: {key} = {value}"
        return self.writer.write(
            content=content,
            memory_type="user",
            importance=importance,
            source="user_preference",
            tags=["user_preference", key.lower()],
            metadata={"preference_key": key, "preference_value": value}
        )

    def get_user_memories(self) -> list[dict]:
        """Retrieves all stored user memories and preferences."""
        return self.retriever.retrieve_by_type("user", limit=50)
