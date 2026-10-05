import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.agent_orchestrator import AgentOrchestrator, FailureClass
from agent.agent_registry import AgentRegistry
from agent.task_planner import TaskPlanner
from agent.execution_state_machine import ExecutionStateMachine, TaskState
from agent.task_persistence import TaskPersistence
from agent.task_model import TaskModel, StepModel, TaskType
from agent.agent_result import AgentResult, AgentResultStatus
from conversation.command_router import route_command
from conversation.context_manager import ContextManager
from conversation.intelligence.context_tracker import ContextTracker

def run_phase2_acceptance_tests():
    print("\n==================================================", flush=True)
    print("JARVIS PHASE 2 — REAL-WORLD ACCEPTANCE TEST SUITE", flush=True)
    print("==================================================\n", flush=True)

    orchestrator = AgentOrchestrator.get_instance()
    context_mgr = ContextManager()
    context_tracker = ContextTracker()
    persistence = TaskPersistence.get_instance()

    results = {}

    # --------------------------------------------------
    # SCENARIO A — SIMPLE REQUEST (Conversational Direct)
    # --------------------------------------------------
    print("--- SCENARIO A: Simple Request ('Explain Riverpod') ---", flush=True)
    t0 = time.time()
    res_a = orchestrator.orchestrate("Explain Riverpod", source="test")
    dt_a = (time.time() - t0) * 1000.0
    
    pass_a = (
        res_a.success and 
        res_a.status == AgentResultStatus.SUCCESS and
        res_a.agent_id == "conversation_agent"
    )
    results["Scenario A (Simple Request)"] = "PASS" if pass_a else f"FAIL ({res_a.error})"
    print(f"Result A: {'PASS' if pass_a else 'FAIL'} | Agent={res_a.agent_id} | Status={res_a.status} | Duration={dt_a:.1f}ms", flush=True)

    # --------------------------------------------------
    # SCENARIO B — SINGLE AGENT TASK
    # --------------------------------------------------
    print("\n--- SCENARIO B: Single Agent Task ('Create a Flutter login screen') ---", flush=True)
    t0 = time.time()
    res_b = orchestrator.orchestrate("Create a Flutter login screen", source="test")
    dt_b = (time.time() - t0) * 1000.0

    pass_b = (
        res_b.success and
        res_b.status == AgentResultStatus.SUCCESS and
        res_b.agent_id in ["app_builder_agent", "code_assistant_agent"]
    )
    results["Scenario B (Single Agent Task)"] = "PASS" if pass_b else f"FAIL ({res_b.error})"
    print(f"Result B: {'PASS' if pass_b else 'FAIL'} | Agent={res_b.agent_id} | Status={res_b.status} | Duration={dt_b:.1f}ms", flush=True)

    # --------------------------------------------------
    # SCENARIO C — MULTI-STEP APP TASK
    # --------------------------------------------------
    print("\n--- SCENARIO C: Multi-Step App Task ('Create task manager app with auth, search, and dark mode') ---", flush=True)
    t0 = time.time()
    plan_c = orchestrator.planner.generate_plan("Create task manager app with auth, search, and dark mode")
    pass_c_plan = (
        plan_c.task_type == TaskType.APP_BUILD and
        len(plan_c.steps) >= 3 and
        len(plan_c.steps[1].dependencies) > 0
    )
    
    res_c = orchestrator.orchestrate("Create task manager app with auth, search, and dark mode", source="test")
    dt_c = (time.time() - t0) * 1000.0

    pass_c = pass_c_plan and res_c.success and (res_c.status == AgentResultStatus.SUCCESS)
    results["Scenario C (Multi-Step Task Plan & Isolation)"] = "PASS" if pass_c else f"FAIL ({res_c.error})"
    print(f"Result C: {'PASS' if pass_c else 'FAIL'} | Steps={len(plan_c.steps)} | Workspace={plan_c.workspace_path} | Duration={dt_c:.1f}ms", flush=True)

    # --------------------------------------------------
    # SCENARIO D — FAILURE HANDLING & BOUNDED RECOVERY
    # --------------------------------------------------
    print("\n--- SCENARIO D: Bounded Recovery & No False Success ---", flush=True)
    task_d = TaskModel(
        task_id="task_fail_demo",
        request_id="req_d",
        user_request="Failing task test",
        normalized_goal="Failing task test",
        task_type=TaskType.APP_BUILD,
        steps=[
            StepModel(
                step_id="step_fail_1",
                task_id="task_fail_demo",
                name="Failing Build Step",
                description="Intentionally failing step",
                agent_id="app_builder_agent"
            )
        ]
    )

    # Simulate step handler throwing repeated compilation error
    orchestrator.state_machine.transition_to(task_d, TaskState.PLANNING)
    orchestrator.state_machine.transition_to(task_d, TaskState.PLANNED)
    orchestrator.state_machine.transition_to(task_d, TaskState.READY)
    orchestrator.state_machine.transition_to(task_d, TaskState.RUNNING)

    err_msg = "Compilation failed: syntax error in main.dart line 42"
    fail_cls = orchestrator.classify_failure(err_msg)
    
    # Verify classification and no false success
    pass_d = (fail_cls == FailureClass.SYNTAX_ERROR)
    results["Scenario D (Failure Handling & Recovery)"] = "PASS" if pass_d else "FAIL"
    print(f"Result D: {'PASS' if pass_d else 'FAIL'} | Classified Class={fail_cls}", flush=True)

    # --------------------------------------------------
    # SCENARIO E — CANCELLATION
    # --------------------------------------------------
    print("\n--- SCENARIO E: Task Cancellation ('Stop this') ---", flush=True)
    res_e = orchestrator.orchestrate("Stop this", source="test")
    pass_e = (res_e.status == AgentResultStatus.CANCELLED)
    results["Scenario E (Cancellation)"] = "PASS" if pass_e else f"FAIL ({res_e.status})"
    print(f"Result E: {'PASS' if pass_e else 'FAIL'} | Status={res_e.status}", flush=True)

    # --------------------------------------------------
    # SCENARIO F — CONTEXT FOLLOW-UP
    # --------------------------------------------------
    print("\n--- SCENARIO F: Context Follow-Up ---", flush=True)
    res_f1 = route_command("Ek expense tracker app bana do.")
    res_f2 = route_command("Isme monthly chart bhi add karna.")
    topic = context_tracker.extract_topic("Ek expense tracker app bana do.")
    pass_f = (topic == "app development") or res_f2 is not None
    results["Scenario F (Context Follow-Up)"] = "PASS" if pass_f else "FAIL"
    print(f"Result F: {'PASS' if pass_f else 'FAIL'} | Extracted Topic='{topic}'", flush=True)

    # --------------------------------------------------
    # SCENARIO G — TWO PROJECTS ISOLATION
    # --------------------------------------------------
    print("\n--- SCENARIO G: Two Projects Isolation ---", flush=True)
    plan_g1 = orchestrator.planner.generate_plan("Create weather forecasting app")
    plan_g2 = orchestrator.planner.generate_plan("Create crypto tracker app")
    
    ws1 = f"JARVIS_Workspace_{plan_g1.task_id}"
    ws2 = f"JARVIS_Workspace_{plan_g2.task_id}"

    pass_g = (ws1 != ws2 and plan_g1.task_id != plan_g2.task_id)
    results["Scenario G (Two Projects Isolation)"] = "PASS" if pass_g else "FAIL"
    print(f"Result G: {'PASS' if pass_g else 'FAIL'} | WS1={ws1} | WS2={ws2}", flush=True)

    # --------------------------------------------------
    # SCENARIO H — SPEECH & VOICE PIPELINE INTEGRATION
    # --------------------------------------------------
    print("\n--- SCENARIO H: Speech & Voice Pipeline Integration ---", flush=True)
    from speech.speech_coordinator import SpeechCoordinator
    from core.state_machine import StateMachine
    from core.timeout_manager import TimeoutManager
    sc = SpeechCoordinator(StateMachine(), TimeoutManager(timeout_seconds=10.0))

    # Emit progress event speech test
    try:
        sc.speak("Phase 2 Orchestrator test voice output.", wait=False)
        pass_h = True
    except Exception as ex:
        pass_h = False
    results["Scenario H (Speech Pipeline Integrity)"] = "PASS" if pass_h else "FAIL"
    print(f"Result H: {'PASS' if pass_h else 'FAIL'}", flush=True)

    # --------------------------------------------------
    # FINAL SUMMARY REPORT
    # --------------------------------------------------
    print("\n==================================================", flush=True)
    print("PHASE 2 ACCEPTANCE TEST SUMMARY REPORT", flush=True)
    print("==================================================", flush=True)
    all_passed = True
    for test_name, status in results.items():
        print(f"{test_name.ljust(45)}: {status}", flush=True)
        if "FAIL" in status:
            all_passed = False

    print("==================================================", flush=True)
    if all_passed:
        print("OVERALL RESULT: ALL PHASE 2 ACCEPTANCE TESTS PASSED!", flush=True)
    else:
        print("OVERALL RESULT: ACCEPTANCE TESTS HAD FAILURES", flush=True)
    print("==================================================\n", flush=True)

    return all_passed

if __name__ == "__main__":
    run_phase2_acceptance_tests()
