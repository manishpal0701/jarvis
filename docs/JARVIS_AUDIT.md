# JARVIS AI SYSTEM AUDIT & COMPREHENSIVE ARCHITECTURE REPORT

**Audit Date:** August 17, 2026  
**Target Deadline:** August 17, 2026, 11:50 PM  
**Primary Goal:** Ensure Jarvis reliably completes 3 core capabilities:
1. Natural human-like conversation (Hinglish/English, zero repetitive fillers, natural spoken phrasing)
2. Code generation / coding tasks (multi-language code assistant with static analysis & syntax verification)
3. Website creation (HTML/CSS/JS scaffolding, page generation, live local previews)

---

## A. Current Architecture

Jarvis is currently structured as a modular Python application with voice input/output, local LLM integration via Ollama, memory management, face biometrics, financial lookups, and video editing bridge extensions.

### Module Responsibilities:
- **`main.py`**: Application entry point, speech engine initialization, `ConversationEngine` startup, and a 500-line monolithic `if/elif` command router.
- **`config.py`**: System constants, Ollama endpoint, model name (`llama3.2`), paths, speech parameters.
- **`core/`**: Session state tracking (`state_machine.py`), daemon thread launcher (`thread_manager.py`), inactivity timeout monitor (`timeout_manager.py`), session active flag (`session_manager.py`), screen OCR (`monitor.py`), request profiler (`performance_profiler.py`).
- **`conversation/`**: Speaker session context (`conversation_manager.py`), main orchestrator loop (`conversation_engine.py`), thread-safe context wrapper (`context_manager.py`), static chat response fallbacks (`chat_responses.py`).
- **`conversation/intelligence/`**: Regex-based analysis layer (`intent_analyzer.py`, `emotion_analyzer.py`, `language_analyzer.py`, `context_tracker.py`, `response_strategy.py`, `response_validator.py`, `conversation_state.py`).
- **`ai/`**: Ollama HTTP integration (`ai_response_manager.py`), prompt construction & streaming pipeline (`ask_ollama.py`), system prompt templates (`prompt.py`).
- **`memory/`**: Memory facade (`memory_manager.py`), thread-safe store (`memory_store.py`), search/retrieval engine (`memory_retriever.py`), policy/privacy filter (`memory_policy.py`), category memory engines (`working_memory.py`, `episodic_memory.py`, `semantic_memory.py`, `user_memory.py`, `project_memory.py`, `task_memory.py`), legacy compatibility (`memory.py`).
- **`speech/`**: Voice pipeline coordinator (`speech_coordinator.py`), STT microphone listener (`listener_manager.py`), wake word detector (`wake_manager.py`), sleep monitor (`sleep_manager.py`), Edge TTS generator (`speech_engine.py`), voice mapping (`voices.py`), sound FX (`sound_manager.py`), audio queue (`queue_manager.py`).
- **`tools/coding/`**: Hardcoded Flutter code generator & reviewer (`code_assistant.py`), `.dart` file scanner (`project_scanner.py`).
- **`tools/computer/`**: File I/O (`file_manager.py`), app opener (`open_app.py`), local music map (`music_libary.py`).
- **`finance/`**: Technical indicator analysis (`stock_analyzer.py`), LLM ticker search (`stock_search.py`).
- **`vision/`**: DeepFace ArcFace face recognition & biometric registration (`face_recognize.py`).
- **`security/`**: Password verification (`voice_security.py`).
- **`video_editing/`**: CEP bridge & automated Premiere/CapCut timeline editor (`editor_agent.py`, `reasoning_engine.py`).

---

## B. Actual Execution Flow

