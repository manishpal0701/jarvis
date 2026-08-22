"""
core/performance_profiler.py
Lightweight per-request pipeline performance profiler.
Resets every request. Thread-safe. Prints a concise [PERFORMANCE] report.
"""
import time
import threading


class PerformanceProfiler:
    """
    Thread-safe per-request performance profiler.
    Call mark(label) at key pipeline points, then report() to print timings.
    """
    _local = threading.local()

    @classmethod
    def reset(cls):
        """Reset all marks for a new request."""
        cls._local.marks = []
        cls._local.start = time.perf_counter()

    @classmethod
    def mark(cls, label: str):
        """Record a named timestamp in the current request."""
        if not hasattr(cls._local, "marks"):
            cls.reset()
        t = time.perf_counter() - cls._local.start
        cls._local.marks.append((label, t))

    @classmethod
    def report(cls):
        """Print a concise [PERFORMANCE] table for the current request."""
        if not hasattr(cls._local, "marks") or not cls._local.marks:
            return

        marks = cls._local.marks
        print("\n[PERFORMANCE]")
        prev_t = 0.0
        for label, t in marks:
            delta = t - prev_t
            print(f"  {label:<35} {t:.3f}s  (+{delta:.3f}s)")
            prev_t = t

        # Derived metrics
        label_map = {label: t for label, t in marks}
        tts_first = label_map.get("TTS_FIRST_AUDIO")
        ollama_first = label_map.get("OLLAMA_FIRST_TOKEN")
        ollama_done = label_map.get("OLLAMA_COMPLETE")
        total = marks[-1][1] if marks else 0

        if tts_first is not None:
            print(f"  {'--- Time to First Speech':<35} {tts_first:.3f}s")
        if ollama_first is not None:
            print(f"  {'--- Ollama First Token Latency':<35} {ollama_first:.3f}s")
        if ollama_done is not None:
            print(f"  {'--- Ollama Total Generation':<35} {ollama_done:.3f}s")
        print(f"  {'--- Total Request Time':<35} {total:.3f}s")
        print()
