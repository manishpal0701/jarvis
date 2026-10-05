"""
scratch/test_all_10_scenarios.py
Verification test script for Ollama streaming fixes across all 10 user scenarios.
"""
import sys
import time

from ai.ask_ollama import ask_ollama_streaming
from conversation.command_router import CommandRouter
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager

def run_tests():
    print("==================================================", flush=True)
    print("RUNNING ALL 10 CONVERSATION VERIFICATION SCENARIOS", flush=True)
    print("==================================================", flush=True)

    results = []

    sm = StateMachine()
    tm = TimeoutManager(timeout_seconds=10.0)
    coordinator = SpeechCoordinator(sm, tm)

    # 1. "hello jarvis"
    print("\n--- TEST 1: 'hello jarvis' ---", flush=True)
    received_chunks = []
    def cb1(chunk):
        received_chunks.append(chunk)
    r1 = ask_ollama_streaming("hello jarvis", "Boss", "boss", speak_callback=cb1, speech_coordinator=coordinator, request_id="test_req_1")
    has_trouble1 = "trouble" in r1.lower() and "ollama" in r1.lower()
    print(f"Result 1: len={len(r1)} text=\"{r1[:60]}...\" chunks={len(received_chunks)} trouble={has_trouble1}")
    results.append(("1. hello jarvis", not has_trouble1 and len(r1) > 0))

    # 2. "how are you?"
    print("\n--- TEST 2: 'how are you?' ---", flush=True)
    received_chunks = []
    def cb2(chunk):
        received_chunks.append(chunk)
    r2 = ask_ollama_streaming("how are you?", "Boss", "boss", speak_callback=cb2, speech_coordinator=coordinator, request_id="test_req_2")
    has_trouble2 = "trouble" in r2.lower() and "ollama" in r2.lower()
    print(f"Result 2: len={len(r2)} text=\"{r2[:60]}...\" chunks={len(received_chunks)} trouble={has_trouble2}")
    results.append(("2. how are you?", not has_trouble2 and len(r2) > 0))

    # 3. "what is Python?"
    print("\n--- TEST 3: 'what is Python?' ---", flush=True)
    received_chunks = []
    def cb3(chunk):
        received_chunks.append(chunk)
    r3 = ask_ollama_streaming("what is Python?", "Boss", "boss", speak_callback=cb3, speech_coordinator=coordinator, request_id="test_req_3")
    has_trouble3 = "trouble" in r3.lower() and "ollama" in r3.lower()
    print(f"Result 3: len={len(r3)} text=\"{r3[:60]}...\" chunks={len(received_chunks)} trouble={has_trouble3}")
    results.append(("3. what is Python?", not has_trouble3 and len(r3) > 0))

    # 4. Longer 3-5 sentence response
    print("\n--- TEST 4: Longer detailed question ---", flush=True)
    received_chunks = []
    def cb4(chunk):
        received_chunks.append(chunk)
    r4 = ask_ollama_streaming("Explain how artificial intelligence and machine learning work in 3 sentences.", "Boss", "boss", speak_callback=cb4, speech_coordinator=coordinator, request_id="test_req_4")
    has_trouble4 = "trouble" in r4.lower() and "ollama" in r4.lower()
    print(f"Result 4: len={len(r4)} text=\"{r4[:60]}...\" chunks={len(received_chunks)} trouble={has_trouble4}")
    results.append(("4. longer response", not has_trouble4 and len(r4) > 0))

    # 5. Two consecutive questions
    print("\n--- TEST 5: Two consecutive questions ---", flush=True)
    r5a = ask_ollama_streaming("What is the capital of France?", "Boss", "boss", request_id="test_req_5a")
    r5b = ask_ollama_streaming("And what is the capital of Japan?", "Boss", "boss", request_id="test_req_5b")
    has_trouble5 = ("trouble" in r5a.lower() or "trouble" in r5b.lower()) and "ollama" in (r5a + r5b).lower()
    print(f"Result 5a: {r5a[:40]} | 5b: {r5b[:40]} trouble={has_trouble5}")
    results.append(("5. two consecutive questions", not has_trouble5 and len(r5a) > 0 and len(r5b) > 0))

    # 6. User interrupts / starts another query while JARVIS is speaking
    print("\n--- TEST 6: User interruption ---", flush=True)
    coordinator.begin_speech_session()
    coordinator.interrupt_speech(reason="user_barge_in", request_id="test_req_6_old")
    r6 = ask_ollama_streaming("tell me a quick joke", "Boss", "boss", speech_coordinator=coordinator, request_id="test_req_6_new")
    has_trouble6 = "trouble" in r6.lower() and "ollama" in r6.lower()
    print(f"Result 6: len={len(r6)} text=\"{r6[:60]}...\" trouble={has_trouble6}")
    results.append(("6. user interruption", not has_trouble6 and len(r6) > 0))

    # 7. Repeated casual conversation
    print("\n--- TEST 7: Repeated casual chat ---", flush=True)
    r7a = ask_ollama_streaming("thanks jarvis", "Boss", "boss", request_id="test_req_7a")
    r7b = ask_ollama_streaming("good job", "Boss", "boss", request_id="test_req_7b")
    has_trouble7 = ("trouble" in r7a.lower() or "trouble" in r7b.lower()) and "ollama" in (r7a + r7b).lower()
    print(f"Result 7a: {r7a[:40]} | 7b: {r7b[:40]} trouble={has_trouble7}")
    results.append(("7. repeated casual chat", not has_trouble7 and len(r7a) > 0 and len(r7b) > 0))

    # 8. Request that takes longer to generate
    print("\n--- TEST 8: Long generation prompt ---", flush=True)
    r8 = ask_ollama_streaming("Write a brief paragraph describing how quantum computing differs from classical computing.", "Boss", "boss", request_id="test_req_8")
    has_trouble8 = "trouble" in r8.lower() and "ollama" in r8.lower()
    print(f"Result 8: len={len(r8)} text=\"{r8[:60]}...\" trouble={has_trouble8}")
    results.append(("8. long generation", not has_trouble8 and len(r8) > 0))

    # 9. Computer-control functionality query
    print("\n--- TEST 9: Computer-control query ---", flush=True)
    router = CommandRouter(speech_coordinator=coordinator)
    cmd9_is_desktop = router.is_datetime_query("what time is it")
    print(f"Result 9: datetime_query={cmd9_is_desktop}")
    results.append(("9. computer control query routing", cmd9_is_desktop))

    # 10. Brightness control check
    print("\n--- TEST 10: Brightness control check ---", flush=True)
    from tools.computer.desktop_automation_engine import DesktopAutomationEngine
    is_desktop_cmd = DesktopAutomationEngine.is_desktop_command("brightness up")
    print(f"Result 10: 'brightness up' recognized as desktop command={is_desktop_cmd}")
    results.append(("10. brightness command routing", is_desktop_cmd))

    out_file = open("scratch/test_results.txt", "w", encoding="utf-8")
    def _log(msg):
        print(msg, flush=True)
        out_file.write(str(msg) + "\n")
        out_file.flush()

    _log("\n==================================================")
    _log("VERIFICATION SUMMARY")
    _log("==================================================")
    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        if not passed:
            all_passed = False
        _log(f"[{status}] {name}")

    if all_passed:
        _log("\nALL 10 VERIFICATION SCENARIOS PASSED SUCCESSFULLY!")
    else:
        _log("\nSOME VERIFICATION SCENARIOS FAILED!")
        out_file.close()
        sys.exit(1)
    out_file.close()

if __name__ == "__main__":
    run_tests()
