import time
import ollama

def test_direct_ollama(model="qwen3:8b", prompt="hello jarvis", options=None, think=False):
    client = ollama.Client()
    messages = [{"role": "user", "content": prompt}]
    start_t = time.perf_counter()
    first_token_t = None
    full_text = ""

    kwargs = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": -1
    }
    if options:
        kwargs["options"] = options
    if think is not None:
        kwargs["think"] = think

    print(f"\n--- Testing DIRECT Ollama stream ---")
    print(f"Model: {model}")
    print(f"Prompt: '{prompt}'")
    print(f"Kwargs: {kwargs}")

    stream = client.chat(**kwargs)
    chunk_count = 0
    for chunk in stream:
        if first_token_t is None:
            first_token_t = time.perf_counter()
        chunk_count += 1
        content = chunk.get("message", {}).get("content", "")
        full_text += content
        if chunk_count <= 5:
            print(f"  Chunk {chunk_count}: '{content}'")

    total_t = time.perf_counter()
    first_token_latency = (first_token_t - start_t) * 1000.0 if first_token_t else 0.0
    total_latency = (total_t - start_t) * 1000.0

    print(f"First Token Latency: {first_token_latency:.1f} ms ({first_token_latency/1000.0:.2f} s)")
    print(f"Total Time: {total_latency:.1f} ms ({total_latency/1000.0:.2f} s)")
    print(f"Response: '{full_text.strip()}'")
    return first_token_latency, total_latency

if __name__ == "__main__":
    # Test 1: Simple direct request with no options
    print("=== TEST 1: Direct Ollama simple prompt ===")
    test_direct_ollama(model="qwen3:8b", prompt="hello jarvis")

    # Test 2: Direct request with CONVERSATION_OPTIONS (num_ctx=512, num_predict=80)
    print("\n=== TEST 2: Direct Ollama with num_ctx=512, num_predict=80 ===")
    test_direct_ollama(model="qwen3:8b", prompt="hello jarvis", options={"num_ctx": 512, "num_predict": 80}, think=False)
