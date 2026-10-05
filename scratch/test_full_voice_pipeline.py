import os
import sys
sys.path.insert(0, os.path.abspath("."))
import time

def main():
    print("=== TESTING FULL VOICE PIPELINE ROUTING ===", flush=True)
    from conversation.command_router import route_command
    from conversation.conversation_engine import ConversationEngine

    engine = ConversationEngine()
    print(f"[TEST_TRACE] ConversationEngine instance: {engine}", flush=True)
    print(f"[TEST_TRACE] speech_coordinator: {engine.speech_coordinator}", flush=True)

    t0 = time.time()
    res = route_command("Jarvis, what is 2 plus 2?", source="voice", sync_execution=True, request_id="req_test_diag_1")
    t1 = time.time()

    print(f"[TEST_TRACE] route_command returned in {t1-t0:.2f}s", flush=True)
    print(f"[TEST_TRACE] result: {res}", flush=True)

if __name__ == "__main__":
    main()
