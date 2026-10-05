import sys
import os
import time
import json
import urllib.request
import psutil
from datetime import datetime

# Enforce UTF-8 output encoding for Windows stdout/stderr
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

import ollama

def get_ollama_ps():
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/ps", timeout=2.0)
        data = json.loads(req.read())
        return data.get("models", [])
    except Exception as e:
        return []

def get_telemetry():
    vmem = psutil.virtual_memory()
    sys_cpu = psutil.cpu_percent(interval=0.1)
    ollama_cpu = 0.0
    ollama_ram_mb = 0.0
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
        try:
            if 'ollama' in proc.info['name'].lower():
                ollama_cpu = proc.info['cpu_percent']
                ollama_ram_mb = proc.info['memory_info'].rss / (1024 * 1024)
                break
        except Exception:
            pass
    return {
        "sys_cpu": sys_cpu,
        "vmem_avail_mb": vmem.available / (1024 * 1024),
        "vmem_percent": vmem.percent,
        "ollama_cpu": ollama_cpu,
        "ollama_ram_mb": ollama_ram_mb
    }

prompt = "Jarvis, what is Python?"
model_name = "qwen3:4b-instruct"

thread_configs = [
    ("Default (Auto)", None),
    ("num_thread = 2", 2),
    ("num_thread = 4", 4),
    ("num_thread = 6", 6),
    ("num_thread = 8", 8),
    ("num_thread = 10", 10),
    ("num_thread = 12", 12)
]

print("=======================================================================", flush=True)
print("JARVIS PHASE 3 — CPU THREAD BENCHMARK SUITE", flush=True)
print("=======================================================================\n", flush=True)

# 1. Topology
print("CPU TOPOLOGY:", flush=True)
print(f"  Physical Cores: {psutil.cpu_count(logical=False)}", flush=True)
print(f"  Logical Cores:  {psutil.cpu_count(logical=True)}", flush=True)
print(f"  Model Target:   {model_name}\n", flush=True)

benchmark_results = {}

client = ollama.Client()

for label, num_thread in thread_configs:
    print(f"--- BENCHMARK GROUP: {label} ---", flush=True)
    
    # Check model warm state
    ps_data = get_ollama_ps()
    model_warm = len(ps_data) > 0 and ps_data[0].get("name") == model_name
    print(f"  Model Warm Check (GET /api/ps): {model_warm} | ps: {ps_data}", flush=True)

    runs = []
    for run_i in range(1, 4):
        opts = {
            "num_ctx": 512,
            "num_predict": 80,
            "temperature": 0.7,
            "top_p": 0.9
        }
        if num_thread is not None:
            opts["num_thread"] = num_thread

        tele_before = get_telemetry()
        start_t = time.perf_counter()
        first_token_t = None
        first_sentence_t = None
        full_text = ""
        prompt_tokens = 0
        output_tokens = 0
        last_chunk = None

        stream = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options=opts,
            think=False,
            keep_alive=-1,
            stream=True
        )

        for chunk in stream:
            last_chunk = chunk
            token = chunk.get("message", {}).get("content", "")
            if token:
                if first_token_t is None:
                    first_token_t = time.perf_counter()
                full_text += token
                if first_sentence_t is None and any(p in token for p in ['.', '!', '?', '\n']):
                    first_sentence_t = time.perf_counter()

        end_t = time.perf_counter()
        if first_sentence_t is None:
            first_sentence_t = end_t
        if first_token_t is None:
            first_token_t = end_t

        ft_ms = (first_token_t - start_t) * 1000.0
        fs_ms = (first_sentence_t - start_t) * 1000.0
        tot_ms = (end_t - start_t) * 1000.0

        tele_after = get_telemetry()

        if last_chunk:
            prompt_tokens = last_chunk.get("prompt_eval_count", 0)
            output_tokens = last_chunk.get("eval_count", 0)

        runs.append({
            "run": run_i,
            "first_token_ms": ft_ms,
            "first_sentence_ms": fs_ms,
            "total_ms": tot_ms,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "ram_avail_mb": tele_after["vmem_avail_mb"],
            "ollama_cpu": tele_after["ollama_cpu"],
            "ollama_ram_mb": tele_after["ollama_ram_mb"]
        })

        print(f"  Run {run_i}: First Token = {ft_ms:.1f} ms | Total = {tot_ms:.1f} ms | Tokens: in={prompt_tokens} out={output_tokens} | RAM Avail: {tele_after['vmem_avail_mb']:.0f}MB", flush=True)
        time.sleep(0.5)

    ft_list = [r["first_token_ms"] for r in runs]
    tot_list = [r["total_ms"] for r in runs]
    avg_ft = sum(ft_list) / len(ft_list)
    min_ft = min(ft_list)
    max_ft = max(ft_list)
    variance_ft = max_ft - min_ft

    benchmark_results[label] = {
        "runs": runs,
        "avg_ft": avg_ft,
        "min_ft": min_ft,
        "max_ft": max_ft,
        "variance_ft": variance_ft,
        "avg_tot": sum(tot_list) / len(tot_list)
    }

    print(f"  Group Summary [{label}]: Avg First Token = {avg_ft:.1f} ms | Min = {min_ft:.1f} ms | Max = {max_ft:.1f} ms | Variance = {variance_ft:.1f} ms\n", flush=True)

print("=======================================================================", flush=True)
print("PHASE 3 FINAL SUMMARY TABLE", flush=True)
print("=======================================================================", flush=True)
print(f"{'Thread Config':<18} | {'Run 1 (ms)':<10} | {'Run 2 (ms)':<10} | {'Run 3 (ms)':<10} | {'Average':<10} | {'Min':<10} | {'Max':<10} | {'Variance':<10}", flush=True)
print("-" * 105, flush=True)

for label, res in benchmark_results.items():
    r1 = res["runs"][0]["first_token_ms"]
    r2 = res["runs"][1]["first_token_ms"]
    r3 = res["runs"][2]["first_token_ms"]
    print(f"{label:<18} | {r1:<10.1f} | {r2:<10.1f} | {r3:<10.1f} | {res['avg_ft']:<10.1f} | {res['min_ft']:<10.1f} | {res['max_ft']:<10.1f} | {res['variance_ft']:<10.1f}", flush=True)
