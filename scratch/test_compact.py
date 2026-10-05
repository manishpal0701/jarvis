"""
Direct test for compact prompt on qwen3:8b
"""
import time
import ollama

def test():
    compact_prompt = (
        "You are Jarvis, a warm, intelligent AI assistant for Manish (Boss).\n"
        "Time: September 05, 2026 11:30 PM IST.\n"
        "Rules: Speak natural Hinglish/English. Friendly, concise (1-2 sentences). Clean spoken speech only (no markdown/lists/code). Never start with 'Certainly Boss' or 'As an AI'.\n\n"
        "User: aaj main bahut khush hun"
    )
    print(f"Compact prompt char length: {len(compact_prompt)}")
    
    client = ollama.Client()
    start_t = time.perf_counter()
    first_token_t = None
    token_count = 0
    full_text = ""
    
    stream = client.chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": compact_prompt}],
        options={
            "num_ctx": 512,
            "num_predict": 80,
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
