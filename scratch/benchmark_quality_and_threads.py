"""
scratch/benchmark_quality_and_threads.py
Runs CPU num_thread benchmark (1, 2, 4, 6, 8) and captures real LLM responses across 10 conversational queries.
"""

import sys
sys.path.insert(0, ".")

import time
from ai.ask_ollama import ask_ollama_streaming
from config import MODEL_NAME

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

def run_quality_matrix():
    print("=================================================================", flush=True)
    print("REAL CONVERSATIONAL QUALITY ACCEPTANCE TEST (10 QUERIES)", flush=True)
    print("=================================================================\n", flush=True)

    results = []

    for tag, query in QUALITY_QUERIES:
        print(f"--- {tag}: \"{query}\" ---", flush=True)
        t0 = time.perf_counter()
        
        chunks = []
        def dummy_cb(text):
            chunks.append(text)

        req_id = f"qtest_{tag}"
        resp = ask_ollama_streaming(
            query,
            speaker_name="Boss",
            relation="boss",
            speak_callback=dummy_cb,
            request_id=req_id
        )
        total_ms = (time.perf_counter() - t0) * 1000.0

        print(f"  Generated Response: \"{resp}\"", flush=True)
        print(f"  Total Duration: {total_ms:.1f} ms", flush=True)
        print(f"  Chunks Count: {len(chunks)}", flush=True)
        print("", flush=True)
        results.append((tag, query, resp, total_ms, len(chunks)))

    print("=================================================================", flush=True)
    print("CONVERSATIONAL QUALITY SUMMARY", flush=True)
    print("=================================================================", flush=True)
    for tag, query, resp, dur_ms, c_cnt in results:
        print(f"[{tag}] User: \"{query}\" -> Jarvis: \"{resp}\" ({dur_ms:.1f}ms)", flush=True)

if __name__ == "__main__":
    run_quality_matrix()
