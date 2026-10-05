import time
import ollama

def benchmark(model_name, prompt="hello jarvis"):
    print(f"\nBenchmarking {model_name}...")
    client = ollama.Client()
    start_t = time.perf_counter()
    first_token_t = None
    full_text = ""
    chunk_count = 0

    stream = client.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 512, "num_predict": 80},
        keep_alive=-1,
        stream=True
    )
    for chunk in stream:
        token = chunk.get("message", {}).get("content", "")
        if token:
            if first_token_t is None:
                first_token_t = time.perf_counter()
            chunk_count += 1
            full_text += token

    end_t = time.perf_counter()
    ft_latency = (first_token_t - start_t) * 1000.0 if first_token_t else 0.0
    tot_latency = (end_t - start_t) * 1000.0
    print(f"Model: {model_name}")
    print(f"First Token Latency: {ft_latency:.1f} ms ({ft_latency/1000.0:.2f} s)")
    print(f"Total Time:          {tot_latency:.1f} ms ({tot_latency/1000.0:.2f} s)")
    print(f"Response: {full_text.strip()}")

if __name__ == "__main__":
    benchmark("qwen3:4b-instruct", "hello jarvis")
    benchmark("qwen3:4b-instruct", "are you lookin good")
