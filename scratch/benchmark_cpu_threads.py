"""
scratch/benchmark_cpu_threads.py
Benchmarks Ollama CPU num_thread (1, 2, 4, 6, 8) using qwen3:4b-instruct.
Measures TTFT, Prompt Eval time, Eval time, and Tokens/sec.
"""

import sys
sys.path.insert(0, ".")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b-instruct"
THREAD_COUNTS = [1, 2, 4, 6, 8]

PROMPT_TEXT = "Hello Jarvis, good morning! How are you doing today?"

def run_thread_benchmark():
    print("=================================================================", flush=True)
    print("OLLAMA CPU THREAD BENCHMARK (num_thread = 1, 2, 4, 6, 8)", flush=True)
    print("=================================================================\n", flush=True)

    results = []

    for threads in THREAD_COUNTS:
        print(f"--- Testing num_thread = {threads} ---", flush=True)
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are Jarvis, a warm female Indian AI assistant. Keep responses under 2 sentences in natural Hinglish."},
                {"role": "user", "content": PROMPT_TEXT}
            ],
            "options": {
                "num_ctx": 512,
                "num_predict": 80,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_thread": threads
            },
            "stream": True,
            "keep_alive": -1
        }

        start_t = time.perf_counter()
        first_token_t = None
        full_text = ""
        eval_count = 0
        prompt_eval_count = 0
        prompt_eval_duration_ns = 0
        eval_duration_ns = 0

        try:
            res = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
            for line in res.iter_lines():
                if not line:
                    continue
                data = json.loads(line.decode("utf-8"))
                if "message" in data and "content" in data["message"]:
                    content = data["message"]["content"]
                    if content and first_token_t is None:
                        first_token_t = time.perf_counter()
                    full_text += content
                if data.get("done", False):
                    eval_count = data.get("eval_count", 0)
                    prompt_eval_count = data.get("prompt_eval_count", 0)
                    prompt_eval_duration_ns = data.get("prompt_eval_duration", 0)
                    eval_duration_ns = data.get("eval_duration", 0)

            total_dur_ms = (time.perf_counter() - start_t) * 1000.0
            ttft_ms = (first_token_t - start_t) * 1000.0 if first_token_t else total_dur_ms
            prompt_eval_ms = prompt_eval_duration_ns / 1e6
            eval_ms = eval_duration_ns / 1e6
            tok_per_sec = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else 0.0

            print(f"  Response: \"{full_text.strip()}\"", flush=True)
            print(f"  TTFT: {ttft_ms:.1f} ms | Prompt Eval: {prompt_eval_ms:.1f} ms ({prompt_eval_count} tok) | Eval: {eval_ms:.1f} ms ({eval_count} tok) | Speed: {tok_per_sec:.2f} tok/s | Total: {total_dur_ms:.1f} ms\n", flush=True)
            
            results.append({
                "threads": threads,
                "ttft_ms": ttft_ms,
                "prompt_eval_ms": prompt_eval_ms,
                "eval_ms": eval_ms,
                "tok_per_sec": tok_per_sec,
                "total_ms": total_dur_ms
            })

        except Exception as e:
            print(f"  ERROR testing threads={threads}: {e}\n", flush=True)

    print("=================================================================", flush=True)
    print("CPU THREAD BENCHMARK SUMMARY TABLE", flush=True)
    print("=================================================================", flush=True)
    print(f"{'Threads':<10} | {'TTFT (ms)':<12} | {'Prompt Eval (ms)':<18} | {'Eval Speed (tok/s)':<20} | {'Total (ms)':<12}")
    print("-" * 75)
    for r in results:
        print(f"{r['threads']:<10} | {r['ttft_ms']:<12.1f} | {r['prompt_eval_ms']:<18.1f} | {r['tok_per_sec']:<20.2f} | {r['total_ms']:<12.1f}")

if __name__ == "__main__":
    run_thread_benchmark()
