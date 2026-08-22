import re
from config import MODEL_NAME
from conversation.conversation_manager import ConversationManager
from memory.memory_manager import MemoryManager
from conversation.intelligence.conversation_analyzer import ConversationAnalyzer
from ai.ai_response_manager import AIResponseManager
from core.performance_profiler import PerformanceProfiler

# ─── Debug flags ────────────────────────────────────────────────────────────
# Set DEBUG_PERFORMANCE = True in a dev session to print detailed performance tables.
DEBUG_PERFORMANCE = False
# Set ENABLE_LLM_DEBUG = True to print full prompts/messages to console.
ENABLE_LLM_DEBUG = False
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instances (module-level, shared across calls)
_conv_analyzer = None

def _get_conv_analyzer() -> ConversationAnalyzer:
    global _conv_analyzer
    if _conv_analyzer is None:
        _conv_analyzer = ConversationAnalyzer()
    return _conv_analyzer


from conversation.intelligence.response_validator import ResponseValidator

_validator = None

def _get_validator() -> ResponseValidator:
    global _validator
    if _validator is None:
        _validator = ResponseValidator()
    return _validator


def clean_response_for_tts(text: str) -> str:
    """
    Sanitizes response text before sending to TTS or persisting to history.
    Delegates to ResponseValidator for comprehensive cleanup.
    """
    return _get_validator().validate_and_clean(text)


def extract_target(user_input: str):
    """Detects if the user is switching the active conversational target."""
    text = user_input.lower()
    if "my friend" in text and "talk to you" in text:
        try:
            name_part = text.split("my friend")[1].split(",")[0].replace("talk to you", "").strip()
            return name_part.title(), "friend"
        except Exception:
            return None, None
    if "my boss" in text and "talk to you" in text:
        return "Boss", "boss"
    if "my sir" in text and "talk to you" in text:
        return "Sir", "sir"
    return None, None


def _build_pipeline(user_input: str, speaker_name: str, relation: str, profiler=None):
    """
    Shared pipeline for both streaming and blocking modes.
    Returns: (messages, intel, conv_manager)
    """
    conv_manager = ConversationManager()
    memory_manager = MemoryManager()

    # 1. Run Conversation Intelligence (local, pure regex — <1ms)
    if profiler:
        profiler.mark("CONV_ANALYSIS_START")
    conv_analyzer = _get_conv_analyzer()
    intel = conv_analyzer.analyze_input(user_input)
    if profiler:
        profiler.mark("CONV_ANALYSIS_END")

    if ENABLE_LLM_DEBUG:
        import json
        print("\n[CONVERSATION INTELLIGENCE]")
        print(json.dumps({k: intel.get(k) for k in (
            "intent", "emotion", "language", "language_style", "confidence", "topic",
            "requires_follow_up", "requires_clarification",
            "requires_suggestion", "response_style", "conversation_goal"
        )}, indent=2))

    # 2. Retrieve relevant memories (local JSON — <1ms, filtered with relevance threshold)
    if profiler:
        profiler.mark("MEMORY_RETRIEVAL_START")
    relevant_memories = memory_manager.retrieve_relevant(user_input, limit=3, min_score=1.0)
    if profiler:
        profiler.mark("MEMORY_RETRIEVAL_END")

    mem_lines = ""
    if relevant_memories:
        mem_lines = "\n".join(f"- {m.get('content')}" for m in relevant_memories)

    # 3. Build compact system prompt
    system_prompt = _build_system_prompt(speaker_name, relation, intel, mem_lines)

    if ENABLE_LLM_DEBUG:
        print(f"\n[SYSTEM PROMPT]\n{system_prompt}")

    # 4. Build messages list (history capped at MAX_HISTORY in ConversationManager)
    history = conv_manager.get_history_context()
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    return messages, intel, conv_manager


