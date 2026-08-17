# JARVIS Architecture Overview

This document provides a comprehensive technical breakdown of the Jarvis AI Assistant architecture, module responsibilities, dependency rules, data flows, technical debt, and planned future evolution.

---

## 1. Project Overview

Jarvis is a Python-based personal AI assistant equipped with voice-driven interaction, local LLM intelligence (via Ollama), code assistance, stock analysis, system monitoring, memory persistence, face recognition, and video editing integration.

---

## 2. Directory & Module Responsibilities

```text
JARVIS/
│
├── main.py                     # Entry point & command routing orchestrator
├── config.py                   # Global system configuration & environment paths
├── requirements.txt            # Python dependencies
├── ARCHITECTURE.md             # System architecture & design documentation
├── AGENTS.md                   # AI Coding Agent behavioral guidelines & project rules
│
├── core/                       # System-level orchestration & infrastructure
│   ├── __init__.py
│   ├── state_machine.py        # Thread-safe StateMachine & State enum
│   ├── session_manager.py      # Voice session active flag manager
│   ├── thread_manager.py       # Daemon background thread executor
│   ├── timeout_manager.py      # Session inactivity timeout tracking
│   └── monitor.py              # Screen OCR monitoring functions
│
├── conversation/               # Conversation engine, speaker context & history
│   ├── __init__.py
│   ├── conversation_manager.py # Speaker state (owner/guest), history & log persistence
│   ├── conversation_engine.py  # Main conversational state machine execution loop
│   ├── context_manager.py      # Thread-safe wrapper around ConversationManager
│   └── chat_responses.py       # Dynamic chat responses & personalization
│
├── ai/                         # LLM / Ollama communication & prompt engineering
│   ├── __init__.py
│   ├── ask_ollama.py           # Prompt assembly, target speaker parsing & Ollama call
│   ├── ai_response_manager.py  # Model prewarming & persistent client singleton
│   └── prompt.py               # Prompt templates (code generation, code review, etc.)
│
├── agent/                      # Autonomous Reasoning Engine (FUTURE / NOT IMPLEMENTED YET)
│   ├── __init__.py
│   └── README.md
│
├── memory/                     # Memory Layer (Phase 1 Subsystem)
│   ├── __init__.py
│   ├── memory_manager.py       # Central facade API for all memory operations
│   ├── memory_store.py         # Thread-safe persistence engine (data/memory.json)
│   ├── memory_retriever.py     # Relevance & type keyword ranker
│   ├── memory_writer.py        # Memory record creation & update pipeline
│   ├── memory_policy.py       # Rule engine, privacy secret filter, deduplication
│   ├── working_memory.py       # Session-level transient context (task/step/file)
│   ├── episodic_memory.py      # History of past events, actions & outcomes
│   ├── semantic_memory.py      # Stable facts & tech stack knowledge
│   ├── user_memory.py          # Long-term user preferences & identity rules
│   ├── project_memory.py       # Project specifications, milestones & issues
│   ├── task_memory.py          # Task tracking & completion status
│   └── memory.py               # Backwards compatibility wrapper for load/save_memory
│
├── tools/                      # Executable tools and capability integrations
│   ├── __init__.py
│   ├── coding/                 # Flutter code generator, reviewer, scanner
│   ├── computer/               # App launcher, file I/O, music library
│   ├── web/                    # Web browsing capabilities
│   ├── video/                  # Video editing integrations
│   └── monitoring/             # System monitoring utilities
│
├── speech/                     # Voice input / output audio pipeline
│   ├── __init__.py
│   ├── speech_coordinator.py   # Audio lock synchronization & speech state transitions
│   ├── listener_manager.py     # Microphone listening & Google speech recognition
│   ├── wake_manager.py         # Wake-word ("jarvis") detection
│   └── sleep_manager.py        # Inactivity/command sleep transition
│
├── vision/                     # Visual perception & biometric recognition
│   ├── __init__.py
│   └── face_recognize.py       # OpenCV camera capture & DeepFace ArcFace embeddings
│
├── security/                   # Authentication & access control
│   ├── __init__.py
│   └── voice_security.py       # Password verification logic
│
├── finance/                    # Stock market analysis & financial lookup
│   ├── __init__.py
│   ├── stock_analyzer.py       # Multi-timeframe technical indicator analysis engine
│   └── stock_search.py        # Symbol lookup using LLM
│
├── tests/                      # Unit test suites
│   ├── __init__.py
│   └── test_memory_layer.py    # Memory Layer test suite
│
├── video_editing/              # Video editing agent & CEP bridge extensions
│
└── data/                       # Persistent runtime data files & databases
    ├── jarvis_cache.json
    ├── completed_trades.json
    ├── conversation_logs.json
    ├── memory.json
    ├── face_database.pkl
    └── jarvis_edit.xml
```

