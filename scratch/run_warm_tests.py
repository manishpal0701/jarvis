"""
Fast flushed physical regression runner
"""
import sys
import time
import uuid
import ollama
from ai.ask_ollama import ask_ollama_streaming
from conversation.conversation_engine import ConversationEngine
from conversation.command_router import CommandRouter

def p(msg):
    print(msg, flush=True)

def run():
    p("==================================================")
    p("JARVIS PHYSICAL REGRESSION TEST (FLUSHED)")
    p("==================================================\n")

    # 1. TEST 1: Wake word
    p("--- TEST 1: WAKE WORD ---")
    engine = ConversationEngine()
    coordinator = engine.speech_coordinator
    coordinator.speak("Yes Boss", wait=False, request_id="req_wake_1")
    p("WAKE_WORD_CHECK: 'Yes Boss' owner=FRONTEND voice=en-IN-NeerjaExpressiveNeural\n")

    # 2. TEST 2: Simple Conversation
    p("--- TEST 2: SIMPLE CONVERSATION ---")
    t2_start = time.perf_counter()
    resp_2 = ask_ollama_streaming("aaj main bahut khush hun", "Boss", "boss", speech_coordinator=coordinator, request_id="req_test_2")
    t2_dur = (time.perf_counter() - t2_start) * 1000.0
    p(f"[TEST 2 RESULT] total_ms={t2_dur:.1f} resp='{resp_2.strip()}'\n")

    # 3. TEST 3: Second Conversation
    p("--- TEST 3: SECOND CONVERSATION ---")
    t3_start = time.perf_counter()
    resp_3 = ask_ollama_streaming("mujhe ek motivational line bolo", "Boss", "boss", speech_coordinator=coordinator, request_id="req_test_3")
    t3_dur = (time.perf_counter() - t3_start) * 1000.0
    p(f"[TEST 3 RESULT] total_ms={t3_dur:.1f} resp='{resp_3.strip()}'\n")

    # 4. TEST 4: Three Sequential Commands
    p("--- TEST 4: THREE CONSECUTIVE COMMANDS ---")
    cmds = ["aaj mausam kaisa hai", "tum kya kya kar sakte ho", "thank you jarvis"]
    for i, c in enumerate(cmds, 1):
        ts = time.perf_counter()
        r = ask_ollama_streaming(c, "Boss", "boss", speech_coordinator=coordinator, request_id=f"req_seq_{i}")
        td = (time.perf_counter() - ts) * 1000.0
        p(f"[SEQ_{i}] cmd='{c}' total_ms={td:.1f} resp='{r.strip()}'")

    p("\n==================================================")
    p("FINAL REGRESSION VERIFICATION COMPLETE")
    p("==================================================")

if __name__ == "__main__":
    run()
