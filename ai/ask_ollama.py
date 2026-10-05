import re
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
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


def strip_emojis_only(text: str) -> str:
    """
    Strips only emojis (for TTS), preserving all other content.
    Used to generate TTS-clean text while keeping display text with emoji intact.
    """
    return _get_validator().strip_emojis_for_tts(text)


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

    # 0. Follow-up pronoun resolution & context lifecycle update
    resolved_info = conv_manager.process_and_resolve_input(user_input)
    effective_user_input = resolved_info.get("resolved_text", user_input)

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
    relevant_memories = memory_manager.retrieve_relevant(user_input, limit=3, min_score=0.5)
    if profiler:
        profiler.mark("MEMORY_RETRIEVAL_END")

    mem_lines = ""
    if relevant_memories:
        mem_lines = "\n".join(f"- {m.get('content')}" for m in relevant_memories)

    active_ctx_str = ""
    if conv_manager.active_entity:
        active_ctx_str = f"\nActive Context: User is talking about '{conv_manager.active_entity}'."

    # 3. Build compact system prompt
    system_prompt = _build_system_prompt(speaker_name, relation, intel, mem_lines, active_ctx_str)

    # 4. Build messages list with context relevance filtering
    history = conv_manager.get_history_context(current_query=user_input)
    if len(history) > 4:
        history = history[-4:]
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": effective_user_input})

    print(
        f"[PROMPT_TELEMETRY] prompt_chars={len(system_prompt)} "
        f"history_messages={len(history)} "
        f"memory_count={len(relevant_memories)} "
        f"has_active_context={bool(conv_manager.active_entity)}",
        flush=True
    )

    if ENABLE_LLM_DEBUG:
        print(f"\n[SYSTEM PROMPT]\n{system_prompt}")

    return messages, intel, conv_manager


from datetime import datetime

def _build_system_prompt(speaker_name: str, relation: str, intel: dict, mem_lines: str, active_ctx_str: str = "") -> str:
    """
    Adaptive system prompt. Language (English/Hinglish) is selected DETERMINISTICALLY
    from the current user utterance via intel["language"] — NOT from context history.
    Grammar directives enforce correct female self-reference.
    """
    now = datetime.now()
    current_time_str = now.strftime("%B %d, %Y (%A) %I:%M %p IST")
    mem_section = f"\nMemories: {mem_lines}" if mem_lines else ""

    # ── Deterministic language selection from current turn ─────────────────
    detected_lang = (intel or {}).get("language", "english")
    lang_instruction = (intel or {}).get("language_instruction", "")

    if detected_lang == "hinglish":
        language_directive = (
            f"LANGUAGE: User is speaking Hinglish (Roman Hindi + English mix). "
            f"Respond naturally in casual spoken Hinglish matching the user's tone. "
            f"{lang_instruction} "
            f"Example good: 'Samajh gayi Boss.' / 'Main theek hoon, aap batao.' / 'Chalo aaj thoda relax karte hain.'"
        )
    elif detected_lang == "hindi":
        language_directive = (
            f"LANGUAGE: User is speaking Hindi. "
            f"Respond in natural spoken Hindi. Use simple, daily Hindi — NOT formal Sanskritized words. "
            f"{lang_instruction}"
        )
    else:  # english (default)
        language_directive = (
            f"LANGUAGE: User is speaking English. "
            f"Respond in clean, friendly, natural conversational English. "
            f"{lang_instruction} "
            f"Example good: 'Sure Boss!' / 'Python is a high-level programming language known for its simple syntax.' "
            f"Do NOT mix Hindi/Hinglish words into an English response."
        )

    return (
        f"You are Jarvis, a warm, intelligent female AI assistant for Manish (Boss).\n"
        f"User: {speaker_name} ({relation}).{mem_section}{active_ctx_str}\n"
        f"System Time: {current_time_str}.\n"
        f"{language_directive}\n"
        f"FEMALE GRAMMAR: Always use correct female self-referential forms: "
        f"'Main theek hoon' (NOT 'theek hoon main'), 'Samajh gayi' (NOT 'samajh gaya'), "
        f"'Main dekh rahi hoon' (NOT 'dekh raha hoon'), 'Main karungi' (NOT 'karunga'). "
        f"Never use male forms like 'lagta hoon', 'sambhalne wale', 'sundar lagta hoon'.\n"
        f"CASUAL CHAT: For greetings, compliments, or small talk — reply warmly in 1-2 sentences, like a friend. "
        f"NEVER end with: 'Kya karna hai ab?', 'Main ready hoon', 'Kya kaam hai', 'Kuch kaam?' unless user explicitly asked for help. "
        f"Example: USER='thank you' → JARVIS='Anytime Boss.' NOT 'Anytime Boss. Kya karna hai ab?'\n"
        f"CLEAN SPOKEN SPEECH ONLY: No markdown, no bullet points, no numbered lists, no code blocks, no 'Jarvis:' prefix. "
        f"Output ONLY the spoken response text."
    )