---

## 3. Memory Subsystem Architecture (Phase 1)

The Memory Layer provides a unified, independent subsystem between Jarvis components and persistent memory storage.

```text
                                User Input / Conversation
                                           │
                                           ▼
                                    MemoryManager
                                           │
    ┌────────────────┬─────────────────────┼─────────────────────┬────────────────┐
    ▼                ▼                     ▼                     ▼                ▼
WorkingMemory  EpisodicMemory        SemanticMemory        UserMemory       Project/TaskMemory
    │                │                     │                     │                │
    └────────────────┴─────────────────────┼─────────────────────┴────────────────┘
                                           │
                      ┌────────────────────┴────────────────────┐
                      ▼                                         ▼
                MemoryPolicy                              MemoryRetriever
               (Secret Filter,                           (Relevance & Type
               Deduplication)                             Keyword Ranker)
                      │                                         │
                      ▼                                         │
                MemoryWriter                                    │
                      │                                         │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                                      MemoryStore
                                (Thread-Safe JSON Engine)
                                           │
                                           ▼
                                   data/memory.json
```

### Memory Categories & Responsibilities
1. **Working Memory**: Transient session state (active task, step, active file, error codes). Cleared when session ends.
2. **Episodic Memory**: Event-based action history, task execution logs, and outcomes.
3. **Semantic Memory**: Stable facts and domain knowledge (tech stack facts, framework details).
4. **User Memory**: Long-term user preferences, communication styles, identity rules.
5. **Project Memory**: Project specifications, architecture markers, stack details, milestones, and issues.
6. **Task Memory**: Task tracking (`task_id`, description, status: `pending`/`in_progress`/`completed`/`failed`, subtasks).

---

## 4. Dependency Rules

1. **Unidirectional Imports**: Higher-level features (e.g. `main.py`, `conversation`, `ai`) may import `core`, `config`, `memory`, and lower-level utilities.
2. **Core Independence**: `core/` modules must never depend on higher-level tools (`tools/`, `finance/`, `vision/`).
3. **Memory Isolation**: No module outside `memory/` should directly access or manipulate `data/memory.json`. All access must pass through `MemoryManager`.
4. **Clean Module Boundaries**: Executable capabilities belong in `tools/`. LLM interaction belongs in `ai/`. Voice interactions belong in `speech/`.
5. **Data Isolation**: All persistent files (`.json`, `.pkl`, `.xml`) live in `data/` and should be referenced via standard path resolves.

---

## 5. System Data Flows

### A. Conversation Flow
```text
User Audio Input -> speech.listener_manager
                 -> core.state_machine (LISTENING -> PROCESSING)
                 -> main.processCommand / ai.ask_ollama
                 -> conversation.conversation_manager (Save history & logs)
                 -> speech.speech_coordinator (SPEAKING) -> Speaker Output
```

### B. AI / LLM & Memory Retrieval Flow
```text
User Request -> ai.ask_ollama
             -> memory.memory_manager.retrieve_relevant(user_input)
             -> Inject relevant memories into system prompt context
             -> ai.ai_response_manager (Prewarmed Ollama Client)
             -> Ollama API (Model: llama3.2) -> Response
```

### C. Tool / Feature Flow
```text
Voice Command -> main.processCommand()
              -> Feature Dispatch:
                 - "check stock"     -> finance.stock_analyzer & stock_search
                 - "write code"      -> tools.coding.code_assistant
                 - "open app"        -> tools.computer.open_app
                 - "who is in front" -> vision.face_recognize
                 - "edit video"      -> video_editing
```

---

## 6. Known Technical Debt

- **Command Routing in `main.py`**: `main.py` contains an `if/elif` chain for voice commands. This will be replaced by the autonomous `agent/` decision engine in future phases.
- **Monkey Patching (`_patch_speak`)**: Dynamic speaker personalization in `ConversationManager` uses runtime monkey patching of `main.speak`. This will be refactored into clean event emission in future phases.

---

## 7. Planned Future Architecture (FUTURE / NOT IMPLEMENTED YET)

```text
[ FUTURE / NOT IMPLEMENTED YET ]

agent/
├── planner.py           # Goal decomposition & step planning
├── executor.py          # Dynamic tool execution & orchestrator
├── verifier.py          # Output validation & self-correction
├── decision_engine.py   # Intent classification & routing
└── autonomous_loop.py   # Continuous background task execution loop
```
