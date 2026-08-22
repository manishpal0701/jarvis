import os
from typing import Tuple, Set

class ProtectedFileValidator:
    """
    Guards core internal system files from being overwritten by AI generated code.
    If a requested filename matches a protected system file, automatically renames it
    (e.g., 'main.py' -> 'generated_main.py').
    """

    PROTECTED_FILES: Set[str] = {
        "main.py",
        "config.py",
        "memory.py",
        "workspace_manager.py",
        "code_assistant.py",
        "assistant.py",
        "state_machine.py",
        "timeout_manager.py",
        "code_validator.py",
        "website_planner.py",
        "prompt.py",
        "ai_response_manager.py",
        "memory_manager.py",
        "agents.md",
        "architecture.md",
        "session_manager.py",
        "thread_manager.py",
        "conversation_manager.py",
        "conversation_engine.py"
    }

    @classmethod
    def protect(cls, relative_path: str) -> Tuple[str, bool]:
        """
        Checks if relative_path matches a protected file.
        Returns tuple of (safe_relative_path, was_protected_flag).
        """
        if not relative_path:
            return "generated_program.py", False

        base_name = os.path.basename(relative_path).lower()
        if base_name in cls.PROTECTED_FILES:
            dir_name = os.path.dirname(relative_path)
            new_basename = f"generated_{base_name}"
            safe_path = os.path.join(dir_name, new_basename) if dir_name else new_basename
            return safe_path, True

        return relative_path, False
