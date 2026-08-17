# Guidelines for AI Coding Agents (AGENTS.md)

Welcome, AI Coding Agent. Follow these strict guidelines when working on the Jarvis codebase.

---

## Core Guidelines

1. **Read Architecture First**: Always read `ARCHITECTURE.md` before making architectural or structural changes to the project.
2. **No Random Root Files**: Do NOT create new Python files in the root directory (`JARVIS/`). All new features must be placed inside the appropriate subpackage (`core/`, `conversation/`, `ai/`, `tools/`, `speech/`, `memory/`, `vision/`, `security/`, `finance/`, `data/`, `tests/`).
3. **Keep `main.py` Lightweight**: Avoid adding feature logic to `main.py`. `main.py` is reserved as the application entry point and orchestrator.
4. **Audit Before Implementing**: Search the codebase for existing utilities, helpers, or classes before writing new implementations. Do not duplicate existing functionality.
5. **Respect Module Boundaries**:
   - Future Agentic AI functionality belongs inside `agent/`.
   - Executable capabilities and tools belong inside `tools/`.
   - LLM / Ollama communication belongs inside `ai/`.
   - Conversation history, context, and engine belong inside `conversation/`.
   - Memory management and storage belong inside `memory/`.
   - Speech synthesis and voice session management belong inside `speech/`.
   - System orchestration, state machine, and timeouts belong inside `core/`.
6. **Memory Subsystem Rules**:
   - Do NOT directly access or manipulate `data/memory.json` or underlying storage from feature modules.
   - ALWAYS use `MemoryManager` (`from memory.memory_manager import MemoryManager`) for memory store and retrieval operations.
   - Do NOT automatically store every spoken conversation or LLM response into long-term memory.
   - Do NOT store sensitive information, credentials, passwords, tokens, or API keys in memory.
   - Do NOT create random memory files outside `data/`. Keep all memory subsystem logic encapsulated within `memory/`.
   - Preserve backward compatibility for `load_memory()` and `save_memory()` functions.
7. **Preserve Functionality**: Do NOT remove or modify working capabilities without explicit permission from the user.
8. **Check Dependencies Before Moving Files**: Always perform a project-wide search for references before moving or renaming files.
9. **Explicit Package Imports**: Use explicit Python package imports (e.g. `from core.state_machine import State`) instead of `sys.path` hacks.
10. **Data File Safety**: Store all persistent runtime data (`.json`, `.pkl`, `.xml`) in `data/`. Never delete or overwrite user data files without backup.
11. **Verification**: Always run Python syntax compilation checks (`python -m py_compile`) and test suites (`python -m unittest tests/test_memory_layer.py`) after making changes.
