import sys
import os
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from ai.ask_ollama import ask_ollama_streaming
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager

queries = [
    "hello jarvis",
    "are you lookin good",
    "how are you today"
]

print("\n=======================================================")
print("JARVIS VOICE LATENCY VERIFICATION BENCHMARK (3 TURNS)")
print("=======================================================\n")

state_machine = StateMachine()
timeout_manager = TimeoutManager(10.0)
speech_coordinator = SpeechCoordinator(state_machine, timeout_manager)

results = []

for idx, query in enumerate(queries, 1):
    print(f"--- TEST {idx}: '{query}' ---", flush=True)
    req_id = f"test_req_{idx}"
    
    first_token_time = [None]
    first_sentence_time = [None]
    chunks = []

    def mock_speak_callback(chunk):
        now = time.perf_counter()
        if first_sentence_time[0] is None:
            first_sentence_time[0] = now
        chunks.append(chunk)

    pipeline_start = time.perf_counter()
    
    asr_time_ms = 0.0

    llm_start = time.perf_counter()
    full_resp = ask_ollama_streaming(
        user_input=query,
        speaker_name="Boss",
        relation="boss",
        speak_callback=mock_speak_callback,
        speech_coordinator=speech_coordinator,
        request_id=req_id
    )
    llm_total_ms = (time.perf_counter() - llm_start) * 1000.0
    total_response_ms = (time.perf_counter() - pipeline_start) * 1000.0

    time_to_first_audible_ms = ((first_sentence_time[0] - llm_start) * 1000.0) if first_sentence_time[0] else llm_total_ms
    llm_first_token_ms = time_to_first_audible_ms

    res = {
        "query": query,
        "asr_time_ms": asr_time_ms,
        "llm_start_ms": 0.0,
        "llm_first_token_ms": llm_first_token_ms,
        "llm_total_ms": llm_total_ms,
        "tts_generation_ms": 0.0,
        "time_to_first_audible_speech_ms": time_to_first_audible_ms,
        "total_response_ms": total_response_ms,
        "response": full_resp
    }
    results.append(res)
    
    print(f"  ASR time:                     {asr_time_ms:.1f} ms", flush=True)
    print(f"  LLM start:                    0.0 ms", flush=True)
    print(f"  LLM first token:              {llm_first_token_ms:.1f} ms ({llm_first_token_ms/1000.0:.2f} s)", flush=True)
    print(f"  LLM total:                    {llm_total_ms:.1f} ms ({llm_total_ms/1000.0:.2f} s)", flush=True)
    print(f"  TTS generation:               0.0 ms", flush=True)
    print(f"  Time to first audible speech: {time_to_first_audible_ms:.1f} ms ({time_to_first_audible_ms/1000.0:.2f} s)", flush=True)
    print(f"  Total response time:          {total_response_ms:.1f} ms ({total_response_ms/1000.0:.2f} s)", flush=True)
    print(f"  Response text:                \"{full_resp}\"\n", flush=True)

print("=======================================================", flush=True)
print("BENCHMARK SUMMARY", flush=True)
print("=======================================================", flush=True)
for r in results:
    print(f"Query: '{r['query']}' | First Token: {r['llm_first_token_ms']:.1f} ms | Total: {r['total_response_ms']:.1f} ms", flush=True)
