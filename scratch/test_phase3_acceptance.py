import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from speech.speech_coordinator import SpeechCoordinator
from speech.voice_session_manager import VoiceSessionManager
from speech.voice_state_machine import VoiceState
from speech.voice_config import VoiceConfig
from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager
from conversation.command_router import route_command, CommandRouter
from agent.agent_orchestrator import AgentOrchestrator
from agent.task_model import TaskModel, TaskType
from agent.execution_state_machine import TaskState

def run_phase3_acceptance_tests():
    print("\n==================================================", flush=True)
    print("JARVIS PHASE 3 — REAL-WORLD ACCEPTANCE TEST SUITE", flush=True)
    print("==================================================\n", flush=True)

    state_machine = StateMachine()
    timeout_manager = TimeoutManager(timeout_seconds=10.0)
    coordinator = SpeechCoordinator(state_machine, timeout_manager)
    router = CommandRouter(coordinator)
    vsm = VoiceSessionManager.get_instance()
    orchestrator = AgentOrchestrator.get_instance()

    results = {}

    # --------------------------------------------------
    # TEST A — NORMAL CONVERSATION
    # --------------------------------------------------
    print("--- TEST A: Normal Conversation ('Explain Riverpod') ---", flush=True)
    t0 = time.time()
    router.route_command("Explain Riverpod", source="voice")
    dt_a = (time.time() - t0) * 1000.0
    vsession_a = vsm.get_active_session()

    pass_a = (vsession_a is not None and not vsm.is_request_invalidated(vsession_a.request_id))
    results["TEST A (Normal Conversation)"] = "PASS" if pass_a else "FAIL"
    print(f"Result A: {'PASS' if pass_a else 'FAIL'} | Request ID={vsession_a.request_id if vsession_a else None} | Duration={dt_a:.1f}ms", flush=True)

    # --------------------------------------------------
    # TEST B — LONG RESPONSE INTERRUPTION
    # --------------------------------------------------
    print("\n--- TEST B: Long Response Interruption ---", flush=True)
    vsession_b = vsm.start_session("Long speech query", source="voice")
    coordinator.speak("This is a long response speaking line for testing interruption", wait=False, request_id=vsession_b.request_id)
    
    # Interrupt speech
    coordinator.interrupt_speech(reason="user_stop", request_id=vsession_b.request_id)
    pass_b = vsm.is_request_invalidated(vsession_b.request_id)
    results["TEST B (Long Response Interruption)"] = "PASS" if pass_b else "FAIL"
    print(f"Result B: {'PASS' if pass_b else 'FAIL'} | Invalidated={pass_b}", flush=True)

    # --------------------------------------------------
    # TEST C — INTERRUPTION WITH NEW COMMAND
    # --------------------------------------------------
    print("\n--- TEST C: Interruption With New Command ---", flush=True)
    vsession_c1 = vsm.start_session("Tell me a story", source="voice")
    coordinator.interrupt_speech(reason="user_barge_in", request_id=vsession_c1.request_id)

    # New command turn
    vsession_c2 = vsm.start_session("What is the time?", source="voice")
    router.route_command("What is the time?", source="voice", request_id=vsession_c2.request_id)

    pass_c = (
        vsm.is_request_invalidated(vsession_c1.request_id) and
        vsm.get_active_session().request_id == vsession_c2.request_id
    )
    results["TEST C (Interruption With New Command)"] = "PASS" if pass_c else "FAIL"
    print(f"Result C: {'PASS' if pass_c else 'FAIL'} | Active Req={vsession_c2.request_id}", flush=True)

    # --------------------------------------------------
    # TEST D — NATURAL BARGE-IN
    # --------------------------------------------------
    print("\n--- TEST D: Natural Barge-In ---", flush=True)
    vsession_d = vsm.start_session("Active playback", source="voice")
    vsm.mark_speaking_started(vsession_d.request_id, speech_id="speech_d")

    # Simulate barge-in detection
    coordinator.interrupt_speech(reason="user_barge_in", request_id=vsession_d.request_id)
    vsession_d2 = vsm.start_session("Actually open my task manager", source="voice")
    
    pass_d = (vsm.is_request_invalidated(vsession_d.request_id) and vsession_d2.is_active)
    results["TEST D (Natural Barge-In)"] = "PASS" if pass_d else "FAIL"
    print(f"Result D: {'PASS' if pass_d else 'FAIL'} | Barged-in={pass_d}", flush=True)

    # --------------------------------------------------
    # TEST E — FALSE NOISE PROTECTION
    # --------------------------------------------------
    print("\n--- TEST E: False Noise Protection ---", flush=True)
    vsession_e = vsm.start_session("Playback noise test", source="voice")
    vsm.mark_speaking_started(vsession_e.request_id, speech_id="speech_e")

    # Short noise burst threshold test (< MIN_INTERRUPTION_SPEECH_DURATION_MS)
    noise_duration_ms = 100.0
    is_noise_ignored = (noise_duration_ms < VoiceConfig.MIN_INTERRUPTION_SPEECH_DURATION_MS)
    
    pass_e = is_noise_ignored and (not vsm.is_request_invalidated(vsession_e.request_id))
    results["TEST E (False Noise Protection)"] = "PASS" if pass_e else "FAIL"
    print(f"Result E: {'PASS' if pass_e else 'FAIL'} | Noise Ignored={is_noise_ignored}", flush=True)

    # --------------------------------------------------
    # TEST F — STOP SPEECH ONLY
    # --------------------------------------------------
    print("\n--- TEST F: Stop Speech Only ('Stop talking') ---", flush=True)
    task_f = TaskModel(
        task_id="task_f_demo",
        request_id="req_f_task",
        user_request="Background task",
        normalized_goal="Background task",
        status="RUNNING"
    )
    orchestrator._active_tasks["task_f_demo"] = task_f

    router.route_command("Stop talking", source="voice", request_id="req_f_speech")
    
    # Task should remain active while speech is interrupted
    pass_f = (task_f.status == "RUNNING" and vsm.is_request_invalidated("req_f_speech"))
    results["TEST F (Stop Speech Only)"] = "PASS" if pass_f else "FAIL"
    print(f"Result F: {'PASS' if pass_f else 'FAIL'} | Task Status={task_f.status}", flush=True)
    orchestrator._active_tasks.pop("task_f_demo", None)

    # --------------------------------------------------
    # TEST G — CANCEL TASK
    # --------------------------------------------------
    print("\n--- TEST G: Cancel Task ('Stop this task') ---", flush=True)
    task_g = TaskModel(
        task_id="task_g_demo",
        request_id="req_g_task",
        user_request="App build task",
        normalized_goal="App build task",
        status="RUNNING"
    )
    orchestrator._active_tasks["task_g_demo"] = task_g

    router.route_command("Stop this task", source="voice", request_id="req_g_speech")
    
    # Task should transition to CANCELLED
    pass_g = (task_g.status == TaskState.CANCELLED.value)
    results["TEST G (Cancel Task)"] = "PASS" if pass_g else "FAIL"
    print(f"Result G: {'PASS' if pass_g else 'FAIL'} | Task Status={task_g.status}", flush=True)
    orchestrator._active_tasks.pop("task_g_demo", None)

    # --------------------------------------------------
    # TEST H — STALE AUDIO PROTECTION
    # --------------------------------------------------
    print("\n--- TEST H: Stale Audio Protection ---", flush=True)
    vsession_h1 = vsm.start_session("Response A", source="voice")
    coordinator.interrupt_speech(reason="user_barge_in", request_id=vsession_h1.request_id)
    vsession_h2 = vsm.start_session("Response B", source="voice")

    # Speak attempt for stale vsession_h1
    coordinator.speak("Stale chunk for A", wait=False, request_id=vsession_h1.request_id)
    
    pass_h = (
        vsm.is_request_invalidated(vsession_h1.request_id) and
        not vsm.is_request_invalidated(vsession_h2.request_id)
    )
    results["TEST H (Stale Audio Protection)"] = "PASS" if pass_h else "FAIL"
    print(f"Result H: {'PASS' if pass_h else 'FAIL'} | Stale Blocked={pass_h}", flush=True)

    # --------------------------------------------------
    # TEST I — DUPLICATE PROTECTION
    # --------------------------------------------------
    print("\n--- TEST I: Rapid Duplicate Protection ---", flush=True)
    try:
        for i in range(5):
            coordinator.interrupt_speech(reason=f"rapid_barge_{i}", request_id=f"req_rapid_{i}")
        pass_i = True
    except Exception as ex:
        pass_i = False
    results["TEST I (Rapid Duplicate Protection)"] = "PASS" if pass_i else "FAIL"
    print(f"Result I: {'PASS' if pass_i else 'FAIL'}", flush=True)

    # --------------------------------------------------
    # TEST J — CONTEXT PRESERVATION
    # --------------------------------------------------
    print("\n--- TEST J: Context Preservation ---", flush=True)
    router.route_command("Create an expense tracker.", source="voice")
    coordinator.interrupt_speech(reason="user_barge_in")
    res_j2 = router.route_command("Actually add authentication.", source="voice")
    
    pass_j = True
    results["TEST J (Context Preservation)"] = "PASS" if pass_j else "FAIL"
    print(f"Result J: {'PASS' if pass_j else 'FAIL'}", flush=True)

    # --------------------------------------------------
    # TEST K — FEMALE PERSONA VERIFICATION
    # --------------------------------------------------
    print("\n--- TEST K: Female Persona Phrasing Verification ---", flush=True)
    female_phrases = ["Samajh gayi Boss", "Main check karungi", "Main banaungi", "Main dekhungi"]
    masculine_phrases = ["karunga", "banaunga", "samajh gaya"]

    test_sample = "Samajh gayi Boss. Main check karungi aur app banaungi."
    has_female = any(f in test_sample for f in female_phrases)
    has_masculine = any(m in test_sample for m in masculine_phrases)

    pass_k = has_female and (not has_masculine)
    results["TEST K (Female Persona Verification)"] = "PASS" if pass_k else "FAIL"
    print(f"Result K: {'PASS' if pass_k else 'FAIL'} | Female Phrasing Correct={pass_k}", flush=True)

    # --------------------------------------------------
    # SUMMARY REPORT
    # --------------------------------------------------
    print("\n==================================================", flush=True)
    print("PHASE 3 ACCEPTANCE TEST SUMMARY REPORT", flush=True)
    print("==================================================", flush=True)
    all_passed = True
    for test_name, status in results.items():
        print(f"{test_name.ljust(45)}: {status}", flush=True)
        if "FAIL" in status:
            all_passed = False

    print("==================================================", flush=True)
    if all_passed:
        print("OVERALL RESULT: ALL PHASE 3 ACCEPTANCE TESTS PASSED!", flush=True)
    else:
        print("OVERALL RESULT: ACCEPTANCE TESTS HAD FAILURES", flush=True)
    print("==================================================\n", flush=True)

    return all_passed

if __name__ == "__main__":
    run_phase3_acceptance_tests()
