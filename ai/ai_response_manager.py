"""
ai/ai_response_manager.py
Singleton Ollama client manager. Supports both blocking and streaming response modes.
Streaming mode pipes tokens through a sentence buffer, calling a callback per sentence
so TTS can begin on the first sentence rather than waiting for the full response.
"""
import ollama
from config import MODEL_NAME
import threading
import time
import re
import datetime

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

# Clause & sentence boundary detection: split strictly on sentence ends: '. ', '! ', '? ', '\n', '...'
_CLAUSE_END = re.compile(r'(?<=[.!?])\s+|(?<=\.\.\.)\s*|\n+')

# Default optimized Ollama parameters for CPU conversational response
DEFAULT_OPTIONS = {
    "num_ctx": 1536,      # Limit context window to 1536 tokens for fast CPU prompt evaluation
    "num_predict": 150,   # Limit max generated output tokens (2-3 concise sentences)
    "temperature": 0.7,   # Natural creativity without excessive rambling
    "top_p": 0.9          # Focused vocabulary sampling
}

# Dedicated options for general conversation (Qwen3:8b) - CPU optimized
CONVERSATION_OPTIONS = {
    "num_ctx": 2048,      # Matched with prewarm context size to prevent context overflow while keeping KV cache fast
    "num_predict": 120,   # Target 1-3 spoken sentences max
    "temperature": 0.7,
    "top_p": 0.9
}

class LLMTimeoutException(Exception):
    """Raised when an LLM generation call exceeds the maximum allowed timeout threshold."""
    pass

class AIResponseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AIResponseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._client = ollama.Client()
        self._prewarmed = False
        self._initialized = True

    def prewarm(self):
        """Prewarm the Ollama model asynchronously — keeps model loaded in RAM with matching context size."""
        if self._prewarmed:
            return

        def _prewarm_thread():
            try:
                # Fast prewarm with matching num_ctx (2048)
                self._client.chat(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": "hi"}],
                    options={"num_ctx": 2048, "num_predict": 5},
                    think=False,
                    keep_alive=-1
                )
                self._prewarmed = True
                print(f"[OLLAMA_PREWARMED] model={MODEL_NAME} num_ctx=2048 status=READY", flush=True)
            except Exception as e:
                print(f"Ollama Prewarm Warning: {e}", flush=True)

        threading.Thread(target=_prewarm_thread, daemon=True).start()

    def generate_response(self, messages: list, keep_alive: int = -1, options: dict = None, model_name: str = None, timeout: float = 180.0, think: bool = None) -> str:
        """
        Blocking (non-streaming) Ollama call. Returns full response string with socket timeout.
        Passes think parameter to Ollama ONLY if explicitly provided.
        """
        target_model = model_name or MODEL_NAME
        opts = options or DEFAULT_OPTIONS
        kwargs = {
            "model": target_model,
            "messages": messages,
            "options": opts,
            "keep_alive": keep_alive
        }
        if think is not None:
            kwargs["think"] = think

        try:
            client = ollama.Client(timeout=timeout)
            response = client.chat(**kwargs)
            return response["message"]["content"]
        except Exception as e:
            err_str = str(e).lower()
            if "time" in err_str or "timeout" in err_str or "timed out" in err_str:
                raise LLMTimeoutException(f"Ollama generation for model '{target_model}' timed out after {timeout} seconds") from e
            raise

    def generate_response_token_stream(
        self,
        messages: list,
        keep_alive: int = -1,
        options: dict = None,
        model_name: str = None,
        timeout: float = 180.0,
        first_token_timeout: float = 180.0,
        inter_token_timeout: float = 30.0,
        file_name: str = "unknown",
        think: bool = None
    ):
        """
        Native Ollama streaming generator with two-stage timeout handling and timing logs.
        """
        target_model = model_name or MODEL_NAME
        opts = options or DEFAULT_OPTIONS
        if timeout != 180.0 and first_token_timeout == 180.0:
            first_token_timeout = timeout
        req_start_time = time.time()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        print(f"[LLM_REQUEST_START] model={target_model} file={file_name} timestamp={now_iso}", flush=True)
        
        first_token_received = False
        first_token_latency = 0.0
        token_count = 0
        last_token_time = req_start_time
        
        kwargs = {
            "model": target_model,
            "messages": messages,
            "options": opts,
            "stream": True,
            "keep_alive": keep_alive
        }
        if think is not None:
            kwargs["think"] = think

        try:
            client = getattr(self, '_client', None) or ollama.Client(timeout=first_token_timeout)
            stream = client.chat(**kwargs)
            for chunk in stream:
                curr_time = time.time()
                
                if not first_token_received:
                    if curr_time - req_start_time > first_token_timeout:
                        elapsed = round(curr_time - req_start_time, 2)
                        print(f"[LLM_TIMEOUT] model={target_model} file={file_name} type=first_token elapsed={elapsed}s", flush=True)
                        print(f"[LLM_REQUEST_END] file={file_name} success=false", flush=True)
                        raise LLMTimeoutException(f"Ollama first-token generation for model '{target_model}' timed out after {elapsed} seconds")
                    first_token_received = True
                    first_token_latency = round(curr_time - req_start_time, 3)
                    print(f"[LLM_FIRST_TOKEN] model={target_model} file={file_name} latency={first_token_latency}s", flush=True)
                    try:
                        from core.performance_profiler import PerformanceProfiler
                        PerformanceProfiler.mark("LLM_FIRST_TOKEN")
                    except Exception:
                        pass
                else:
                    if curr_time - last_token_time > inter_token_timeout:
                        elapsed = round(curr_time - last_token_time, 2)
                        print(f"[LLM_TIMEOUT] model={target_model} file={file_name} type=inter_token elapsed={elapsed}s", flush=True)
                        print(f"[LLM_REQUEST_END] file={file_name} success=false", flush=True)
                        raise LLMTimeoutException(f"Ollama token stream stalled for model '{target_model}' for {elapsed} seconds")
                
                last_token_time = curr_time
                token = chunk.get("message", {}).get("content", "")
                if token:
                    token_count += 1
                    if token_count % 50 == 0:
                        elapsed_so_far = round(curr_time - req_start_time, 2)
                        print(f"[LLM_STREAM_PROGRESS] model={target_model} file={file_name} elapsed={elapsed_so_far}s tokens={token_count}", flush=True)
                    yield token

            total_time = round(time.time() - req_start_time, 3)
            print(f"[LLM_REQUEST_END] model={target_model} file={file_name} total_time={total_time}s total_tokens={token_count} success=true", flush=True)

        except LLMTimeoutException as lte:
            print(f"[LLM_REQUEST_END] file={file_name} success=false", flush=True)
            raise lte
        except Exception as e:
            print(f"[LLM_REQUEST_END] file={file_name} success=false", flush=True)
            curr_time = time.time()
            elapsed = round(curr_time - req_start_time, 2)
            err_str = str(e).lower()
            if "time" in err_str or "timeout" in err_str or "timed out" in err_str:
                timeout_type = "first_token" if not first_token_received else "inter_token"
                print(f"[LLM_TIMEOUT] model={target_model} file={file_name} type={timeout_type} elapsed={elapsed}s", flush=True)
                raise LLMTimeoutException(f"Ollama generation for model '{target_model}' timed out after {elapsed} seconds") from e
            raise

    def generate_response_streaming(
        self,
        messages: list,
        sentence_callback,
        perf_profiler=None,
        debug_perf: bool = False,
        keep_alive: int = -1,
        options: dict = None,
        think: bool = None,
        timeout: float = 60.0,
        inter_token_timeout: float = 30.0,
        request_id: str = ""
    ) -> str:
        """
        Streaming Ollama call with token stall protection. Buffers tokens into complete sentences
        using StreamingSentenceBuffer and calls sentence_callback(sentence: str) per complete sentence.

        Returns full response string.
        """
        from ai.sentence_buffer import StreamingSentenceBuffer
        sentence_buffer_inst = StreamingSentenceBuffer()

        full_response = []
        first_token_marked = False
        first_sentence_dispatched = False
        first_token_time = None
        start_time = time.perf_counter()
        last_token_time = start_time

        opts = options or DEFAULT_OPTIONS

        kwargs = {
            "model": MODEL_NAME,
            "messages": messages,
            "options": opts,
            "stream": True,
            "keep_alive": keep_alive
        }
        if think is not None:
            kwargs["think"] = think

        # Send request to Ollama with socket timeout
        try:
            print(f"[STREAM_DEBUG] ollama_request_started model={MODEL_NAME}", flush=True)
            client = ollama.Client(timeout=timeout)
            stream = client.chat(**kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "time" in err_str or "timeout" in err_str or "timed out" in err_str:
                raise LLMTimeoutException(f"Ollama connection timed out after {timeout} seconds") from e
            raise

        last_chunk = None
        chunk_idx = 0

        try:
            for chunk in stream:
                curr_t = time.perf_counter()
                # Check inter-token stall (e.g. 30s pause between tokens)
                if first_token_marked and (curr_t - last_token_time > inter_token_timeout):
                    elapsed_stall = round(curr_t - last_token_time, 1)
                    raise LLMTimeoutException(f"Ollama token stream stalled for {elapsed_stall}s")

                last_chunk = chunk
                token = chunk.get("message", {}).get("content", "")
                if not token:
                    continue

                last_token_time = curr_t
                chunk_idx += 1
                print(f"[STREAM_DEBUG] ollama_chunk_received chunk_index={chunk_idx} text=\"{token}\"", flush=True)

                # Mark first token latency
                if not first_token_marked:
                    first_token_time = curr_t
                    if perf_profiler:
                        perf_profiler.mark("OLLAMA_FIRST_TOKEN")
                    first_token_marked = True

                full_response.append(token)

                # Append token to sentence buffer and dispatch complete sentences
                sentences = sentence_buffer_inst.append(token, request_id=request_id)
                for sentence in sentences:
                    if not first_sentence_dispatched:
                        if perf_profiler:
                            perf_profiler.mark("TTS_FIRST_AUDIO")
                        first_sentence_dispatched = True
                    print(f"[STREAM_DEBUG] sentence_ready text=\"{sentence}\"", flush=True)
                    sentence_callback(sentence)
        except LLMTimeoutException:
            raise
        except Exception as e:
            err_str = str(e).lower()
            if "time" in err_str or "timeout" in err_str or "timed out" in err_str:
                raise LLMTimeoutException(f"Ollama stream read timed out after {timeout} seconds") from e
            raise

        # Flush any remaining complete response text in buffer at stream end
        final_sentences = sentence_buffer_inst.flush_remaining(request_id=request_id)
        for sentence in final_sentences:
            if not first_sentence_dispatched and perf_profiler:
                perf_profiler.mark("TTS_FIRST_AUDIO")
            print(f"[STREAM_DEBUG] sentence_ready text=\"{sentence}\"", flush=True)
            sentence_callback(sentence)

        total_time = time.perf_counter() - start_time
        first_token_latency = (first_token_time - start_time) if first_token_time else total_time

        if perf_profiler:
            perf_profiler.mark("OLLAMA_COMPLETE")

        # Optional detailed [OLLAMA PERF] printing when debug_perf is True
        if debug_perf and last_chunk:
            prompt_chars = sum(len(m.get("content", "")) for m in messages)
            prompt_tokens = last_chunk.get("prompt_eval_count", "N/A")
            load_dur = (last_chunk.get("load_duration", 0) or 0) / 1e9
            prompt_eval_dur = (last_chunk.get("prompt_eval_duration", 0) or 0) / 1e9
            eval_count = last_chunk.get("eval_count", len(full_response))
            eval_dur = (last_chunk.get("eval_duration", 0) or 0) / 1e9
            tokens_per_sec = (eval_count / eval_dur) if eval_dur > 0 else 0.0

            print("\n[OLLAMA PERF]")
            print(f"Model: {MODEL_NAME}")
            print(f"Model loaded: {self._prewarmed}")
            print(f"Prompt characters: {prompt_chars}")
            print(f"Prompt tokens if available: {prompt_tokens}")
            print(f"Prompt evaluation: {prompt_eval_dur:.3f}s")
            print(f"First token: {first_token_latency:.3f}s")
            print(f"Generation: {eval_dur:.3f}s ({eval_count} tokens)")
            print(f"Total: {total_time:.3f}s")
            print(f"Tokens/sec if available: {tokens_per_sec:.2f} t/s\n")

        return "".join(full_response)