```text
User Audio Input
  │
  ▼
speech.listener_manager (Google Web STT API, 0.5s ambient noise check)
  │
  ▼
core.state_machine (Transitions: LISTENING -> PROCESSING)
  │
  ▼
main.processCommand(command) [Executed in ThreadManager background thread]
  │
  ├── [Keyword Match: "remember", "check stock", "meet", "who is in front", "edit video", "song", "open app"]
  │     └─ Executed via dedicated module helper in main.py
  │
  ├── [Keyword Match: "write", "create", "generate", "build"] ⚠️ HUGE ROUTING BUG
  │     └─ Routed straight to tools.coding.code_assistant.generate_code()
  │     └─ Generates Flutter .dart code and saves to FLUTTER_PROJECT/lib/<task>.dart
  │
  └── [Fallback: General Conversation]
        └─ ai.ask_ollama_streaming()
             ├─ SpeechCoordinator.begin_speech_session() (State -> THINKING)
             ├─ ConversationAnalyzer.analyze_input() (Intent/Language/Emotion regex)
             ├─ MemoryManager.retrieve_relevant() (JSON keyword search)
             ├─ AIResponseManager.generate_response_streaming() (Ollama llama3.2 HTTP stream)
             ├─ Token boundary regex splits text into sentences
             ├─ SpeechCoordinator.speak_chunk() -> speech.speak() (Edge TTS API network call -> MP3 -> Pygame playback)
             │    └─ ⚠️ State transitions to WAITING_FOR_NEXT_COMMAND after chunk 1 finishes!
             └─ History saved to ConversationManager
```

---

## C. Problems Found

1. **Catastrophic Command Overlap**:
   Lines 401-406 in `main.py` intercept ANY user request containing `"write"`, `"create"`, `"generate"`, or `"build"`. Asking *"write a poem"*, *"create a website"*, or *"build a quick python script"* automatically forces Jarvis to generate Flutter Dart code and save it into a Flutter project folder!
2. **Premature State Machine Transitions**:
   When streaming speech chunks, `SpeechCoordinator.speak()` transitions state to `WAITING_FOR_NEXT_COMMAND` as soon as the first sentence audio finishes playing. This triggers `StateMachine._print_state_transition()`, printing `"Waiting for next command..."` right in the middle of ongoing Ollama streaming or multi-sentence output.
3. **No Verification Before Claiming Task Completion**:
   `main.py` speaks *"Boss task completed"* immediately after writing code files without attempting syntax compilation, execution, or automated verification.
4. **Zero Website Generation Subsystem**:
   There is no website creation agent, HTML/CSS layout engine, or local preview viewer anywhere in `tools/` or `agent/`.
5. **Slow Response Latency (3.5s – 8.0s total per turn)**:
   - STT recalculates ambient noise for `0.5s` on every request.
   - STT relies on Google's cloud API (`recognize_google`), introducing network roundtrips.
   - Speech TTS splits sentences and calls Microsoft Edge TTS web API per sentence over internet.
6. **Local LLM Model Underutilization**:
   The user has 3 local models installed in Ollama (`llama3.2`, `phi4-mini`, `qwen3:4b-instruct`). Currently, `llama3.2` is hardcoded everywhere, leaving `phi4-mini` and `qwen3:4b-instruct` completely unused.
7. **Multiple Uncoordinated LLM Calls per Request**:
   Commands like stock search trigger one LLM call for symbol lookup and another for text response. Code review runs up to 9 LLM calls in nested loops.

---

## D. Duplicate & Overlapping Systems

1. **TTS Speech Invocation**:
   - `speech.speak()` (direct module call) vs `speech_coordinator.speak()` vs `conversation_engine.speech_coordinator.speak()`.
2. **Memory Access & Storage**:
   - `memory.py` (`load_memory()` returning legacy user preference dict) vs `MemoryManager` accessing `data/memory.json`. `main.py` loads `load_memory()` into a global variable at startup but never syncs it with `MemoryManager`.
3. **Ollama Client Instances**:
   - `AIResponseManager` maintains a singleton `ollama.Client()`.
   - `CodeAssistant` creates its own `self.ollama_client = ollama.Client()`.
   - `stock_search.py` imports `ollama` directly and makes standalone `ollama.chat()` calls.