# ─── Public API ──────────────────────────────────────────────────────────────

import threading
import time
_active_request_ids = set()
_active_req_lock = threading.Lock()

# Per-request TTS duration accumulator (thread-safe, for real telemetry)
_tts_duration_accum: dict = {}  # req_id -> list[float]
_tts_accum_lock = threading.Lock()

def _record_tts_duration(req_id: str, duration_ms: float):
    """Thread-safe accumulator for async TTS generation durations."""
    with _tts_accum_lock:
        if req_id not in _tts_duration_accum:
            _tts_duration_accum[req_id] = []
        _tts_duration_accum[req_id].append(duration_ms)

def _get_tts_total_ms(req_id: str) -> float:
    """Returns total TTS generation ms accumulated for this request, then clears it."""
    with _tts_accum_lock:
        vals = _tts_duration_accum.pop(req_id, [])
    return sum(vals) if vals else 0.0

def ask_ollama_streaming(user_input: str, speaker_name: str, relation: str, speak_callback=None, speech_coordinator=None, request_id: str = None) -> str:
    """
    STREAMING pipeline. Dispatches sentences to SpeechCoordinator as they arrive
    from Ollama, so TTS begins on the FIRST SENTENCE.

    Uses CONVERSATION_OPTIONS and think=False for qwen3:8b. Includes detailed timing telemetry.
    """
    import uuid
    import time
    pipeline_start_t = time.perf_counter()
    req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"

    with _active_req_lock:
        if req_id in _active_request_ids:
            print(f"[CONVERSATION_DUPLICATE_REQUEST]\nrequest_id={req_id}\naction=IGNORED", flush=True)
            return ""
        _active_request_ids.add(req_id)

    try:
        print(f"[RESPONSE_STREAM_START] request_id={req_id}", flush=True)
        print(f"[VOICE_PIPELINE]\nrequest_id={req_id}", flush=True)
        print(f"[ASR_COMPLETE]\nrequest_id={req_id}\nduration_ms=0.0", flush=True)
        print(f"[LLM_START]\nrequest_id={req_id}", flush=True)
        print(f"[LLM_REQUEST]\nrequest_id={req_id}\nattempt=1", flush=True)
        print(f"[LLM_REQUEST_START]\nrequest_id={req_id}", flush=True)

        PerformanceProfiler.reset(request_id=req_id)
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
        if speech_coordinator is None:
            try:
                from conversation.conversation_engine import ConversationEngine
                engine = ConversationEngine()
                if engine and hasattr(engine, "speech_coordinator"):
                    speech_coordinator = engine.speech_coordinator
            except Exception:
                pass

        if speech_coordinator:
            speech_coordinator.begin_speech_session()

        PerformanceProfiler.mark("THINKING_STATE_SET")

        # Build pipeline and measure memory retrieval timing
        mem_start_t = time.perf_counter()
        messages, intel, conv_manager = _build_pipeline(
            user_input, speaker_name, relation, profiler=PerformanceProfiler
        )
        memory_ms = (time.perf_counter() - mem_start_t) * 1000.0

        first_token_time_ref = [None]
        _first_chunk_marked = [False]
        _chunk_count = [0]
        _delivered_sentences = []

        def _sentence_dispatcher(sentence: str):
            from speech.voice_session_manager import VoiceSessionManager
            vsm = VoiceSessionManager.get_instance()
            if vsm.is_request_invalidated(req_id):
                active_id = vsm.get_active_request_id()
                print(f"[STALE_CHUNK_DROPPED] request_id={req_id} active_request_id={active_id} sentence=\"{sentence[:30]}\"", flush=True)
                return

            if first_token_time_ref[0] is None:
                first_token_time_ref[0] = time.perf_counter()
                first_token_latency_ms = (first_token_time_ref[0] - ollama_start_t) * 1000.0
                print(f"[LLM_FIRST_TOKEN]\nrequest_id={req_id}\nlatency_ms={first_token_latency_ms:.1f}", flush=True)
                print(f"[FIRST_TOKEN_READY] request_id={req_id} latency_ms={first_token_latency_ms:.1f}", flush=True)
            # Strip only emojis for TTS; keep original sentence for UI display
            tts_text = clean_response_for_tts(sentence)
            display_text = sentence.strip()  # Original sentence — emoji preserved for UI
            if not tts_text:
                return
            _chunk_count[0] += 1
            _delivered_sentences.append(display_text)
            c_id = f"chunk_{_chunk_count[0]}"
            print(f"[RESPONSE_CHUNK] request_id={req_id} chunk={_chunk_count[0]} chunk_id={c_id}", flush=True)
            print(f"[TTS_SENTENCE_DISPATCH] request_id={req_id} sentence_id={_chunk_count[0]} chunk_id={c_id} chars={len(tts_text)}", flush=True)
            if not _first_chunk_marked[0]:
                PerformanceProfiler.mark("FIRST_SPEAKABLE_SENTENCE")
                _first_chunk_marked[0] = True
            if speak_callback:
                speak_callback(tts_text)
            if speech_coordinator:
                print(f"[STREAM_DEBUG] speech_coordinator_called request_id={req_id} chunk_id={c_id} text=\"{tts_text[:40]}\"", flush=True)
                # Pass both display_text (for UI, with emoji) and tts_text (for TTS, emoji-stripped)
                speech_coordinator.speak_chunk(
                    tts_text,
                    wait=False,
                    request_id=req_id,
                    chunk_id=c_id,
                    display_text=display_text,
                    tts_duration_callback=lambda ms: _record_tts_duration(req_id, ms)
                )

        PerformanceProfiler.mark("OLLAMA_REQUEST_START")
        ai_manager = AIResponseManager()
        from ai.ai_response_manager import CONVERSATION_OPTIONS, MODEL_NAME, LLMTimeoutException

        print(f"[CONVERSATION_LLM_START]\nrequest_id={req_id}\nmodel={MODEL_NAME}\nthink=False", flush=True)
        ollama_start_t = time.perf_counter()

        full_response = ""
        try:
            raw_response = ai_manager.generate_response_streaming(
                messages=messages,
                sentence_callback=_sentence_dispatcher,
                perf_profiler=PerformanceProfiler,
                debug_perf=DEBUG_PERFORMANCE,
                keep_alive=-1,
                options=CONVERSATION_OPTIONS,
                think=False,
                timeout=60.0,
                request_id=req_id
            )
            parse_start_t = time.perf_counter()
            full_response = clean_response_for_tts(raw_response)
            response_parse_ms = (time.perf_counter() - parse_start_t) * 1000.0

            # 1-retry mechanism if sanitized response is empty and no chunks were delivered
            if not full_response.strip() and _chunk_count[0] == 0:
                print("[CONVERSATION_EMPTY_RESPONSE] Output empty after sanitization. Retrying (max 1 retry)...", flush=True)
                print(f"[LLM_REQUEST]\nrequest_id={req_id}\nattempt=2", flush=True)
                raw_response_retry = ai_manager.generate_response_streaming(
                    messages=messages,
                    sentence_callback=_sentence_dispatcher,
                    perf_profiler=PerformanceProfiler,
                    debug_perf=DEBUG_PERFORMANCE,
                    keep_alive=-1,
                    options=CONVERSATION_OPTIONS,
                    think=False,
                    timeout=60.0,
                    request_id=req_id
                )
                full_response = clean_response_for_tts(raw_response_retry)

                if not full_response.strip() and _chunk_count[0] == 0:
                    print("[CONVERSATION_EMPTY_RESPONSE] Retry produced empty response. Using deterministic fallback.", flush=True)
                    full_response = "Sorry Boss, response generate karte waqt issue aa gaya."

            if not full_response.strip() and _delivered_sentences:
                full_response = " ".join(_delivered_sentences)

            ollama_dur_ms = (time.perf_counter() - ollama_start_t) * 1000.0
            llm_first_token_ms = ((first_token_time_ref[0] - ollama_start_t) * 1000.0) if first_token_time_ref[0] else ollama_dur_ms

            print(f"[RESPONSE_STREAM_COMPLETE] request_id={req_id}", flush=True)
            print(f"[LLM_STREAM_END]\nrequest_id={req_id}\ntotal_ms={ollama_dur_ms:.1f}", flush=True)
            print(f"[LLM_RESPONSE_READY]\nrequest_id={req_id}", flush=True)
            print(f"[LLM_COMPLETE]\nrequest_id={req_id}\nduration_ms={ollama_dur_ms:.1f}", flush=True)
            print(f"[CONVERSATION_LLM_COMPLETE]\nrequest_id={req_id}\nmodel={MODEL_NAME}\nduration_ms={ollama_dur_ms:.1f}", flush=True)
            print(f"[CONVERSATION_SUCCESS] model={MODEL_NAME} response_len={len(full_response)}", flush=True)

            if full_response.strip():
                if speech_coordinator:
                    if _chunk_count[0] == 0:
                        speech_coordinator.speak(full_response, wait=True, request_id=req_id)
                elif speak_callback and _chunk_count[0] == 0:
                    speak_callback(full_response)

        except LLMTimeoutException:
            ollama_dur_ms = (time.perf_counter() - ollama_start_t) * 1000.0
            llm_first_token_ms = ollama_dur_ms
            response_parse_ms = 0.0
            print(f"[RESPONSE_STREAM_COMPLETE] request_id={req_id}", flush=True)
            print(f"[CONVERSATION_LLM_TIMEOUT]\nrequest_id={req_id}\nmodel={MODEL_NAME}\ntimeout_seconds=60.0", flush=True)
            if _chunk_count[0] > 0 and _delivered_sentences:
                full_response = " ".join(_delivered_sentences)
                print(f"[RESPONSE_STREAM_PARTIAL_SUCCESS] request_id={req_id} chunks={_chunk_count[0]} reason=llm_timeout_after_delivered_chunks", flush=True)
            else:
                fallback = "I'm listening, Boss. How can I help?"
                full_response = fallback
                if speech_coordinator and _chunk_count[0] == 0:
                    speech_coordinator.speak(fallback, wait=True, request_id=req_id)
                elif speak_callback and _chunk_count[0] == 0:
                    speak_callback(fallback)

        except Exception as e:
            ollama_dur_ms = (time.perf_counter() - ollama_start_t) * 1000.0
            llm_first_token_ms = ollama_dur_ms
            response_parse_ms = 0.0
            print(f"[RESPONSE_STREAM_COMPLETE] request_id={req_id}", flush=True)
            print(f"[CONVERSATION_LLM_ERROR]\nrequest_id={req_id}\nmodel={MODEL_NAME}\nerror={e}", flush=True)
            if _chunk_count[0] > 0 and _delivered_sentences:
                full_response = " ".join(_delivered_sentences)
                print(f"[RESPONSE_STREAM_PARTIAL_SUCCESS] request_id={req_id} chunks={_chunk_count[0]} reason=exception_after_delivered_chunks error={e}", flush=True)
            else:
                err = "I'm having trouble thinking right now, Boss. Check if Ollama is running."
                full_response = err
                if speech_coordinator and _chunk_count[0] == 0:
                    speech_coordinator.speak(err, wait=True, request_id=req_id)
                elif speak_callback and _chunk_count[0] == 0:
                    speak_callback(err)
        finally:
            if speech_coordinator:
                speech_coordinator.end_speech_session()

        total_ms = (time.perf_counter() - pipeline_start_t) * 1000.0
        # Collect real TTS generation durations from async workers (accumulated during streaming)
        # Note: TTS workers may still be running; this captures completed sentences only.
        tts_generation_ms = _get_tts_total_ms(req_id)
        tts_queue_ms = 0.0  # Queue wait is internal to ThreadPoolExecutor — not measurable from here

        print(
            f"[CONVERSATION_TIMING]\n"
            f"request_id={req_id}\n"
            f"memory_ms={memory_ms:.1f}\n"
            f"llm_start=0.0\n"
            f"llm_first_token_ms={llm_first_token_ms:.1f}\n"
            f"llm_total_ms={ollama_dur_ms:.1f}\n"
            f"response_parse_ms={response_parse_ms:.1f}\n"
            f"tts_generation_ms={tts_generation_ms:.1f} (async_completed_sentences)\n"
            f"tts_queue_ms={tts_queue_ms:.1f}\n"
            f"total_ms={total_ms:.1f}",
            flush=True
        )
        print(f"[VOICE_PIPELINE_COMPLETE]\nrequest_id={req_id}\ntotal_ms={total_ms:.1f}", flush=True)
        print(f"[FULL_RESPONSE_COMPLETE] request_id={req_id} total_ms={total_ms:.1f}", flush=True)

        PerformanceProfiler.mark("PIPELINE_END")
        if DEBUG_PERFORMANCE:
            PerformanceProfiler.report()

        # Persist history after full response is available
        conv_manager.add_to_history("user", user_input)
        conv_manager.add_to_history("assistant", full_response)

        return full_response

    finally:
        with _active_req_lock:
            _active_request_ids.discard(req_id)


