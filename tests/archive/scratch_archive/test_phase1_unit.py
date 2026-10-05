import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import is_coding_task
from conversation.intelligence.language_analyzer import LanguageAnalyzer
from memory.memory_manager import MemoryManager
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager

print("==================================================")
print("RUNNING INSTANT UNIT TESTS FOR PHASE 1")
print("==================================================")

# 1. COMMAND ROUTING TESTS
print("\n--- 1. TESTING COMMAND ROUTING (is_coding_task) ---")
test_cases = [
    ("mujhe bhookh lag rahi hai kya karun", False),
    ("han mujhe khana khana hai kya khaun", False),
    ("mujhe maggi ki recipe batao", False),
    ("yaar mera code baar baar error de raha hai", False),
    ("write a poem for me", False),
    ("create a joke", False),
    ("build a story", False),
    ("generate an idea", False),
    ("what should I build?", False),
    ("create something funny", False),
    ("write a Python program that prints hello", True),
    ("fix this Python code", True),
    ("create a Flutter app", True),
    ("build a website", True),
    ("write JavaScript for this", True),
    ("debug my code", True),
]

routing_passed = True
for cmd, expected in test_cases:
    res = is_coding_task(cmd)
    match = (res == expected)
    if not match:
        routing_passed = False
    print(f"  ['{cmd}'] -> Detected: {res} | Expected: {expected} | {'OK' if match else 'FAIL'}")

# 2. LANGUAGE ANALYZER TESTS
print("\n--- 2. TESTING LANGUAGE ANALYZER ---")
analyzer = LanguageAnalyzer()
intel1 = analyzer.analyze("mujhe bhookh lag rahi hai")
print(f"  Language instruction: {intel1.get('instruction')[:80]}...")
has_forbidden = any(w in intel1.get('instruction').lower() for w in ["saamagri", "nirdesh", "upayukt"])

# 3. MEMORY RETRIEVAL TEST
print("\n--- 3. TESTING MEMORY GROUNDING ---")
mem_mgr = MemoryManager()
mems = mem_mgr.retrieve_relevant("what is my current project?", limit=3, min_score=1.0)
print(f"  Retrieved memories for 'current project': {[m.get('content') for m in mems]}")
has_jarvis = any("Jarvis AI" in m.get("content", "") for m in mems)

# 4. SPEECH STATE MACHINE & LOCK TEST
print("\n--- 4. TESTING SPEECH STATE MACHINE LOCKS ---")
sm = StateMachine()
tm = TimeoutManager()
sc = SpeechCoordinator(sm, tm)

state_sequence = []
sc.begin_speech_session()
state_sequence.append(sm.state)

sc.speak_chunk("Sentence one", wait=False)
state_sequence.append(sm.state)

sc.speak_chunk("Sentence two", wait=False)
state_sequence.append(sm.state)

sc.end_speech_session()
state_sequence.append(sm.state)

print(f"  State sequence: {[s.name for s in state_sequence]}")
no_premature_waiting = not any(s == State.WAITING_FOR_NEXT_COMMAND for s in state_sequence[:-1])
final_waiting = (state_sequence[-1] == State.WAITING_FOR_NEXT_COMMAND)

print("\n==================================================")
print("UNIT TEST RESULTS SUMMARY")
print("==================================================")
print(f"Command Routing Tests: {'PASSED' if routing_passed else 'FAILED'}")
print(f"Language Analyzer Rules: {'PASSED' if not has_forbidden else 'FAILED'}")
print(f"Memory Grounding Match: {'PASSED' if has_jarvis else 'FAILED'}")
print(f"Speech State Machine Lock: {'PASSED' if (no_premature_waiting and final_waiting) else 'FAILED'}")

all_unit_passed = routing_passed and not has_forbidden and has_jarvis and no_premature_waiting and final_waiting
print(f"\nALL UNIT TESTS PASSED: {all_unit_passed}")
