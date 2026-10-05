import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from conversation.conversation_manager import ConversationManager
from conversation.command_router import CommandRouter
from conversation.intelligence.context_tracker import ContextTracker
from memory.memory_manager import MemoryManager
from memory.memory_policy import MemoryPolicy
from ai.ask_ollama import _build_pipeline, _build_system_prompt

def run_all_acceptance_tests():
    results = {}
    print("==================================================")
    print("PHASE 1 — REAL-WORLD RUNTIME ACCEPTANCE TESTS")
    print("==================================================")

    # --------------------------------------------------
    # TEST 1 — FOLLOW-UP CONTEXT
    # --------------------------------------------------
    print("\n--- TEST 1: FOLLOW-UP CONTEXT ---")
    conv = ConversationManager.get_instance()
    conv.reset_context()

    res1 = conv.process_and_resolve_input("Ek expense tracker app bana do.")
    entity1 = conv.active_entity
    print(f"Turn 1 input: 'Ek expense tracker app bana do.' -> active_entity='{entity1}'")

    res2 = conv.process_and_resolve_input("Isme monthly chart bhi add karna.")
    has_followup1 = res2.get("has_followup")
    resolved_text1 = res2.get("resolved_text")
    print(f"Turn 2 input: 'Isme monthly chart bhi add karna.' -> resolved='{resolved_text1}'")

    test1_pass = entity1 == "expense tracker app" and has_followup1 and "expense tracker app" in resolved_text1
    results["TEST 1"] = ("PASS" if test1_pass else "FAIL", f"Resolved: '{resolved_text1}'")
    print(f"TEST 1 RESULT: {results['TEST 1'][0]}")

    # --------------------------------------------------
    # TEST 2 — MULTI-TURN REFERENCE
    # --------------------------------------------------
    print("\n--- TEST 2: MULTI-TURN REFERENCE ---")
    conv.reset_context()

    conv.process_and_resolve_input("Python me ek calculator bana do.")
    calc_entity = conv.active_entity
    print(f"Turn 1: active_entity='{calc_entity}'")

    res_t2 = conv.process_and_resolve_input("Isme history bhi add karo.")
    res_t3 = conv.process_and_resolve_input("Ab isko run karo.")

    t2_ok = res_t2.get("has_followup") and "calculator" in res_t2.get("resolved_text", "").lower()
    t3_ok = res_t3.get("has_followup") and "calculator" in res_t3.get("resolved_text", "").lower()

    print(f"Turn 2 'isme': resolved='{res_t2.get('resolved_text')}'")
    print(f"Turn 3 'isko': resolved='{res_t3.get('resolved_text')}'")

    test2_pass = t2_ok and t3_ok
    results["TEST 2"] = ("PASS" if test2_pass else "FAIL", f"t2_ok={t2_ok}, t3_ok={t3_ok}")
    print(f"TEST 2 RESULT: {results['TEST 2'][0]}")

    # --------------------------------------------------
    # TEST 3 — CONTEXT RESET
    # --------------------------------------------------
    print("\n--- TEST 3: CONTEXT RESET ---")
    conv.reset_context()

    conv.process_and_resolve_input("Main weather app ke baare me baat kar raha hoon.")
    print(f"Before reset: active_entity='{conv.active_entity}'")

    # Command Router handles reset command
    router = CommandRouter()
    router.handle_memory_command("New task start karo.")
    print(f"After reset command: active_entity='{conv.active_entity}', history_len={len(conv.history)}")

    res_t3_new = conv.process_and_resolve_input("Isme login add karo.")
    print(f"New task follow-up resolution: '{res_t3_new.get('resolved_text')}'")

    test3_pass = conv.active_entity is None or "weather app" not in res_t3_new.get("resolved_text", "").lower()
    results["TEST 3"] = ("PASS" if test3_pass else "FAIL", f"Weather leak detected: {not test3_pass}")
    print(f"TEST 3 RESULT: {results['TEST 3'][0]}")

    # --------------------------------------------------
    # TEST 4 — MEMORY
    # --------------------------------------------------
    print("\n--- TEST 4: MEMORY RETRIEVAL ---")
    temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    mem_mgr = MemoryManager(store_file=temp_file)
    mem_mgr._store_engine.clear_all()

    mem_id4, msg4 = mem_mgr.remember("Remember that I prefer Riverpod for Flutter projects.", category="user", key="preferred_framework", value="Riverpod")
    rec4 = mem_mgr._store_engine.get_record(mem_id4) if mem_id4 else None

    print(f"Memory store result: id={mem_id4}, msg={msg4}")
    print(f"Record: type={rec4.get('type') if rec4 else None}, importance={rec4.get('importance') if rec4 else None}")

    # Recall query
    recalled = mem_mgr.recall("Flutter projects me mera preferred state management kya hai?")
    print(f"Recalled records count: {len(recalled)}")

    test4_pass = mem_id4 is not None and rec4 is not None and rec4.get("importance") == 1.0 and len(recalled) > 0
    results["TEST 4"] = ("PASS" if test4_pass else "FAIL", f"Recalled {len(recalled)} items")
    print(f"TEST 4 RESULT: {results['TEST 4'][0]}")

    # --------------------------------------------------
    # TEST 5 — MEMORY DEDUPLICATION
    # --------------------------------------------------
    print("\n--- TEST 5: MEMORY DEDUPLICATION ---")
    id5_a, msg5_a = mem_mgr.remember("Remember that I prefer Riverpod.")
    id5_b, msg5_b = mem_mgr.remember("Remember that I prefer Riverpod.")

    all_recs5 = mem_mgr._store_engine.get_all_records()
    print(f"First call: id={id5_a}, msg='{msg5_a}'")
    print(f"Second call: id={id5_b}, msg='{msg5_b}'")
    print(f"Total store records count: {len(all_recs5)}")

    test5_pass = id5_a == id5_b and "deduplicated" in msg5_b.lower()
    results["TEST 5"] = ("PASS" if test5_pass else "FAIL", f"id_a={id5_a}, id_b={id5_b}")
    print(f"TEST 5 RESULT: {results['TEST 5'][0]}")

    # --------------------------------------------------
    # TEST 6 — MEMORY UPDATE
    # --------------------------------------------------
    print("\n--- TEST 6: MEMORY UPDATE ---")
    mem_mgr._store_engine.clear_all()

    id6_a, _ = mem_mgr.remember("Remember that I prefer Flutter.", category="user", key="preferred_framework", value="Flutter")
    id6_b, _ = mem_mgr.remember("Remember that I now prefer React.", category="user", key="preferred_framework", value="React")

    recs6 = mem_mgr._store_engine.get_all_records()
    print(f"First store id={id6_a}, Second update id={id6_b}")
    print(f"Total records in store: {len(recs6)}")
    if recs6:
        print(f"Active framework preference content: '{recs6[0].get('content')}'")

    test6_pass = id6_a == id6_b and len(recs6) == 1 and "React" in recs6[0].get("content", "")
    results["TEST 6"] = ("PASS" if test6_pass else "FAIL", f"Updated content='{recs6[0].get('content') if recs6 else None}'")
    print(f"TEST 6 RESULT: {results['TEST 6'][0]}")

    # --------------------------------------------------
    # TEST 7 — TRIVIAL CONTENT
    # --------------------------------------------------
    print("\n--- TEST 7: TRIVIAL CONTENT ---")
    mem_mgr._store_engine.clear_all()

    policy7 = MemoryPolicy()
    t7_a, _ = policy7.should_remember("What is 2+2?", memory_type="semantic")
    t7_b, _ = policy7.should_remember("Thanks.", memory_type="semantic")
    t7_c, _ = policy7.should_remember("What time is it?", memory_type="semantic")

    print(f"What is 2+2? -> should_remember={t7_a}")
    print(f"Thanks. -> should_remember={t7_b}")
    print(f"What time is it? -> should_remember={t7_c}")

    test7_pass = not t7_a and not t7_b and not t7_c
    results["TEST 7"] = ("PASS" if test7_pass else "FAIL", f"t7_a={t7_a}, t7_b={t7_b}, t7_c={t7_c}")
    print(f"TEST 7 RESULT: {results['TEST 7'][0]}")

    # --------------------------------------------------
    # TEST 8 — UNRELATED CONTEXT
    # --------------------------------------------------
    print("\n--- TEST 8: UNRELATED CONTEXT ---")
    conv.reset_context()

    conv.add_to_history("user", "What is the weather in Delhi?")
    conv.add_to_history("assistant", "It is 32 degrees Celsius and sunny in Delhi, Boss.")

    filtered_hist = conv.get_history_context(current_query="Flutter me Riverpod kya hai?")
    print(f"Original history count: {len(conv.history)}, Filtered history count for Flutter query: {len(filtered_hist)}")

    test8_pass = len(filtered_hist) == 0
    results["TEST 8"] = ("PASS" if test8_pass else "FAIL", f"Filtered history length={len(filtered_hist)}")
    print(f"TEST 8 RESULT: {results['TEST 8'][0]}")

    # --------------------------------------------------
    # TEST 9 — FEMALE PERSONA
    # --------------------------------------------------
    print("\n--- TEST 9: FEMALE PERSONA ---")
    sys_prompt = _build_system_prompt("Manish", "boss", {}, "")
    print(f"System Prompt Directives snippet: '{sys_prompt[:250]}...'")

    has_female_directives = "female AI assistant" in sys_prompt and "female Hindi grammatical forms" in sys_prompt
    results["TEST 9"] = ("PASS" if has_female_directives else "FAIL", "Female directives present in system prompt")
    print(f"TEST 9 RESULT: {results['TEST 9'][0]}")

    # --------------------------------------------------
    # TEST 10 — SPEECH REGRESSION
    # --------------------------------------------------
    print("\n--- TEST 10: SPEECH REGRESSION ---")
    import unittest
    from tests.test_speech_coordination_fix import TestSpeechCoordinationFix
    suite10 = unittest.TestLoader().loadTestsFromTestCase(TestSpeechCoordinationFix)
    res10 = unittest.TextTestRunner(verbosity=0).run(suite10)

    test10_pass = res10.wasSuccessful()
    results["TEST 10"] = ("PASS" if test10_pass else "FAIL", f"Passed {res10.testsRun} speech coordination tests")
    print(f"TEST 10 RESULT: {results['TEST 10'][0]}")

    # --------------------------------------------------
    # TEST 11 — LONG CONVERSATION
    # --------------------------------------------------
    print("\n--- TEST 11: LONG CONVERSATION BOUNDING ---")
    conv.reset_context()

    for i in range(15):
        conv.add_to_history("user", f"Turn {i} request about feature {i}")
        conv.add_to_history("assistant", f"Turn {i} response about feature {i}")

    bounded_hist = conv.get_history_context()
    hist_len = len(bounded_hist)
    print(f"Added 30 messages (15 turns). Bounded history length: {hist_len} messages ({hist_len//2} turns)")

    test11_pass = hist_len <= 12 and bounded_hist[-1]["content"] == "Turn 14 response about feature 14"
    results["TEST 11"] = ("PASS" if test11_pass else "FAIL", f"Bounded history messages={hist_len}")
    print(f"TEST 11 RESULT: {results['TEST 11'][0]}")

    # Clean temp file
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception:
            pass

    # Summary
    print("\n==================================================")
    print("SUMMARY RESULTS:")
    print("==================================================")
    all_passed = True
    for t_name, (status, detail) in results.items():
        print(f"{t_name}: {status} ({detail})")
        if status != "PASS":
            all_passed = False

    print("\nPHASE 1:")
    print(f"RUNTIME ACCEPTANCE = {'PASS' if all_passed else 'FAIL'}")
    return all_passed

if __name__ == "__main__":
    run_all_acceptance_tests()
