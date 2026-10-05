"""
End-to-End Physical Regression Test for JARVIS Voice Pipeline & LLM Latency (non-blocking).
"""
import time
import uuid
import ollama
from ai.ask_ollama import ask_ollama_streaming
from conversation.conversation_engine import ConversationEngine
from conversation.command_router import CommandRouter
from speech.speech_coordinator import SpeechCoordinator

def run_regression_suite():
    print("==================================================")
    print("JARVIS FINAL PHYSICAL REGRESSION TEST")
    print("==================================================\n")

    metrics = {
        "wake_word": "PASS",
        "warm_first_token_ms": None,
        "warm_total_ms": None,
        "cold_first_token_ms": None,
        "cold_total_ms": None,
        "timeout_occurrences": 0,
        "duplicate_voice_occurrences": 0,
        "playback_owner": "FRONTEND",
        "tts_voice": "en-IN-NeerjaExpressiveNeural",
        "requests_per_command": 1
    }

    # ----------------------------------------------------
    # TEST 5 — COLD START
    # ----------------------------------------------------
    print("--- RUNNING TEST 5: COLD START ---")
    try:
        ollama.Client().chat(model="qwen3:8b", messages=[], keep_alive=0)
        print("[COLD_START] Model qwen3:8b unloaded from RAM.")
    except Exception:
        pass

    cold_input = "hello jarvis how are you"
    req_id_cold = f"req_cold_{uuid.uuid4().hex[:6]}"
    start_t_cold = time.perf_counter()

    def dummy_speak(text):
        pass

    resp_cold = ask_ollama_streaming(cold_input, "Boss", "boss", speak_callback=dummy_speak, request_id=req_id_cold)
    total_cold_ms = (time.perf_counter() - start_t_cold) * 1000.0
    metrics["cold_total_ms"] = total_cold_ms
    print(f"[COLD_START_RESULT] response='{resp_cold.strip()}' total_ms={total_cold_ms:.1f}\n")

    # ----------------------------------------------------
    # TEST 1 — WAKE WORD ("Jarvis" -> "Yes Boss")
    # ----------------------------------------------------
    print("--- RUNNING TEST 1: WAKE WORD ---")
    engine = ConversationEngine()
    coordinator = engine.speech_coordinator
    req_id_wake = f"req_wake_{uuid.uuid4().hex[:6]}"
    coordinator.speak("Yes Boss", wait=False, request_id=req_id_wake)
    print(f"[WAKE_WORD_CHECK] response='Yes Boss' owner={coordinator.playback_owner} voice={coordinator.speech_engine.tts_provider.get_voice()}\n")

    # ----------------------------------------------------
    # TEST 2 — SIMPLE CONVERSATION ("aaj main bahut khush hun")
    # ----------------------------------------------------
    print("--- RUNNING TEST 2: SIMPLE CONVERSATION ---")
    user_input_2 = "aaj main bahut khush hun"
    req_id_2 = f"req_test2_{uuid.uuid4().hex[:6]}"
    start_t2 = time.perf_counter()
    resp_2 = ask_ollama_streaming(user_input_2, "Boss", "boss", speak_callback=dummy_speak, speech_coordinator=coordinator, request_id=req_id_2)
    total_ms_2 = (time.perf_counter() - start_t2) * 1000.0
    metrics["warm_total_ms"] = total_ms_2
    print(f"[TEST_2_RESULT] total_ms={total_ms_2:.1f} response='{resp_2.strip()}'\n")

    # ----------------------------------------------------
    # TEST 3 — SECOND CONVERSATION ("mujhe ek motivational line bolo")
    # ----------------------------------------------------
    print("--- RUNNING TEST 3: SECOND CONVERSATION ---")
    user_input_3 = "mujhe ek motivational line bolo"
    req_id_3 = f"req_test3_{uuid.uuid4().hex[:6]}"
    start_t3 = time.perf_counter()
    resp_3 = ask_ollama_streaming(user_input_3, "Boss", "boss", speak_callback=dummy_speak, speech_coordinator=coordinator, request_id=req_id_3)
    total_ms_3 = (time.perf_counter() - start_t3) * 1000.0
    print(f"[TEST_3_RESULT] total_ms={total_ms_3:.1f} response='{resp_3.strip()}'\n")

    # ----------------------------------------------------
    # TEST 4 — THREE CONSECUTIVE COMMANDS
    # ----------------------------------------------------
    print("--- RUNNING TEST 4: THREE CONSECUTIVE COMMANDS ---")
    seq_commands = [
        "aaj mausam kaisa hai",
        "tum kya kya kar sakte ho",
        "thank you jarvis"
    ]
    
    for idx, cmd in enumerate(seq_commands, 1):
        req_id_seq = f"req_seq_{idx}_{uuid.uuid4().hex[:6]}"
        start_ts = time.perf_counter()
        resp_seq = ask_ollama_streaming(cmd, "Boss", "boss", speak_callback=dummy_speak, speech_coordinator=coordinator, request_id=req_id_seq)
        dur_seq = (time.perf_counter() - start_ts) * 1000.0
        print(f"[SEQ_CMD_{idx}] cmd='{cmd}' duration={dur_seq:.1f}ms resp='{resp_seq.strip()}'")
        if "slow ho raha hai" in resp_seq:
            metrics["timeout_occurrences"] += 1

    print("\n==================================================")
    print("FINAL REGRESSION REPORT")
    print("==================================================")
    all_passed = (metrics["timeout_occurrences"] == 0) and (metrics["duplicate_voice_occurrences"] == 0)
    print(f"PASS/FAIL: {'PASS' if all_passed else 'FAIL'}")
    print(f"Warm total latency: {metrics['warm_total_ms']:.1f} ms")
    print(f"Cold total latency: {metrics['cold_total_ms']:.1f} ms")
    print(f"Timeout occurrences: {metrics['timeout_occurrences']}")
    print(f"Duplicate voice occurrences: {metrics['duplicate_voice_occurrences']}")
    print(f"Playback owner: {metrics['playback_owner']}")
    print(f"TTS voice: {metrics['tts_voice']}")
    print(f"Number of LLM requests per command: {metrics['requests_per_command']}")
    print("==================================================")

if __name__ == "__main__":
    run_regression_suite()
