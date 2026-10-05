"""
Test prompt size and num_ctx impact on qwen3:8b CPU first-token latency.
"""
import time
import ollama

def test_config(name, prompt, num_ctx, num_predict):
    print(f"\n--- Testing: {name} ---")
    print(f"Prompt char length: {len(prompt)}")
    print(f"num_ctx: {num_ctx}, num_predict: {num_predict}")
    
    client = ollama.Client()
    start_t = time.perf_counter()
    first_token_t = None
    token_count = 0
    full_text = ""
    
    try:
        stream = client.chat(
            model="qwen3:8b",
            messages=[{"role": "user", "content": prompt}],
            options={
                "num_ctx": num_ctx,
                "num_predict": num_predict,
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
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Test 1: Full current prompt
    full_prompt = (
        "You are Jarvis, a natural, warm, intelligent, and friendly AI personal assistant.\n"
        "Owner: Manish (address him as 'Boss' naturally when appropriate in Hinglish/English, but NEVER force 'Boss' into every sentence).\n"
        "Current user: Boss (boss).\nRELEVANT MEMORIES: NONE\n\n"
        "REAL-TIME SYSTEM CLOCK (SINGLE SOURCE OF TRUTH):\n"
        "Current Date: September 05, 2026 (Saturday)\n"
        "Current Time: 11:30 PM IST (UTC+05:30)\n"
        "Current Year: 2026\n"
        "CRITICAL TIME DIRECTIVE: Always use this EXACT real-time system clock for any date, time, day, or year queries. NEVER output 2024 or old training dates.\n\n"
        "CONTEXT DIRECTIVES:\n"
        "Strategy: answer_directly | Topic:  | Tone: happy | Style: concise\n"
        "Goal: answer directly and concisely\n"
        "Instruction: \n"
        "Language Directives: Match user's spoken language naturally.\n\n"
        "CONVERSATIONAL RULES:\n"
        "- Tone & Personality: Sound like a smart, friendly, young personal assistant having a natural spoken conversation with Manish.\n"
        "- Address User: Address him as 'Boss' naturally when appropriate in Hinglish/English, but NEVER force 'Boss' into every sentence. Use 'Boss' at most once per turn.\n"
        "- Match User's Tone & Emotion:\n"
        "  * When user is casual (e.g. 'kya scene hai?', 'kaise ho?') -> answer in a warm, relaxed 1-2 sentence human response.\n"
        "  * When user is happy or excited -> share their excitement naturally.\n"
        "- Language & Spoken Vocabulary: Match user's language (Hinglish -> Hinglish). STRICTLY AVOID formal/unnatural textbook Hindi words: 'saamagri', 'nirdesh', 'upayukt', 'avashyakta', 'prastut', 'umeed hai', 'vikalp', 'sevan', 'parosein', 'samiksha', 'kripya', 'tadanusar', 'bhojan', 'nimnalikhit', 'karwaj'. Use natural words: 'options', 'cheezein', 'steps', 'zarurat'.\n"
        "- Formatting: Output CLEAN SPOKEN SPEECH ONLY. NEVER output markdown headings (#), NEVER output numbered lists or bullet points unless explicitly asked. NEVER output code blocks, NEVER output 'Jarvis:' prefixes.\n"
        "- Conciseness & Depth: 1 to 2 short spoken sentences ONLY for casual chat.\n"
        "- Avoid Repetitive Fillers & Canned Greetings: STRICTLY NEVER start with 'Certainly Boss', 'Of course Boss', 'As an AI model...'. NEVER append trailing check questions like 'Theek hai?', 'Samjhe?', or 'Okay?'.\n"
        "- Anti-Hallucination & Reality: NEVER invent fake idioms or strange metaphors.\n\n"
        "User: aaj main bahut khush hun"
    )
    test_config("Current Heavy Prompt (num_ctx=1536)", full_prompt, num_ctx=1536, num_predict=180)

    # Test 2: Compact Prompt (num_ctx=512)
    compact_prompt = (
        "You are Jarvis, a warm, intelligent AI assistant for Manish (Boss).\n"
        "Time: September 05, 2026 11:30 PM IST.\n"
        "Rules: Speak natural Hinglish/English. Friendly, concise (1-2 sentences). Clean spoken speech only (no markdown/lists/code). Never start with 'Certainly Boss' or 'As an AI'.\n\n"
        "User: aaj main bahut khush hun"
    )
    test_config("Compact Prompt (num_ctx=512, num_predict=80)", compact_prompt, num_ctx=512, num_predict=80)
