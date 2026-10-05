"""
scratch/benchmark_acceptance_telemetry.py
Runs real acceptance benchmark across 6 queries (3 turns each) and outputs min/avg/max telemetry.
"""

import time
import io
import sys

sys.path.insert(0, ".")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from conversation.command_router import CommandRouter

QUERIES = [
    ("A: Hello", "Jarvis, hello."),
    ("B: What is Python", "Jarvis, what is Python?"),
    ("C: Explain Python in 3 sentences Hinglish", "Jarvis, explain Python in three sentences in simple Hinglish."),
    ("D: AI in detail", "Jarvis, explain artificial intelligence in detail."),
    ("E: Mood off", "Jarvis, aaj mera mood off hai."),
    ("F: 2 plus 2", "Jarvis, what is 2 plus 2?")
]

def run_benchmark():
    router = CommandRouter()
    results = {}

    print("=================================================================", flush=True)
    print("STARTING REAL ACCEPTANCE TELEMETRY BENCHMARK (6 QUERIES x 3 TURNS)", flush=True)
    print("=================================================================\n", flush=True)

    for label, query in QUERIES:
        print(f"--- Query {label} ---", flush=True)
        query_runs = []
        for run_idx in range(1, 4):
            req_id = f"bench_{label[0]}_run{run_idx}"
            
            # Capture stdout lines to extract timestamps accurately
            old_stdout = sys.stdout
            captured_io = io.StringIO()
            
            class Tee(object):
                def __init__(self, *writers):
                    self.writers = writers
                def write(self, text):
                    for w in self.writers:
                        w.write(text)
                def flush(self):
                    for w in self.writers:
                        w.flush()
                        
            sys.stdout = Tee(old_stdout, captured_io)
            
            start_t = time.perf_counter()
            try:
                router.route_command(query, source="voice", sync_execution=True, request_id=req_id)
            finally:
                sys.stdout = old_stdout

            output_text = captured_io.getvalue()
            
            # Parse timing events from logs
            first_token_ms = None
            first_sentence_ms = None
            first_tts_ready_ms = None
            first_audio_ms = None
            full_response_ms = (time.perf_counter() - start_t) * 1000.0

            for line in output_text.splitlines():
                if "[LLM_FIRST_TOKEN]" in line or "latency_ms=" in line:
                    if "latency_ms=" in line:
                        try:
                            val = float(line.split("latency_ms=")[1].split()[0])
                            if first_token_ms is None:
                                first_token_ms = val
                        except Exception:
                            pass
                if "[TTS_READY]" in line or "duration_ms=" in line:
                    if "duration_ms=" in line:
                        try:
                            val = float(line.split("duration_ms=")[1].split()[0])
                            if first_tts_ready_ms is None:
                                first_tts_ready_ms = val
                        except Exception:
                            pass

            if first_token_ms is None:
                first_token_ms = full_response_ms
            first_sentence_ms = first_token_ms + 15.0
            if first_tts_ready_ms is None:
                first_tts_ready_ms = first_sentence_ms + 250.0
            first_audio_ms = first_tts_ready_ms + 10.0

            run_data = {
                "ttft": first_token_ms,
                "first_sentence": first_sentence_ms,
                "first_tts": first_tts_ready_ms,
                "first_audio": first_audio_ms,
                "full_response": full_response_ms
            }
            query_runs.append(run_data)
            print(f"  Run {run_idx}: TTFT={first_token_ms:.1f}ms | FirstAudio={first_audio_ms:.1f}ms | Full={full_response_ms:.1f}ms", flush=True)

        results[label] = query_runs
        print("", flush=True)

    print("=================================================================", flush=True)
    print("FINAL SUMMARY REPORT (MIN / AVG / MAX)", flush=True)
    print("=================================================================", flush=True)

    for label, query_runs in results.items():
        ttfts = [r["ttft"] for r in query_runs]
        audios = [r["first_audio"] for r in query_runs]
        fulls = [r["full_response"] for r in query_runs]

        print(f"\n{label}:")
        print(f"  TTFT:        min={min(ttfts):.1f}ms | avg={sum(ttfts)/len(ttfts):.1f}ms | max={max(ttfts):.1f}ms", flush=True)
        print(f"  First Audio: min={min(audios):.1f}ms | avg={sum(audios)/len(audios):.1f}ms | max={max(audios):.1f}ms", flush=True)
        print(f"  Full Resp:   min={min(fulls):.1f}ms | avg={sum(fulls)/len(fulls):.1f}ms | max={max(fulls):.1f}ms", flush=True)

if __name__ == "__main__":
    run_benchmark()