4. **Conversation History Logging**:
   - `ConversationManager` maintains history list & writes `conversation_logs.json`.
   - `main.py` calls `conversation.save_log()`.
   - `ask_ollama_streaming` calls `conv_manager.add_to_history()`.

---

## E. Performance Bottlenecks

| Component | Current Implementation | Latency Cost | Fix / Optimization |
|---|---|---|---|
| **STT** | `speech_recognition` + `recognize_google` + `adjust_for_ambient_noise(0.5)` | 1.5s – 2.5s | One-time ambient noise calibrate; fast local or cached STT wrapper |
| **Memory** | JSON keyword score ranking (`MemoryRetriever`) | 0.005s | Already fast (<10ms), retain local JSON index |
| **LLM 1st Token** | `llama3.2` CPU prompt evaluation (300-500 tokens) | 1.5s – 3.0s | Model prewarming (`keep_alive=-1`), compact prompt formatting |
| **LLM Generation** | `llama3.2` on CPU (~15 tokens/sec) | 1.0s – 3.0s | Stream tokens with sentence chunking |
| **TTS Generation** | `edge_tts` web API request per sentence chunk | 0.8s – 2.0s | Asynchronous chunk synthesis & local audio caching |
| **Tool Execution** | Sequential file scans & blocking subprocesses | 2.0s – 10.0s | Thread pool execution & cached file hashes |

---

## F. Conversation Problems

1. **Unnatural Formal Hindi / Hinglish**:
   - `transliterate_text()` converts Devanagari Hindi into Romanized Hindi, but `EdgeTTSProvider` voice `hi-IN-SwaraNeural` fails to pronounce Romanized Hindi correctly.
   - System prompts occasionally output formal Hindi terms (*saamagri*, *nirdesh*, *upayukt*) when language classifier returns high confidence on Devanagari.
2. **Repetitive Answers & Canned Greetings**:
   - `chat_responses.py` contains static arrays picked with `random.choice`.
   - Lack of repetition penalty or recent output buffer allows the LLM to reuse opening phrasing (*"Certainly Boss"*, *"As an AI..."*).
3. **Hallucinations & False Claims**:
   - Low relevance thresholds in `MemoryRetriever` cause unrelated facts to enter prompt context.

---

## G. Coding-Agent Problems

1. **Hardcoded Flutter / Dart Scope**:
   - `code_assistant.py` is locked to `FLUTTER_PROJECT` (`lib/*.dart`) and `pubspec.yaml`. It cannot create or modify Python, JavaScript, HTML, C++, or standalone shell scripts elsewhere.
2. **No Execution or Verification Loop**:
   - Generated code is written to disk without checking Python syntax (`python -m py_compile`), running tests, or inspecting terminal output for runtime errors.
3. **Interception in `main.py`**:
   - Simple voice instructions (*"write a quick hello world in python"*) get swallowed by line 401 of `main.py` and saved to Flutter `lib/write_a_quick_hello_world_in_python.dart`.

---

## H. Website-Agent Problems

1. **Missing Website Creation Infrastructure**:
   - No module exists to generate complete web projects (HTML5, CSS layout, JavaScript logic).
2. **No Preview / Server Capabilities**:
   - No local HTTP static server or automated browser launching to display generated websites.
3. **No Multi-File Scaffolding**:
   - No single-prompt to multi-file bundler (creating `index.html`, `styles.css`, `app.js` together in a dedicated output directory).

---

## I. Existing Features That Must NOT Be Broken

1. **Voice Session Lifecycle**: Wake word detection ("Jarvis"), active session loop, silence timeout (12s).
2. **Face Recognition (`vision/face_recognize.py`)**: DeepFace ArcFace camera capture, friend registration, identity greetings ("who is in front of me").
3. **Stock Analysis (`finance/stock_analyzer.py`)**: Technical analysis calculation for NSE/BSE stock symbols.
4. **Memory Layer (`memory/memory_manager.py`)**: 6 memory categories, policy secret filtering, `data/memory.json` persistence.
5. **Video Editing Bridge (`video_editing/`)**: Premiere Pro & CapCut CEP bridge commands.
6. **Computer Control (`tools/computer/`)**: Opening websites/apps (`open_app.py`), system monitoring (`monitor.py`).

