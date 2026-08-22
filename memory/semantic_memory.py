class SemanticMemory:
    """
    Semantic Memory handler.
    Manages stable facts, knowledge, framework details, and technology stack rules learned during work.
    """
    def __init__(self, writer, retriever):
        self.writer = writer
        self.retriever = retriever

    def add_fact(self, fact: str, importance: float = 0.7, tags: list[str] = None, project: str = None) -> tuple[str | None, str]:
        """Adds a semantic fact to memory."""
        all_tags = ["semantic", "fact"]
        if tags:
            all_tags.extend(tags)
        
        return self.writer.write(
            content=fact,
            memory_type="semantic",
            importance=importance,
            source="knowledge_acquisition",
            project=project,
            tags=all_tags
        )

    def search_facts(self, query: str, limit: int = 5) -> list[dict]:
        """Searches semantic facts relevant to a query."""
        return self.retriever.retrieve_relevant(query, limit=limit, memory_type="semantic")
