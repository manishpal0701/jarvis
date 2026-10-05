"""
speech/speech_coordinator.py
Thread-safe speech coordinator. Manages audio playback locks and state machine
transitions for both single-shot and streaming multi-chunk response sessions.

CRITICAL DESIGN:
- speak_chunk() MUST NOT block the calling thread (Ollama streaming loop).
- TTS generation is dispatched to a background ThreadPoolExecutor.
- QueueManager handles sequential playback (already ordered by enqueue order).
- sentence_id tracking ensures FIRST_SENTENCE_READY fires only once per request.
"""
import speech
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable
from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager
from speech.voice_state_machine import VoiceState

class SpeechCoordinator:
    def __init__(self, state_machine: StateMachine, timeout_manager: TimeoutManager):
        self.state_machine = state_machine
        self.timeout_manager = timeout_manager
        self._lock = threading.Lock()
        self._session_active = False
        self._last_speech_end_time = 0.0
        self._dispatched_responses = set()
        self._dispatched_texts: dict[str, float] = {}
        self._request_dispatch_counts: dict[str, int] = {}

        # --- Async TTS dispatch pool (2 workers: one generating while one plays) ---
        # Using 2 workers so sentence N+1 TTS can generate while sentence N plays.
        # QueueManager ensures playback order is preserved regardless of generation order.
        self._tts_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tts_worker")

        # Per-request first-sentence tracking (for correct telemetry)
        self._first_sentence_dispatched: set[str] = set()

    def begin_speech_session(self):
        """Signals the start of a streaming or multi-sentence response session."""
        with self._lock:
            self._session_active = True
            self.state_machine.transition_to(State.THINKING)
            self.timeout_manager.reset()

    def speak_chunk(self, text: str, wait: bool = False, request_id: Optional[str] = None, chunk_id: Optional[str] = None, stream_id: Optional[str] = None, display_text: Optional[str] = None, tts_duration_callback: Optional[Callable[[float], None]] = None):
        """
        Speaks a single sentence/chunk during an active session.

        ARCHITECTURE:
        - Runs deduplication and ID assignment synchronously (fast, under lock).
        - TTS generation (EdgeTTS network call, 2-15s) is dispatched to background thread pool.
        - Returns IMMEDIATELY to allow Ollama streaming loop to continue consuming tokens.
        - QueueManager handles sequential playback automatically.
        - display_text: original text with emoji (for UI chat bubble). Falls back to text if not provided.
        - tts_duration_callback: called with real TTS generation ms for telemetry accumulation.

        This design eliminates the TTS-blocking-Ollama bug.
        """
        if not text or not text.strip():
            return

        with self._lock:
            self._session_active = True
            self.state_machine.transition_to(State.SPEAKING)
            self.timeout_manager.reset()

            clean_t = text.strip()
            try:
                print(f"Jarvis: {clean_t}", flush=True)
            except Exception:
                pass

            # --- Deduplication by text content (3s window) ---
            now = time.time()
            stale_texts = [k for k, t in list(self._dispatched_texts.items()) if now - t > 10.0]
            for k in stale_texts:
                self._dispatched_texts.pop(k, None)

            if clean_t in self._dispatched_texts and (now - self._dispatched_texts[clean_t]) < 3.0:
                print(f"[TTS_DUPLICATE_BLOCKED]\ntext={clean_t[:30]}\nreason=duplicate_text_window", flush=True)
                return
            self._dispatched_texts[clean_t] = now

            import os
            import uuid
            from datetime import datetime
            from speech.voice_session_manager import VoiceSessionManager
            vsm = VoiceSessionManager.get_instance()

            req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"
            count = self._request_dispatch_counts.get(req_id, 0) + 1
            c_id = chunk_id or f"chunk_{count}"
            speech_id = f"speech_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.now().isoformat()

            # --- Correct sentence telemetry (Part 7/8) ---
            is_first_sentence = req_id not in self._first_sentence_dispatched
            if is_first_sentence:
                self._first_sentence_dispatched.add(req_id)
                print(f"[FIRST_SENTENCE_READY] request_id={req_id} text=\"{clean_t[:40]}\"", flush=True)
            else:
                print(f"[SENTENCE_READY] request_id={req_id} sentence_id={count} text=\"{clean_t[:40]}\"", flush=True)

            # --- Stale request check ---
            if vsm.is_request_invalidated(req_id):
                print(f"[TTS_STALE_BLOCKED] request_id={req_id} reason=request_interrupted", flush=True)
                return
            vsm.mark_speaking_started(req_id, speech_id=speech_id)

            # --- Deduplication by chunk key ---
            chunk_key = f"{req_id}:{c_id}"
            if chunk_key in self._dispatched_responses:
                print(f"[TTS_DUPLICATE_BLOCKED]\nchunk_key={chunk_key}\nrequest_id={req_id}\nreason=duplicate_chunk_id", flush=True)
                return
            if len(self._dispatched_responses) > 200:
                self._dispatched_responses.clear()
            self._dispatched_responses.add(chunk_key)

            self._request_dispatch_counts[req_id] = count

            # display_text: original text with emoji for UI; falls back to tts_text if not provided
            display_clean = (display_text or clean_t).strip()

            print(f"[CONVERSATION_RESPONSE]\nrequest_id={req_id}\nresponse_id={speech_id}\nsentence_id={count}\ntext={clean_t}", flush=True)
            print(f"[CONVERSATION_DISPATCH]\nrequest_id={req_id}\nresponse_id={speech_id}\nsentence_id={count}", flush=True)
            print(f"[TTS_DISPATCH] request_id={req_id} sentence_id={count} chunk_id={c_id}", flush=True)
            print(f"[STREAM_DEBUG] tts_async_dispatch request_id={req_id} speech_id={speech_id} sentence_id={count}", flush=True)

        # ─── ASYNC TTS GENERATION — dispatched off the calling thread ─────────
        # The Ollama streaming loop continues immediately while this runs in background.
        def _generate_and_enqueue():
            tts_gen_start = time.perf_counter()
            try:
                print(f"[TTS_AUDIO_GENERATION_START] request_id={req_id} speech_id={speech_id} sentence_id={count}", flush=True)

                # Re-check staleness before generating (request may have been interrupted)
                from speech.voice_session_manager import VoiceSessionManager as _VSM
                if _VSM.get_instance().is_request_invalidated(req_id):
                    print(f"[TTS_STALE_BLOCKED] request_id={req_id} speech_id={speech_id} reason=invalidated_before_generation", flush=True)
                    return

                audio_path = speech.speak(clean_t, wait=False, speech_id=speech_id, request_id=req_id)
                tts_dur_ms = (time.perf_counter() - tts_gen_start) * 1000.0

                print(f"[TTS_AUDIO_GENERATION_END] request_id={req_id} speech_id={speech_id} sentence_id={count} duration_ms={tts_dur_ms:.1f}", flush=True)

                # Correct first-TTS telemetry (Part 7)
                if is_first_sentence:
                    print(f"[FIRST_TTS_READY] request_id={req_id} speech_id={speech_id} duration_ms={tts_dur_ms:.1f}", flush=True)
                else:
                    print(f"[TTS_READY] request_id={req_id} speech_id={speech_id} sentence_id={count} duration_ms={tts_dur_ms:.1f}", flush=True)

                print(f"[STREAM_DEBUG] tts_generation_complete request_id={req_id} speech_id={speech_id} audio_path={audio_path}", flush=True)

                import os as _os
                owner = _os.getenv("PLAYBACK_OWNER", "FRONTEND").upper()

                print(f"[TTS_READY]\nrequest_id={req_id}\nspeech_id={speech_id}\nsentence_id={count}\nduration_ms={tts_dur_ms:.1f}", flush=True)
                print(f"[AUDIO_PLAYBACK_OWNER]\nowner={owner}", flush=True)
                print(f"[VOICE_PLAYBACK_OWNER]\nowner={owner}", flush=True)

                audio_url = ""
                if audio_path:
                    filename = _os.path.basename(audio_path)
                    audio_url = f"http://localhost:8000/speech/cache/{filename}"

                # Report real TTS generation duration back to ask_ollama telemetry accumulator
                if tts_duration_callback:
                    try:
                        tts_duration_callback(tts_dur_ms)
                    except Exception:
                        pass

                print(f"[TTS_QUEUE_ENQUEUE] request_id={req_id} speech_id={speech_id} sentence_id={count}", flush=True)

                if is_first_sentence:
                    print(f"[FIRST_AUDIO_PLAYBACK_START] request_id={req_id} speech_id={speech_id} audio_url={audio_url}", flush=True)
                else:
                    print(f"[SUBSEQUENT_AUDIO_PLAYBACK_START] request_id={req_id} speech_id={speech_id} sentence_id={count} audio_url={audio_url}", flush=True)

                print(f"[WS_TX] event=speaking_start speech_id={speech_id} sentence_id={count} text={clean_t[:40]} audio_url={audio_url}", flush=True)
                try:
                    from api.websocket.jarvis import broadcast_sync
                    from datetime import datetime as _dt
                    broadcast_sync({
                        "type": "speaking_start",
                        "text": clean_t,          # TTS-clean text (no emoji) — used by audio pipeline
                        "text_display": display_clean,  # Original text with emoji — used by UI chat bubble
                        "timestamp": timestamp,
                        "request_id": req_id,
                        "speech_id": speech_id,
                        "sentence_id": count,
                        "audio_url": audio_url,
                        "playback_owner": owner,
                        "owner": owner
                    })
                    print(f"[STREAM_DEBUG] websocket_speaking_start_sent speech_id={speech_id}", flush=True)
                except Exception:
                    pass

            except Exception as tts_err:
                print(f"[TTS_GENERATION_ERROR] request_id={req_id} speech_id={speech_id} error={type(tts_err).__name__}", flush=True)

        # Submit to background thread pool — returns immediately if wait=False
        fut = self._tts_executor.submit(_generate_and_enqueue)
        self.timeout_manager.reset()
        self._last_speech_end_time = time.time()

        if wait:
            try:
                fut.result(timeout=5.0)
            except Exception:
                pass

        # speaking_end is now sent after audio plays, not immediately after TTS generation
        # The frontend receives speaking_start when TTS is ready; speaking_end from the audio queue
        # (handled by QueueManager/AudioEngine)

    def interrupt_speech(self, reason: str = "user_barge_in", request_id: Optional[str] = None):
        """
        Signals real-time voice interruption / barge-in.
        Immediately stops active playback, flushes QueueManager, broadcasts speaking_interrupted event,
        and invalidates stale request IDs.
        """
        with self._lock:
            self._session_active = False
            from datetime import datetime
            from speech.voice_session_manager import VoiceSessionManager
            vsm = VoiceSessionManager.get_instance()
            active_session = vsm.get_active_context() if hasattr(vsm, "get_active_context") else vsm.get_active_session()

            req_id = request_id or (active_session.request_id if active_session else "active_req")
            speech_id = active_session.current_audio_id if active_session else "speech_active"
            session_id = active_session.session_id if active_session else "session_active"

            vsm.invalidate_request(req_id, reason=reason)
            vsm.state_machine.transition_to(VoiceState.INTERRUPTED, reason=reason)
            vsm.state_machine.transition_to(VoiceState.CANCELLING, reason=reason)

            # Clear first-sentence tracking so new request starts fresh
            self._first_sentence_dispatched.discard(req_id)

            try:
                engine = speech.get_engine()
                if engine and hasattr(engine, "queue_manager"):
                    engine.queue_manager.cancel_request(req_id)
            except Exception as e:
                print(f"[SpeechCoordinator Interrupt Error]: {e}", flush=True)

            print(f"[WS_TX] event=speaking_interrupted request_id={req_id} speech_id={speech_id} reason={reason}", flush=True)
            print(f"[SPEECH_INTERRUPTED] request_id={req_id} speech_id={speech_id} reason='{reason}'", flush=True)

            try:
                from api.websocket.jarvis import broadcast_sync
                broadcast_sync({
                    "type": "speaking_interrupted",
                    "text": "[Interrupted]",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": req_id,
                    "speech_id": speech_id,
                    "session_id": session_id,
                    "reason": reason
                })
            except Exception:
                pass

            self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
            self.timeout_manager.reset()
            self._last_speech_end_time = time.time()

    def cancel_speech(self):
        """
        Cancels any active speech session, flushes enqueued audio chunks,
        and stops playback cleanly without race conditions.
        """
        self.interrupt_speech(reason="user_cancel")

    def end_speech_session(self):
        """
        Signals the end of a streaming response session. Advances state machine
        to WAITING_FOR_NEXT_COMMAND after speech audio playback has finished (with 2.5s safety timeout).
        """
        # Wait outside lock until audio queue and playback are finished (max 2.5s)
        wait_start = time.time()
        while speech.is_speaking() and (time.time() - wait_start < 2.5):
            time.sleep(0.05)

        with self._lock:
            self.timeout_manager.reset()
            self._session_active = False
            self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
            self._last_speech_end_time = time.time()

    def speak(self, text: str, wait: bool = True, request_id: Optional[str] = None):
        """Convenience method for single-shot speech calls (non-streaming, e.g. direct commands)."""
        if not text:
            return

        with self._lock:
            prev_state = self.state_machine.state
            self.state_machine.transition_to(State.SPEAKING)
            self.timeout_manager.reset()

            clean_t = text.strip()
            try:
                print(f"Jarvis: {clean_t}", flush=True)
            except Exception:
                pass

            now = time.time()
            stale_texts = [k for k, t in list(self._dispatched_texts.items()) if now - t > 10.0]
            for k in stale_texts:
                self._dispatched_texts.pop(k, None)

            if clean_t in self._dispatched_texts and (now - self._dispatched_texts[clean_t]) < 3.0:
                print(f"[TTS_DUPLICATE_BLOCKED]\ntext={clean_t[:30]}\nreason=duplicate_text_window", flush=True)
                return
            self._dispatched_texts[clean_t] = now

            import os
            import uuid
            from datetime import datetime
            from speech.voice_session_manager import VoiceSessionManager
            vsm = VoiceSessionManager.get_instance()

            speech_id = f"speech_{uuid.uuid4().hex[:8]}"
            req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.now().isoformat()

            if vsm.is_request_invalidated(req_id):
                print(f"[TTS_STALE_BLOCKED] request_id={req_id} reason=request_interrupted", flush=True)
                return
            vsm.mark_speaking_started(req_id, speech_id=speech_id)

            if speech_id in self._dispatched_responses:
                print(f"[TTS_DUPLICATE_BLOCKED]\nresponse_id={speech_id}\nrequest_id={req_id}", flush=True)
                return
            if len(self._dispatched_responses) > 200:
                self._dispatched_responses.clear()
            self._dispatched_responses.add(speech_id)

            if len(self._request_dispatch_counts) > 200:
                self._request_dispatch_counts.clear()

            count = self._request_dispatch_counts.get(req_id, 0) + 1
            if count > 1:
                print(f"[TTS_DUPLICATE_BLOCKED]\nrequest_id={req_id}\ncount={count}\nreason=already_dispatched_for_request", flush=True)
                return
            self._request_dispatch_counts[req_id] = count

            print(f"[CONVERSATION_RESPONSE]\nrequest_id={req_id}\nresponse_id={speech_id}\ntext={clean_t}", flush=True)
            print(f"[CONVERSATION_DISPATCH]\nrequest_id={req_id}\nresponse_id={speech_id}", flush=True)
            print(f"[TTS_DISPATCH] request_id={req_id} count={count}", flush=True)
            print(f"[TTS_QUEUE] request_id={req_id} count={count}", flush=True)

            tts_gen_start = time.perf_counter()
            try:
                audio_path = speech.speak(clean_t, wait=False, speech_id=speech_id, request_id=req_id)
            except Exception as e:
                print(f"[SpeechCoordinator Error]: speech generation error: {e}", flush=True)
                audio_path = None
            tts_dur_ms = (time.perf_counter() - tts_gen_start) * 1000.0

            owner = os.getenv("PLAYBACK_OWNER", "FRONTEND").upper()

            print(f"[TTS_READY]\nrequest_id={req_id}\nspeech_id={speech_id}\nduration_ms={tts_dur_ms:.1f}", flush=True)
            print(f"[AUDIO_PLAYBACK_OWNER]\nowner={owner}", flush=True)
            print(f"[VOICE_PLAYBACK_OWNER]\nowner={owner}", flush=True)

            audio_url = ""
            if audio_path:
                filename = os.path.basename(audio_path)
                audio_url = f"http://localhost:8000/speech/cache/{filename}"

            print(f"[WS_TX] event=speaking_start speech_id={speech_id} text={clean_t[:40]} audio_url={audio_url}", flush=True)
            try:
                from api.websocket.jarvis import broadcast_sync
                broadcast_sync({
                    "type": "speaking_start",
                    "text": clean_t,
                    "timestamp": timestamp,
                    "request_id": req_id,
                    "speech_id": speech_id,
                    "audio_url": audio_url,
                    "playback_owner": owner,
                    "owner": owner
                })
            except Exception:
                pass

            if wait:
                engine = speech.get_engine()
                if engine and hasattr(engine, "queue_manager"):
                    engine.queue_manager.wait_until_done()

            self.timeout_manager.reset()
            self._last_speech_end_time = time.time()

            print(f"[WS_TX] event=speaking_end speech_id={speech_id}", flush=True)
            try:
                from api.websocket.jarvis import broadcast_sync
                broadcast_sync({
                    "type": "speaking_end",
                    "text": clean_t,
                    "timestamp": datetime.now().isoformat(),
                    "request_id": req_id,
                    "speech_id": speech_id
                })
            except Exception:
                pass

            if self._session_active:
                pass
            elif prev_state == State.WAKE_DETECTED:
                self.state_machine.transition_to(State.LISTENING)
            elif prev_state in (State.SLEEPING, State.WAKE_MODE):
                self.state_machine.transition_to(State.WAKE_MODE)
            else:
                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)

    def get_last_speech_end_time(self) -> float:
        """Returns the epoch timestamp when speech audio output last completed."""
        with self._lock:
            return self._last_speech_end_time

    def is_speaking(self) -> bool:
        """
        Returns True if TTS audio is playing, queue is non-empty, state is SPEAKING,
        or a multi-chunk speech session is currently active.
        """
        with self._lock:
            return (
                self._session_active or
                speech.is_speaking() or
                self.state_machine.state in (State.SPEAKING, State.THINKING, State.PROCESSING)
            )

    def shutdown(self):
        """Clean shutdown of background TTS executor."""
        try:
            self._tts_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            self._tts_executor.shutdown(wait=False)