---

## J. Recommended Architecture

```text
JARVIS AI ARCHITECTURE (REFINED)
│
├── main.py                          # Lightweight startup orchestrator
├── config.py                        # Central settings & multi-model registry
│
├── core/                            # System state machine & thread manager
│   ├── state_machine.py             # Single source of truth for UI/Voice states
│   └── performance_profiler.py      # Latency measurement
│
├── ai/                              # Centralized Multi-Model LLM Layer
│   ├── ai_response_manager.py       # Singleton Client with Multi-Model routing:
│   │                                  ├─ llama3.2 / phi4-mini -> Fast Chat & Intent Classification
│   │                                  └─ qwen3:4b-instruct  -> Coding & Website Generation
│   ├── ask_ollama.py                # Prompt assembly & sentence streaming
│   └── prompt.py                    # Structured system prompts
│
├── conversation/                    # Conversation Engine & Intelligence
│   ├── conversation_engine.py       # Main state loop (Fixed state transitions)
│   └── intelligence/                # Language, Intent & Response Validator
│
├── memory/                          # Memory Subsystem (Unchanged API)
│   └── memory_manager.py            # Central facade to data/memory.json
│
├── speech/                          # Speech Pipeline
│   ├── speech_coordinator.py        # Synchronized TTS playback & state lock
│   ├── listener_manager.py          # Optimized STT listening
│   └── speech_engine.py             # Natural Edge TTS voice generation
│
└── tools/                           # Tool & Execution Capabilities
    ├── router.py                    # Intelligent intent/tool router (replaces main.py if/elif)
    ├── coding/                      # Multi-Language Code Agent
    │   ├── code_assistant.py        # Refactored Code Assistant (Python, JS, Dart, etc.)
    │   └── executor.py              # Code verification & syntax checker
    └── website/                     # NEW: Website Creation Agent
        ├── site_builder.py          # HTML/CSS/JS generator (Qwen 4B powered)
        └── preview_server.py        # Local web preview launcher
```

---

## K. Exact Implementation Phases

### PHASE 1 — Conversation Reliability & Intent Routing
- **Files to Modify**:
  - `main.py`: Refactor `processCommand()` routing; remove aggressive `any(word in command for word in ["write", "create", ...])` keyword trap; route intents cleanly.
  - `speech/speech_coordinator.py`: Fix premature state transition to `WAITING_FOR_NEXT_COMMAND` in `speak_chunk()` and `speak()`. Transition only after audio queue is completely empty and speech session ended.
  - `speech/listener_manager.py`: Optimize ambient noise check to run once at startup or dynamically without forcing `0.5s` delay per turn.
  - `conversation/intelligence/language_analyzer.py` & `speech/speech_engine.py`: Fix Devanagari vs Romanized Hindi voice routing so EdgeTTS uses natural spoken Hinglish/Hindi without phonetic distortion.
  - `ai/ask_ollama.py`: Standardize prompt directives to guarantee 1-3 natural sentence conversational responses without formal textbook Hindi.
  - `finance/stock_search.py` & `tools/coding/code_assistant.py`: Standardize LLM calls through `AIResponseManager` singleton.
- **Files to Create**: None.
- **Responsibility**: Guarantee sub-2s voice conversation start, eliminate premature "Waiting for command" console logs, fix Hindi phrasing, and prevent misrouting of conversation queries.
- **Dependencies**: Existing `core/state_machine.py`, `speech/`, `ai/`.
- **Testing Method**: Run multi-turn voice tests (`tests/test_conversation_simulation.py` & interactive voice turns).
- **Success Criteria**:
  - Response starts speaking in < 2.5 seconds.
  - "Waiting for next command" ONLY prints after speech is 100% finished.
  - Conversational requests like "write a poem" or "create a joke" are handled conversationally without triggering Flutter Dart file generation.

