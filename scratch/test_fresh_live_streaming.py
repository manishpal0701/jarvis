import os
import sys
sys.path.insert(0, os.path.abspath("."))
import time

def test_query(prompt: str, req_id: str):
    print(f"\n==================================================", flush=True)
    print(f"TESTING PROMPT: '{prompt}'", flush=True)
    print(f"==================================================", flush=True)
    from conversation.command_router import route_command
    from conversation.conversation_engine import ConversationEngine

    engine = ConversationEngine()
    
    t0 = time.time()
    res = route_command(prompt, source="voice", sync_execution=True, request_id=req_id)
    t1 = time.time()

    print(f"\n[LIVE_TEST_SUMMARY] prompt='{prompt}' duration={t1-t0:.2f}s res={res}", flush=True)

def main():
    test_query("Jarvis, explain Python in three sentences in simple Hinglish.", "req_fresh_hinglish_101")
    test_query("Jarvis, what is 2 plus 2?", "req_fresh_math_102")

if __name__ == "__main__":
    main()
