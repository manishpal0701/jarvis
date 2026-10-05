import os
import sys
sys.path.insert(0, os.path.abspath("."))
import time
import logging

logging.basicConfig(level=logging.DEBUG)

def main():
    print("=== TESTING OLLAMA STREAMING DIAGNOSTICS ===", flush=True)
    from ai.ai_response_manager import AIResponseManager, CONVERSATION_OPTIONS, MODEL_NAME
    
    ai = AIResponseManager()
    
    messages = [
        {"role": "system", "content": "You are JARVIS, a helpful female AI assistant."},
        {"role": "user", "content": "Jarvis, what is 2 plus 2?"}
    ]
    
    print("[STREAM_DEBUG] starting generate_response_streaming call...", flush=True)
    chunks_received = []
    def dummy_callback(chunk):
        print(f"[STREAM_DEBUG] sentence_callback called with chunk: '{chunk}'", flush=True)
        chunks_received.append(chunk)

    try:
        t0 = time.time()
        res = ai.generate_response_streaming(
            messages=messages,
            sentence_callback=dummy_callback,
            keep_alive=-1,
            options=CONVERSATION_OPTIONS,
            think=False,
            timeout=45.0
        )
        t1 = time.time()
        print(f"[STREAM_DEBUG] generate_response_streaming returned in {t1-t0:.2f}s", flush=True)
        print(f"[STREAM_DEBUG] total chunks received={len(chunks_received)} full_res='{res}'", flush=True)
    except Exception as e:
        print(f"[STREAM_DEBUG] EXCEPTION in generate_response_streaming: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
