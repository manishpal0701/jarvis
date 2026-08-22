import re
import time
from typing import Callable, Optional

class MarkdownFenceFilter:
    """
    Stream filter state machine.
    Strips markdown block fences (e.g., ```python\n ... ```) from real-time token streams,
    ensuring that only actual code is emitted to the live editor preview buffer.
    """

    def __init__(self):
        self.started = False
        self.buffer = ""

    def process(self, token: str) -> str:
        if not token:
            return ""

        self.buffer += token

        # 1. Strip leading fence (e.g. ```python\n)
        if not self.started:
            # Check if buffer starts with ```
            if self.buffer.startswith("```"):
                if "\n" in self.buffer:
                    # Header complete, strip up to newline
                    first_newline = self.buffer.find("\n")
                    self.started = True
                    cleaned = self.buffer[first_newline + 1:]
                    self.buffer = ""
                    return cleaned
                else:
                    # Waiting for opening line newline
                    return ""
            else:
                # Buffer doesn't start with ```, stream normally
                self.started = True
                cleaned = self.buffer
                self.buffer = ""
                return cleaned

        # 2. In body: check if token contains trailing ```
        if "```" in self.buffer:
            parts = self.buffer.split("```")
            out = parts[0]
            self.buffer = "```".join(parts[1:])
            return out

        out = self.buffer
        self.buffer = ""
        return out

    def flush(self) -> str:
        rem = self.buffer
        self.buffer = ""
        if rem.startswith("```"):
            return ""
        return rem.replace("```", "")

class TokenBatcher:
    """
    Pacing buffer targeting smooth 30-60 FPS visual UI updates.
    Combines tiny LLM sub-tokens into ~15-30ms micro-batches to prevent SSE socket congestion.
    """

    def __init__(self, callback: Callable[[str], None], batch_interval_ms: float = 20.0, min_chunk_len: int = 15):
        self.callback = callback
        self.batch_interval_sec = batch_interval_ms / 1000.0
        self.min_chunk_len = min_chunk_len
        self.buffer = ""
        self.last_emit_time = time.perf_counter()

    def add(self, text: str):
        if not text:
            return
        self.buffer += text
        now = time.perf_counter()

        # Emit if buffer has newlines, reached min length, or batch interval elapsed
        if "\n" in self.buffer or len(self.buffer) >= self.min_chunk_len or (now - self.last_emit_time) >= self.batch_interval_sec:
            self.flush()

    def flush(self):
        if self.buffer:
            text_to_emit = self.buffer
            self.buffer = ""
            self.last_emit_time = time.perf_counter()
            self.callback(text_to_emit)