def _build_system_prompt(speaker_name: str, relation: str, intel: dict, mem_lines: str) -> str:
    """
    Compact, highly focused system prompt for Phase 1 Jarvis Response Quality Engine.
    Guides response style, personality, truthfulness, memory grounding, and length naturally.
    """
    emotion = intel.get("emotion", "neutral")
    action = intel.get("action_type", "answer_directly")
    topic = intel.get("topic", "")
    goal = intel.get("conversation_goal", "answer directly and concisely")
    instruction = intel.get("instruction", "")
    style = intel.get("response_style", "concise")
    lang_inst = intel.get("language_instruction", "Match user's spoken language naturally.")

    mem_section = f"\nRELEVANT MEMORIES:\n{mem_lines}" if mem_lines else "\nRELEVANT MEMORIES: NONE"

    return f"""You are Jarvis, a highly capable, warm, intelligent, confident, and natural AI assistant.
Owner: Manish (address him as "Boss" naturally when appropriate in Hinglish/English, but NEVER force "Boss" into every sentence).
Current user: {speaker_name} ({relation}).{mem_section}

CONTEXT DIRECTIVES:
Strategy: {action} | Topic: {topic} | Tone: {emotion} | Style: {style}
Goal: {goal}
Instruction: {instruction}
Language Directives: {lang_inst}

CONVERSATIONAL RULES:
- Tone & Personality: Sound like a smart, friendly, young personal assistant having a natural spoken conversation with Boss.
- Spoken Vocabulary: Preferred language is natural Hinglish / English. STRICTLY AVOID formal/unnatural textbook Hindi words: 'saamagri', 'nirdesh', 'upayukt', 'avashyakta', 'prastut', 'umeed hai', 'vikalp', 'sevan', 'parosein', 'samiksha', 'kripya', 'tadanusar', 'bhojan', 'nimnalikhit'. Prefer 'options', 'cheezein', 'steps', 'zarurat'.
- Tone Examples:
  * Bad: "Boss, aapko bhojan ki avashyakta hai."
  * Good: "Boss, bhookh lagi hai toh kuch kha le, Maggi ya sandwich bana lo."
  * Bad: "Is recipe ke liye nimnalikhit saamagri ki aavashyakta hogi."
  * Good: "Bilkul Boss! Ek packet Maggi ke liye 1.5 cup paani garam karo, masala dalo aur 2 minute mein tayar."
- Length Control: For simple questions / chat / recipes -> 1 to 3 short spoken sentences ONLY.
- Formatting: Output CLEAN SPOKEN SPEECH ONLY. NO markdown headings (#), NO numbered lists (1. 2. 3.), NO bullet points (* -), NO code blocks, NO "Jarvis:" prefixes.
- Disagreement & Reasoning: Respectfully express opinion with clear reasoning when asked.
- Avoid Repetitive Fillers: Never start with "Certainly Boss", "Of course Boss", "As an AI model...", or canned greetings.
- Memory Grounding & Anti-Hallucination:
  * If RELEVANT MEMORIES contains stored facts (e.g. "My current project is Jarvis AI"), ALWAYS USE THOSE FACTS TO ANSWER DIRECTLY (e.g. "Boss, aapka current project Jarvis AI hai.").
  * ONLY if RELEVANT MEMORIES is NONE or does not contain the answer for a personal question, state clearly: "Boss, mere paas iski information nahi hai."
  * NEVER fabricate fake people, fake projects, or fake events."""




# ─── Public API ──────────────────────────────────────────────────────────────

