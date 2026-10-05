"""
Direct test runner for all 5 queries sequentially
"""
import time
import uuid
import ollama
from ai.ask_ollama import ask_ollama_streaming

def test():
    queries = [
        "aaj main bahut khush hun",
        "mujhe ek motivational line bolo",
        "aaj mausam kaisa hai",
        "tum kya kya kar sakte ho",
        "thank you jarvis"
    ]
    
    for i, q in enumerate(queries, 1):
        print(f"\n--- QUERY {i}: '{q}' ---", flush=True)
        start_t = time.perf_counter()
        req_id = f"req_test_q{i}_{uuid.uuid4().hex[:4]}"
        first_t = [None]
        
        def cb(txt):
            if first_t[0] is None:
                first_t[0] = time.perf_counter()
        
        resp = ask_ollama_streaming(q, "Boss", "boss", speak_callback=cb, request_id=req_id)
        total_ms = (time.perf_counter() - start_t) * 1000.0
        first_ms = ((first_t[0] - start_t) * 1000.0) if first_t[0] else total_ms
        print(f"QUERY {i} complete in {total_ms:.1f}ms (first token: {first_ms:.1f}ms)")
        print(f"Response: '{resp.strip()}'", flush=True)

if __name__ == "__main__":
    test()