def ask_ollama(user_input: str, speaker_name: str, relation: str) -> str:
    """
    Blocking (non-streaming) pipeline. Returns full response as a string.
    Uses CONVERSATION_OPTIONS and think=False for qwen3:8b. Includes 1-retry fallback for empty output.
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
    from ai.ai_response_manager import CONVERSATION_OPTIONS, MODEL_NAME

    print(f"[CONVERSATION_LLM_START] model={MODEL_NAME} think=False", flush=True)

    try:
        ai_response = ai_manager.generate_response(
            messages,
            keep_alive=-1,
            options=CONVERSATION_OPTIONS,
            think=False
        )
        cleaned_response = clean_response_for_tts(ai_response)

        # 1-retry mechanism if sanitized response is empty
        if not cleaned_response.strip():
            print("[CONVERSATION_EMPTY_RESPONSE] Output empty after sanitization. Retrying (max 1 retry)...", flush=True)
            print("[CONVERSATION_RETRY] Executing retry turn...", flush=True)
            ai_response_retry = ai_manager.generate_response(
                messages,
                keep_alive=-1,
                options=CONVERSATION_OPTIONS,
                think=False
            )
            cleaned_response = clean_response_for_tts(ai_response_retry)

            if not cleaned_response.strip():
                print("[CONVERSATION_EMPTY_RESPONSE] Retry produced empty response. Using deterministic fallback.", flush=True)
                cleaned_response = "Sorry Boss, response generate karte waqt issue aa gaya. Ek baar phir bolna."

        PerformanceProfiler.mark("OLLAMA_COMPLETE")
        print(f"[CONVERSATION_SUCCESS] model={MODEL_NAME} response_len={len(cleaned_response)}", flush=True)
    except Exception as e:
        print(f"[Ollama Error]: {e}", flush=True)
        return "I'm having trouble thinking clearly right now, Boss. Maybe check if the Ollama service is running?"

    PerformanceProfiler.mark("PIPELINE_END")
    if DEBUG_PERFORMANCE:
        PerformanceProfiler.report()

    conv_manager.add_to_history("user", user_input)
    conv_manager.add_to_history("assistant", cleaned_response)

    return cleaned_response

