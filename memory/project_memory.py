class ProjectMemory:
    """
    Project Memory handler.
    Manages project specifications, tech stack details, architecture milestones, and known issues per project.
    """
    def __init__(self, writer, retriever):
        self.writer = writer
        self.retriever = retriever

    def record_project_info(self, project_name: str, key: str, value: str, importance: float = 0.8) -> tuple[str | None, str]:
        """Records a piece of information about a project."""
        content = f"Project '{project_name}' {key}: {value}"
        return self.writer.write(
            content=content,
            memory_type="project",
            importance=importance,
            source="project_tracker",
            project=project_name,
            tags=["project", project_name.lower(), key.lower()],
            metadata={"project": project_name, "key": key, "value": value}
        )

    def get_project_memories(self, project_name: str) -> list[dict]:
        """Retrieves memories for a given project."""
        return self.retriever.retrieve_project(project_name)
