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
    Strictly separates DIRECT_COMMAND_EXECUTION_TIME from FIRST_AUDIBLE_AUDIO_LATENCY.
    """
    _local = threading.local()

    @classmethod
    def reset(cls, request_id: str = None):
        """Reset all marks for a new request."""
        cls._local.request_id = request_id
        cls._local.marks = []
        cls._local.start = time.perf_counter()
        if request_id:
            print(f"[PERF_START]\nrequest_id={request_id}", flush=True)

    @classmethod
    def start_request(cls, request_id: str):
        """Signals start of performance tracking for a request_id."""
        cls.reset(request_id=request_id)

    @classmethod
    def log_stage(cls, request_id: str, stage: str, duration_ms: float):
        """Prints formatted PERF_STAGE log."""
        print(f"[PERF_STAGE]\nrequest_id={request_id}\nstage={stage}\nduration_ms={duration_ms:.1f}", flush=True)

    @classmethod
    def log_total(cls, request_id: str, duration_ms: float):
        """Prints formatted PERF_TOTAL log."""
        print(f"[PERF_TOTAL]\nrequest_id={request_id}\nduration_ms={duration_ms:.1f}", flush=True)

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
        print("\n[PERFORMANCE_TIMING_BREAKDOWN]", flush=True)
        prev_t = 0.0
        for label, t in marks:
            delta = t - prev_t
            print(f"  {label:<35} {t*1000:.1f} ms  (+{delta*1000:.1f} ms)", flush=True)
            prev_t = t

        label_map = {label: t for label, t in marks}
        req_id = getattr(cls._local, "request_id", None)
        
        # 1. Direct Command Processing Latency
        direct_exec = label_map.get("DIRECT_COMMAND_EXECUTION_TIME")
        if direct_exec is not None:
            print(f"  {'--- DIRECT_COMMAND_EXECUTION_TIME':<35} {direct_exec*1000:.1f} ms", flush=True)

        # 2. First Audible Audio Latency (measured when audio output playback actually starts)
        audio_start = label_map.get("AUDIO_PLAYBACK_START") or label_map.get("TTS_FIRST_AUDIO")
        if audio_start is not None:
            print(f"  {'--- FIRST_AUDIBLE_AUDIO_LATENCY':<35} {audio_start*1000:.1f} ms", flush=True)

        # 3. Component Breakdown
        llm_ft = label_map.get("LLM_FIRST_TOKEN") or label_map.get("OLLAMA_FIRST_TOKEN")
        if llm_ft is not None:
            print(f"  {'--- LLM Time-To-First-Token (TTFT)':<35} {llm_ft*1000:.1f} ms", flush=True)

        total = marks[-1][1] if marks else 0.0
        print(f"  {'--- TOTAL_RESPONSE_LATENCY':<35} {total*1000:.1f} ms", flush=True)
        if req_id:
            cls.log_total(req_id, total * 1000.0)
        print(flush=True)
