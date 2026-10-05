import traceback
import sys

try:
    from ai.ask_ollama import ask_ollama_streaming
    print("Starting ask_ollama_streaming test...", flush=True)
    res = ask_ollama_streaming("hello jarvis", "Boss", "boss", request_id="diag_req_1")
    print(f"Result: '{res}'", flush=True)
except Exception as e:
    print(f"EXCEPTION OCCURRED: {e}", flush=True)
    traceback.print_exc()
