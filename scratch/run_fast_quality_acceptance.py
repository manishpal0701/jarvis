"""
scratch/run_fast_quality_acceptance.py
Fast quality acceptance test executing 10 conversational scenarios to print responses and timing.
"""

import sys
sys.path.insert(0, ".")

import time
from ai.ask_ollama import ask_ollama_streaming

QUALITY_QUERIES = [
    ("Q1", "hello jarvis"),
    ("Q2", "hello jarvis how are you"),
    ("Q3", "good morning"),
    ("Q4", "what are you doing"),
    ("Q5", "jarvis aaj tum sundar lag rahi ho"),
    ("Q6", "thank you"),
    ("Q7", "mera mood off hai"),
    ("Q8", "I'm feeling lonely"),
    ("Q9", "tell me something funny"),
    ("Q10", "what can you do")
]

def run_fast_quality():
    print("=================================================================", flush=True)
    print("FAST CONVERSATIONAL QUALITY ACCEPTANCE TEST (10 QUERIES)", flush=True)
    print("=================================================================\n", flush=True)

    results = []

    for tag, query in QUALITY_QUERIES:
        t0 = time.perf_counter()
        captured_chunks = []
        def cb(chunk):
            captured_chunks.append(chunk)

        req_id = f"qtest_{tag}"
        resp = ask_ollama_streaming(
            query,
            speaker_name="Boss",
            relation="boss",
            speak_callback=cb,
            speech_coordinator=None,
            request_id=req_id
        )
        total_ms = (time.perf_counter() - t0) * 1000.0
        results.append((tag, query, resp, total_ms, len(captured_chunks)))
        print(f"[{tag}] User: \"{query}\"\n     Jarvis: \"{resp}\" ({total_ms:.1f}ms | {len(captured_chunks)} chunks)\n", flush=True)

    print("=================================================================", flush=True)
    print("FINAL QUALITY ACCEPTANCE SUMMARY REPORT", flush=True)
    print("=================================================================", flush=True)
    for tag, query, resp, dur_ms, c_cnt in results:
        print(f"[{tag}] User: \"{query}\" -> Jarvis: \"{resp}\" ({dur_ms:.1f}ms)", flush=True)

if __name__ == "__main__":
    run_fast_quality()
