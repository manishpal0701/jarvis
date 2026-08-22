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

# Sentence boundary detection: split on '. ', '! ', '? ', '\n', '...'
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+|(?<=\.\.\.)\s*|\n+')

# Default optimized Ollama parameters for CPU conversational response
DEFAULT_OPTIONS = {
    "num_ctx": 1536,      # Limit context window to 1536 tokens for fast CPU prompt evaluation
    "num_predict": 150,   # Limit max generated output tokens (2-3 concise sentences)
    "temperature": 0.7,   # Natural creativity without excessive rambling
    "top_p": 0.9          # Focused vocabulary sampling
}

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
        """Prewarm the Ollama model asynchronously — keeps model loaded in RAM."""
        if self._prewarmed:
            return

        def _prewarm_thread():
            try:
                # Fast prewarm with minimal prompt/predict length
                self._client.chat(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": "hi"}],
                    options={"num_ctx": 512, "num_predict": 5},
                    keep_alive=-1
                )
                self._prewarmed = True
            except Exception as e:
                print(f"Ollama Prewarm Warning: {e}")

        threading.Thread(target=_prewarm_thread, daemon=True).start()

    def generate_response(self, messages: list, keep_alive: int = -1, options: dict = None) -> str:
        """
        Blocking (non-streaming) Ollama call. Returns full response string.
        """
        opts = options or DEFAULT_OPTIONS
        response = self._client.chat(
            model=MODEL_NAME,
            messages=messages,
            options=opts,
            keep_alive=keep_alive
        )
        return response["message"]["content"]

    def generate_response_token_stream(self, messages: list, keep_alive: int = -1, options: dict = None):
        """
        Native Ollama streaming generator. Yields token string chunks directly from Ollama as stream=True emits them.
        """
        opts = options or DEFAULT_OPTIONS
        stream = self._client.chat(
            model=MODEL_NAME,
            messages=messages,
            options=opts,
            stream=True,
            keep_alive=keep_alive
        )
        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    def generate_response_streaming(
        self,
        messages: list,
        sentence_callback,
        perf_profiler=None,
        debug_perf: bool = False,
        keep_alive: int = -1,
        options: dict = None
    ) -> str:
        """
        Streaming Ollama call. Buffers tokens into sentences and calls
        sentence_callback(sentence: str) as each sentence becomes available.

        Returns full response string.
        """
        full_response = []
        token_buffer = ""
        first_token_marked = False
        first_sentence_dispatched = False
        first_token_time = None
        start_time = time.perf_counter()

        opts = options or DEFAULT_OPTIONS

        # Send request to Ollama
        stream = self._client.chat(
            model=MODEL_NAME,
            messages=messages,
            options=opts,
            stream=True,
            keep_alive=keep_alive
        )

        last_chunk = None

        for chunk in stream:
            last_chunk = chunk
            token = chunk.get("message", {}).get("content", "")
            if not token:
                continue

            # Mark first token latency
            if not first_token_marked:
                first_token_time = time.perf_counter()
                if perf_profiler:
                    perf_profiler.mark("OLLAMA_FIRST_TOKEN")
                first_token_marked = True

            token_buffer += token
            full_response.append(token)

            # Detect sentence boundaries and dispatch complete sentences
            parts = _SENTENCE_END.split(token_buffer)
            if len(parts) > 1:
                for sentence in parts[:-1]:
                    sentence = sentence.strip()
                    if sentence:
                        if not first_sentence_dispatched:
                            if perf_profiler:
                                perf_profiler.mark("TTS_FIRST_AUDIO")
                            first_sentence_dispatched = True
                        sentence_callback(sentence)
                token_buffer = parts[-1]

        # Flush any remaining text in buffer
        if token_buffer.strip():
            if not first_sentence_dispatched and perf_profiler:
                perf_profiler.mark("TTS_FIRST_AUDIO")
            sentence_callback(token_buffer.strip())

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
