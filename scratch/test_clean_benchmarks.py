import time
import ollama

def test_model(model_name):
    print(f"\n==========================================")
    print(f"Testing model: {model_name}")
    print(f"==========================================")
    client = ollama.Client()
    start_t = time.perf_counter()
    first_token_t = None
    full_text = ""
    chunk_count = 0

    try:
        stream = client.chat(
            model=model_name,
            messages=[{"role": "user", "content": "hello jarvis"}],
            options={"num_ctx": 512, "num_predict": 80},
            keep_alive=-1,
            stream=True
        )
        for chunk in stream:
            chunk_content = chunk.get("message", {}).get("content", "")
            if chunk_content:
                if first_token_t is None:
                    first_token_t = time.perf_counter()
                chunk_count += 1
                full_text += chunk_content

        total_t = time.perf_counter()
        first_token_latency = (first_token_t - start_t) * 1000.0 if first_token_t else 0.0
        total_latency = (total_t - start_t) * 1000.0

        print(f"[{model_name}] First Token Latency: {first_token_latency:.1f} ms ({first_token_latency/1000.0:.2f} s)")
        print(f"[{model_name}] Total Time:         {total_latency:.1f} ms ({total_latency/1000.0:.2f} s)")
        print(f"[{model_name}] Chunks:             {chunk_count}")
        print(f"[{model_name}] Response: {full_text.strip()[:100]}")
    except Exception as e:
        print(f"[{model_name}] Error: {e}")

if __name__ == "__main__":
    for m in ["qwen3:4b-instruct", "phi4-mini:latest", "llama3.2:latest", "qwen3:8b"]:
        test_model(m)
