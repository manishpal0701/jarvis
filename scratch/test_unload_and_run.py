"""
Test unloading extra models and benchmarking qwen3:8b
"""
import time
import ollama

def test():
    client = ollama.Client()
    
    # 1. Unload qwen3:4b-instruct to free CPU RAM & L3 cache
    print("Unloading qwen3:4b-instruct...")
    try:
        client.chat(model="qwen3:4b-instruct", messages=[], keep_alive=0)
    except Exception:
        pass
    
    # 2. Test qwen3:8b with num_ctx=512 and compact prompt
    compact_prompt = (
        "You are Jarvis, a warm, intelligent AI assistant for Manish (Boss).\n"
        "Time: September 05, 2026 11:30 PM IST.\n"
        "Rules: Speak natural Hinglish/English. Friendly, concise (1-2 sentences). Clean spoken speech only (no markdown/lists/code). Never start with 'Certainly Boss' or 'As an AI'.\n\n"
        "User: aaj main bahut khush hun"
    )
    
    print("\nPrewarming qwen3:8b with num_ctx=512...")
    start_warm = time.perf_counter()
    client.chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": "hi"}],
        options={"num_ctx": 512, "num_predict": 5},
        think=False,
        keep_alive=-1
    )
    warm_ms = (time.perf_counter() - start_warm) * 1000.0
    print(f"Prewarm time: {warm_ms:.1f}ms")
    
    print("\nRunning actual request...")
    start_t = time.perf_counter()
    first_token_t = None
    token_count = 0
    full_text = ""
    
    stream = client.chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": compact_prompt}],
        options={
            "num_ctx": 512,
            "num_predict": 60,
            "temperature": 0.7,
            "top_p": 0.9
        },
        stream=True,
        think=False,
        keep_alive=-1
    )
    for chunk in stream:
        curr_t = time.perf_counter()
        token = chunk.get("message", {}).get("content", "")
        if token:
            if first_token_t is None:
                first_token_t = curr_t
                first_ms = (first_token_t - start_t) * 1000.0
                print(f"FIRST TOKEN LATENCY: {first_ms:.1f} ms")
            token_count += 1
            full_text += token
    
    total_ms = (time.perf_counter() - start_t) * 1000.0
    print(f"TOTAL TIME: {total_ms:.1f} ms ({token_count} tokens)")
    print(f"OUTPUT: '{full_text.strip()}'")

if __name__ == "__main__":
    test()
