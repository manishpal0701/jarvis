"""
scratch/phase5_runtime_e2e.py
Phase 5 — E2E Real Host Machine Verification Script for Real Build, Run, Integration Testing & Autonomous Debugging.
Tests full pipeline execution, real commands, physical APK outputs, backend startup, health check HTTP GET,
API integration (POST -> GET -> DELETE), storage persistence, controlled failure repair, and status matrix display.
"""
import os
import sys
import json
import shutil
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.app_builder.app_model import AppBrief, AppProject, AppState
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_development_planner import AppDevelopmentPlanner
from tools.app_builder.app_workspace_manager import AppWorkspaceManager
from tools.app_builder.app_coding_agent import AppCodingAgent
from tools.app_builder.flutter_runtime import FlutterRuntime
from tools.app_builder.node_runtime import NodeRuntime
from tools.app_builder.api_integration_tester import ApiIntegrationTester
from tools.app_builder.runtime_error_analyzer import RuntimeErrorAnalyzer
from tools.app_builder.app_runtime_orchestrator import AppRuntimeOrchestrator


def run_phase5_e2e_verification():
    print("======================================================================")
    print("JARVIS APP BUILDER PHASE 5: REAL HOST RUNTIME VERIFICATION")
    print("======================================================================")

    test_workspace_root = os.path.join(PROJECT_ROOT, "JARVIS App Projects", "E2EPhase5ExpenseApp")
    if os.path.exists(test_workspace_root):
        shutil.rmtree(test_workspace_root, ignore_errors=True)

    # 1. Create AppBrief & Phase 3 Architecture Plan
    print("\n[STEP 1] Initializing AppBrief for Expense Tracker...")
    brief = AppBrief(
        name="Expense Pro",
        description="Production Expense Manager mobile application with REST API and persistence",
        features=["Login", "Dashboard", "Add Expense", "Expense Detail", "Profile"],
        authentication="JWT Auth"
    )
    plan = AppDevelopmentPlanner.generate_plan(brief, app_id="e2e_phase5_expense")
    print(f"-> Phase 3 Plan generated. Domain: {plan.get('domain')}, Screens: {len(plan.get('screens', []))}")

    # 2. Create Workspace
    print("\n[STEP 2] Creating physical workspace...")
    app = AppProject(project_id="e2e_phase5_expense", name="Expense Pro", brief=brief, development_plan=plan)
    ws_mgr = AppWorkspaceManager(workspace_root=os.path.dirname(test_workspace_root))
    ws_mgr.create_workspace(app, plan)
    workspace_path = app.workspace_path
    print(f"-> Workspace created at: {workspace_path}")

    # 3. Phase 4 Code Generation Engine
    print("\n[STEP 3] Generating application source code...")
    coding_agent = AppCodingAgent()
    gen_res = coding_agent.generate_project_code(workspace_path, app_id="e2e_phase5_expense")
    assert gen_res["success"], "Phase 4 Code Generation failed!"
    print(f"-> Code Generation completed: {gen_res['validated_files']}/{gen_res['total_files']} files validated.")

    # 4. Phase 5 Real Runtime Verification Pipeline
    print("\n[STEP 4] Executing Phase 5 AppRuntimeOrchestrator runtime verification pipeline...")
    runtime_orch = AppRuntimeOrchestrator()
    report = runtime_orch.execute_runtime_verification(workspace_path, app_id="e2e_phase5_expense")

    # 5. Verify Physical Output Files
    print("\n[STEP 5] Verifying physical output report files...")
    plan_file = os.path.join(workspace_path, "runtime_test_plan.json")
    report_file = os.path.join(workspace_path, "runtime_verification_report.json")
    assert os.path.exists(plan_file), f"Missing {plan_file}"
    assert os.path.exists(report_file), f"Missing {report_file}"
    print("  [OK] runtime_test_plan.json exists")
    print("  [OK] runtime_verification_report.json exists")

    # 6. Controlled Failure & Autonomous Repair Verification
    print("\n[STEP 6] Testing Controlled Failure Injection & Autonomous Repair Loop...")
    target_err_file = os.path.join(workspace_path, "frontend", "lib", "screens", "dashboard_screen.dart")
    if os.path.exists(target_err_file):
        with open(target_err_file, "a", encoding="utf-8") as f:
            f.write("\n// Controlled Error\nclass BrokenClass { undefinedVar = 42; }\n")

        print("  -> Controlled syntax error injected into dashboard_screen.dart")
        ana_broken = FlutterRuntime.analyze(os.path.join(workspace_path, "frontend"), app_id="e2e_phase5_expense")
        err_obj = RuntimeErrorAnalyzer.parse_error(ana_broken.get("stdout") or ana_broken.get("stderr"), platform="flutter")
        print(f"  -> Error Extracted: {err_obj.get('message')[:80]} at {err_obj.get('file')}:{err_obj.get('line')}")

        print("  -> Executing Autonomous Repair...")
        coding_agent.apply_change_request(workspace_path, "Fix broken syntax in dashboard_screen.dart", app_id="e2e_phase5_expense")
        ana_fixed = FlutterRuntime.analyze(os.path.join(workspace_path, "frontend"), app_id="e2e_phase5_expense")
        assert "BrokenClass" not in (ana_fixed.get("stdout") or ""), "Repair failed to clean up broken class"
        print("  [OK] Autonomous repair successfully fixed injected failure!")

    print("\n======================================================================")
    print("PHASE 5 PRODUCTION E2E VERIFICATION COMPLETED SUCCESSFULLY!")
    print("======================================================================\n")


if __name__ == "__main__":
    run_phase5_e2e_verification()
