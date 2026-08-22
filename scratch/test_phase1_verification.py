import sys
import os
import time
import io

# Ensure UTF-8 unbuffered output encoding for Windows console (handles emojis cleanly)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import speech
speech.initialize()

from main import is_coding_task, processCommand
from ai.ask_ollama import ask_ollama, ask_ollama_streaming
from conversation.intelligence.language_analyzer import LanguageAnalyzer
from memory.memory_manager import MemoryManager
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager

suite_start_time = time.time()
print("==================================================")
print("RUNNING PHASE 1 VERIFICATION TEST SUITE")
print("==================================================")

results = {}

forbidden_words = ["saamagri", "nirdesh", "upayukt", "avashyakta", "prastut", "umeed hai", "vikalp", "sevan", "parosein", "samiksha", "kripya", "tadanusar", "bhojan", "nimnalikhit"]

# --------------------------------------------------
# TEST 1: "mujhe bhookh lag rahi hai kya karun"
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 1 ---")
cmd1 = "mujhe bhookh lag rahi hai kya karun"
is_code1 = is_coding_task(cmd1)
resp1 = ask_ollama(cmd1, "Manish", "owner")
print(f"Command: {cmd1}")
print(f"is_coding_task: {is_code1}")
print(f"Response:\n{resp1}")
has_formal_hindi1 = any(w in resp1.lower() for w in forbidden_words)
results["TEST 1"] = not is_code1 and not has_formal_hindi1 and len(resp1) > 5
print(f"[TEST 1 DONE in {time.time()-t0:.2f}s]")

# --------------------------------------------------
# TEST 2: "han mujhe khana khana hai kya khaun"
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 2 ---")
cmd2 = "han mujhe khana khana hai kya khaun"
is_code2 = is_coding_task(cmd2)
resp2 = ask_ollama(cmd2, "Manish", "owner")
print(f"Command: {cmd2}")
print(f"is_coding_task: {is_code2}")
print(f"Response:\n{resp2}")
has_formal_hindi2 = any(w in resp2.lower() for w in forbidden_words)
results["TEST 2"] = not is_code2 and not has_formal_hindi2 and len(resp2) > 5
print(f"[TEST 2 DONE in {time.time()-t0:.2f}s]")

# --------------------------------------------------
# TEST 3: "mujhe maggi ki recipe batao"
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 3 ---")
cmd3 = "mujhe maggi ki recipe batao"
is_code3 = is_coding_task(cmd3)
resp3 = ask_ollama(cmd3, "Manish", "owner")
print(f"Command: {cmd3}")
print(f"is_coding_task: {is_code3}")
print(f"Response:\n{resp3}")
has_formal_hindi3 = any(w in resp3.lower() for w in forbidden_words)
has_numbered_list3 = bool(resp3.startswith("1.") or "\n1." in resp3 or "\n2." in resp3)
results["TEST 3"] = not is_code3 and not has_formal_hindi3 and not has_numbered_list3
print(f"[TEST 3 DONE in {time.time()-t0:.2f}s]")

# --------------------------------------------------
# TEST 4: "yaar mera code baar baar error de raha hai"
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 4 ---")
cmd4 = "yaar mera code baar baar error de raha hai"
is_code4 = is_coding_task(cmd4)
resp4 = ask_ollama(cmd4, "Manish", "owner")
print(f"Command: {cmd4}")
print(f"is_coding_task: {is_code4} (Must be False!)")
print(f"Response:\n{resp4}")
results["TEST 4"] = (is_code4 == False) and len(resp4) > 5
print(f"[TEST 4 DONE in {time.time()-t0:.2f}s]")

# --------------------------------------------------
# TEST 5: "write a poem for me"
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 5 ---")
cmd5 = "write a poem for me"
is_code5 = is_coding_task(cmd5)
resp5 = ask_ollama(cmd5, "Manish", "owner")
print(f"Command: {cmd5}")
print(f"is_coding_task: {is_code5} (Must be False!)")
print(f"Response:\n{resp5}")
results["TEST 5"] = (is_code5 == False) and len(resp5) > 5
print(f"[TEST 5 DONE in {time.time()-t0:.2f}s]")

# --------------------------------------------------
# TEST 6: "write a Python program that prints hello"
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 6 ---")
cmd6 = "write a Python program that prints hello"
is_code6 = is_coding_task(cmd6)
print(f"Command: {cmd6}")
print(f"is_coding_task: {is_code6} (Must be True!)")
results["TEST 6"] = (is_code6 == True)
print(f"[TEST 6 DONE in {time.time()-t0:.2f}s]")

# --------------------------------------------------
# TEST 7: "what is my current project?"
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 7 ---")
cmd7 = "what is my current project?"
resp7 = ask_ollama(cmd7, "Manish", "owner")
print(f"Command: {cmd7}")
print(f"Response:\n{resp7}")
results["TEST 7"] = "jarvis" in resp7.lower()
print(f"[TEST 7 DONE in {time.time()-t0:.2f}s]")

# --------------------------------------------------
# TEST 8: State Machine & Speech Lock Test
# --------------------------------------------------
t0 = time.time()
print("\n--- RUNNING TEST 8 ---")
sm = StateMachine()
sm._state = State.PROCESSING
tm = TimeoutManager()
sc = SpeechCoordinator(sm, tm)

state_log = []
def log_state():
    state_log.append(sm.state)

sc.begin_speech_session()
log_state()
print(f"Initial streaming state: {sm.state}")

# Simulate 3 streaming sentence chunks without real audio locks
sc.speak_chunk("Sentence one of response", wait=False)
log_state()
print(f"During chunk 1 state: {sm.state}")

sc.speak_chunk("Sentence two of response", wait=False)
log_state()
print(f"During chunk 2 state: {sm.state}")

sc.speak_chunk("Sentence three of response", wait=False)
log_state()
print(f"During chunk 3 state: {sm.state}")

sc.end_speech_session()
log_state()
print(f"After end_speech_session state: {sm.state}")

waiting_during_stream = any(s == State.WAITING_FOR_NEXT_COMMAND for s in state_log[:-1])
final_is_waiting = (state_log[-1] == State.WAITING_FOR_NEXT_COMMAND)

results["TEST 8"] = (not waiting_during_stream) and final_is_waiting
print(f"[TEST 8 DONE in {time.time()-t0:.2f}s]")

total_suite_time = time.time() - suite_start_time

print("\n==================================================")
print("TEST RESULTS SUMMARY")
print("==================================================")
all_passed = True
for test_name, passed in results.items():
    status = "PASSED" if passed else "FAILED"
    print(f"{test_name}: {status}")
    if not passed:
        all_passed = False

print(f"\nALL TESTS PASSED: {all_passed}")
print(f"TOTAL SUITE EXECUTION TIME: {total_suite_time:.2f} seconds")

# Clean up speech engine background threads
speech.shutdown()