def ask_ollama_streaming(user_input: str, speaker_name: str, relation: str, speak_callback=None) -> str:
    """
    STREAMING pipeline. Dispatches sentences to SpeechCoordinator as they arrive
    from Ollama, so TTS begins on the FIRST SENTENCE.

    Manages speech session state to prevent premature WAITING_FOR_NEXT_COMMAND state transitions.

    Returns the complete response text for history persistence.
    """
    PerformanceProfiler.reset()
    PerformanceProfiler.mark("PIPELINE_START")

    conv_manager = ConversationManager()

    # Check for target switching
    target_name, target_relation = extract_target(user_input)
    if target_name:
        conv_manager.switch_to_guest(target_name, target_relation)
        response = f"Hello {target_name}, how can I help you?"
        if speak_callback:
            speak_callback(response)
        return response

    # Acquire speech coordinator for state lock
    speech_coordinator = None
    try:
        from conversation.conversation_engine import ConversationEngine
        engine = ConversationEngine()
        if engine and hasattr(engine, "speech_coordinator"):
            speech_coordinator = engine.speech_coordinator
            speech_coordinator.begin_speech_session()
    except Exception:
        pass

    PerformanceProfiler.mark("THINKING_STATE_SET")

    # Build pipeline
    messages, intel, conv_manager = _build_pipeline(
        user_input, speaker_name, relation, profiler=PerformanceProfiler
    )

    def _sentence_dispatcher(sentence: str):
        cleaned_chunk = clean_response_for_tts(sentence)
        if not cleaned_chunk:
            return
        if speech_coordinator:
            speech_coordinator.speak_chunk(cleaned_chunk, wait=True)
        elif speak_callback:
            speak_callback(cleaned_chunk)

    PerformanceProfiler.mark("OLLAMA_REQUEST_START")
    ai_manager = AIResponseManager()

    try:
        raw_response = ai_manager.generate_response_streaming(
            messages=messages,
            sentence_callback=_sentence_dispatcher,
            perf_profiler=PerformanceProfiler,
            debug_perf=DEBUG_PERFORMANCE,
            keep_alive=-1
        )
        full_response = clean_response_for_tts(raw_response)
    except Exception as e:
        print(f"[Ollama Streaming Error]: {e}")
        err = "I'm having trouble thinking right now, Boss. Check if Ollama is running."
        if speech_coordinator:
            speech_coordinator.speak_chunk(err, wait=True)
        elif speak_callback:
            speak_callback(err)
        full_response = err
    finally:
        if speech_coordinator:
            speech_coordinator.end_speech_session()

    PerformanceProfiler.mark("PIPELINE_END")
    if DEBUG_PERFORMANCE:
        PerformanceProfiler.report()

    # Persist history after full response is available
    conv_manager.add_to_history("user", user_input)
    conv_manager.add_to_history("assistant", full_response)

    return full_response


def ask_ollama(user_input: str, speaker_name: str, relation: str) -> str:
    """
    Blocking (non-streaming) pipeline. Returns full response as a string.
    Used by code assistant, tests, and non-conversational callers.
    """
    PerformanceProfiler.reset()
    PerformanceProfiler.mark("PIPELINE_START")

    conv_manager = ConversationManager()

    target_name, target_relation = extract_target(user_input)
    if target_name:
        conv_manager.switch_to_guest(target_name, target_relation)
        return f"Hello {target_name}, how can I assist you today?"

    messages, intel, conv_manager = _build_pipeline(
        user_input, speaker_name, relation, profiler=PerformanceProfiler
    )

    PerformanceProfiler.mark("OLLAMA_REQUEST_START")
    ai_manager = AIResponseManager()

    try:
        ai_response = ai_manager.generate_response(messages, keep_alive=-1)
        ai_response = clean_response_for_tts(ai_response)
        PerformanceProfiler.mark("OLLAMA_COMPLETE")
    except Exception as e:
        print(f"[Ollama Error]: {e}")
        return "I'm having trouble thinking clearly right now, Boss. Maybe check if the Ollama service is running?"

    PerformanceProfiler.mark("PIPELINE_END")
    if DEBUG_PERFORMANCE:
        PerformanceProfiler.report()

    conv_manager.add_to_history("user", user_input)
    conv_manager.add_to_history("assistant", ai_response)

    return ai_response
