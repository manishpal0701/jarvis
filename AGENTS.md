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

---

## 12. Master Production App Builder Guidelines (24 Rules)

Whenever the user requests JARVIS to build an application ("Jarvis, build an app..."):

1. **Product-First Rule**: Analyze app purpose, target users, primary user journey, required screens, navigation hierarchy, core features, data flow, API requirements, authentication, loading/error/empty states, responsive behavior, and visual identity before code generation. Never generate an empty dashboard or stub screens.
2. **Required App Architecture**: Enforce standard Flutter production directory layout (`lib/core/`, `models/`, `services/`, `providers/`, `screens/`, `widgets/`, `main.dart`).
3. **Complete Navigation Is Mandatory**: Build the full user journey (`Splash` -> `Onboarding` -> `Login`/`Signup` -> `Home Dashboard` -> `Features` -> `Search` -> `Profile` -> `Settings` -> `Logout`) without dead buttons or broken routes.
4. **Dashboard Must Be A Real Dashboard**: Displays active stats, recent activity, featured content, quick action shortcuts, and bottom navigation.
5. **Professional UI/UX System**: Consistent typography scale, color palette (Material 3), spacing system, and standard UI widgets.
6. **Icons Required**: Semantic icon usage for actions and navigation.
7. **Top Bar + Bottom Navigation**: Active tab highlighting, contextual header actions, search and profile entry points.
8. **Functional Search**: Search input, filtering, sorting, and empty search results state functioning against real data.
9. **3D + Animation System**: Purposeful page transitions, hero animations, card entry effects, staggered lists, and micro-interactions.
10. **Production-Quality Empty States**: Designed empty, loading, loaded, error, and retry states for all lists and views.
11. **Real REST API Integration**: Clean layered flow (`UI` -> `Provider/State` -> `Service` -> `API Client` -> `Express/FastAPI` -> `Persistence`).
12. **Backend Must Match Frontend**: Strict schema, endpoint, method, path, parameter, and response matching.
13. **Complete Authentication Flow**: Login, Signup, Session Persistence, Logout, and Auth Guards.
14. **Real Data**: Structured domain models and JSON/DB persistence. Fallback data isolated cleanly.
15. **Responsive Design**: Support for small/large mobile screens, tablets, and desktop using `MediaQuery`, `LayoutBuilder`, `Flexible`, `Expanded`, `SafeArea`.
16. **Error-Proof Code Generation**: Static analysis verification before completion.
17. **Build Verification**: Mandatory `flutter pub get`, `flutter analyze` (0 errors), `flutter test`, `flutter build apk --debug`.
18. **Screen-by-Screen QA**: Automated flow verification across every screen in the application.
19. **Visual QA**: Alignment, hierarchy, typography, colors, theme consistency, and accessibility checks.
20. **No Placeholder UI Policy**: Zero forbidden placeholder strings (`Component Ready`, `Coming Soon`, `Lorem ipsum`, `TODO`).
21. **App Quality Target**: Production App, Release Ready.
22. **Autonomous Build Pipeline**: Structured multi-stage execution pipeline.
23. **JARVIS Must Report Real Progress**: All user-facing announcements must route through `ProgressReporter` -> WebSocket -> `SpeechCoordinator` -> EdgeTTS -> Frontend Audio Engine voice output.
24. **Final Quality Rule**: Quality > speed, functionality > fake completion, production readiness > generated code count.