---

### PHASE 2 — Multi-Language Coding Agent with Execution Verification
- **Files to Modify**:
  - `tools/coding/code_assistant.py`: Expand beyond Flutter. Support Python, JS, HTML, C++, Dart, Shell. Utilize `qwen3:4b-instruct` model via `AIResponseManager` for high-precision code output.
  - `tools/coding/project_scanner.py`: Extend scanner to recognize project types (Python, Node.js, Web, Flutter).
  - `main.py`: Explicitly route code generation requests ("write python script", "fix code in main.py") to `CodeAssistant`.
- **Files to Create**:
  - `tools/coding/executor.py`: Local execution & verification sandbox. Performs `python -m py_compile`, syntax checks, or test runs before declaring task completion.
- **Responsibility**: Generate syntactically valid code in multiple languages, verify code via execution/compilation check, and report true completion status.
- **Dependencies**: `ai/ai_response_manager.py` (`qwen3:4b-instruct` model), `tools/computer/file_manager.py`.
- **Testing Method**: Programmatically test `CodeAssistant.generate_and_verify()` with sample Python and JS tasks.
- **Success Criteria**:
  - Code generation uses `qwen3:4b-instruct`.
  - Generated code is automatically checked for syntax/compilation errors.
  - Jarvis only claims completion after successful verification.

---

### PHASE 3 — Autonomous Website Creation Agent
- **Files to Modify**:
  - `main.py`: Add routing for website creation commands (*"build a landing page for a coffee shop"*, *"create a portfolio website"*).
  - `config.py`: Add `WEBSITES_DIR = os.path.join(DATA_DIR, "websites")`.
- **Files to Create**:
  - `tools/website/site_builder.py`: Multi-file web app generator. Prompt `qwen3:4b-instruct` to produce modern, responsive HTML5, CSS3, and JavaScript files in a dedicated site folder.
  - `tools/website/preview_server.py`: Local static HTTP server launcher and browser opener (`http://localhost:8000/site_name`).
- **Responsibility**: Scaffolding complete, beautiful, single-page or multi-page websites based on voice prompts and immediately opening a live browser preview.
- **Dependencies**: `ai/ai_response_manager.py` (`qwen3:4b-instruct`), `tools/computer/file_manager.py`, Python `http.server` & `webbrowser`.
- **Testing Method**: Execute website creation command, verify HTML/CSS/JS files created in `data/websites/`, verify HTTP server launches and browser opens.
- **Success Criteria**:
  - Voice command *"build a portfolio website"* generates complete `index.html`, `style.css`, `script.js`.
  - Browser automatically opens live local preview.
  - Zero crashes, zero hallucinated completion.

---

## L. Summary of Files to Modify & Create

### Recommended Files to Modify:
1. `main.py`
2. `config.py`
3. `ai/ask_ollama.py`
4. `ai/ai_response_manager.py`
5. `speech/speech_coordinator.py`
6. `speech/listener_manager.py`
7. `speech/speech_engine.py`
8. `conversation/intelligence/language_analyzer.py`
9. `finance/stock_search.py`
10. `tools/coding/code_assistant.py`
11. `tools/coding/project_scanner.py`

### Recommended Files to Create:
1. `docs/JARVIS_AUDIT.md` (Created during audit)
2. `tools/coding/executor.py` (Phase 2)
3. `tools/website/__init__.py` (Phase 3)
4. `tools/website/site_builder.py` (Phase 3)
5. `tools/website/preview_server.py` (Phase 3)

---

## M. Final Audit Summary Metric

- **Files Analyzed**: 63 Python source files + config & schema files
- **Problems Found**: 18 specific issues
- **Critical Problems**: 7 critical blockers (Command routing trap, premature speech state transition, unverified code completion, missing website agent, hardcoded single model usage, duplicate Ollama clients, STT/TTS latency overhead)
- **Next Step**: Awaiting approval for **PHASE 1 — Conversation reliability**.
