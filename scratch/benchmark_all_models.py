import time
import ollama

models_to_test = ["qwen3:8b", "qwen3:4b-instruct", "phi4-mini:latest", "llama3.2:latest"]

for model in models_to_test:
    print(f"\n==========================================")
    print(f"Testing model: {model}")
    print(f"==========================================")
    client = ollama.Client()
    start_t = time.perf_counter()
    first_token_t = None
    full_text = ""
    chunk_count = 0

    try:
        stream = client.chat(
            model=model,
            messages=[{"role": "user", "content": "hello jarvis"}],
            options={"num_ctx": 512, "num_predict": 80},
            keep_alive=-1,
            stream=True
        )
        for chunk in stream:
            if first_token_t is None:
                first_token_t = time.perf_counter()
            chunk_count += 1
            content = chunk.get("message", {}).get("content", "")
            full_text += content

        total_t = time.perf_counter()
        first_token_latency = (first_token_t - start_t) * 1000.0 if first_token_t else 0.0
        total_latency = (total_t - start_t) * 1000.0

        print(f"[{model}] First Token Latency: {first_token_latency:.1f} ms ({first_token_latency/1000.0:.2f} s)")
        print(f"[{model}] Total Time:         {total_latency:.1f} ms ({total_latency/1000.0:.2f} s)")
        print(f"[{model}] Response: {full_text.strip()[:100]}")
    except Exception as e:
        print(f"[{model}] Error: {e}")
