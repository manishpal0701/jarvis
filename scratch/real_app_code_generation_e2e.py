"""
scratch/real_app_code_generation_e2e.py
Phase 4 — E2E Real Host Machine Verification Script for Intelligent Multi-File Code Generation Engine.
"""
import os
import sys
import json
import shutil
import subprocess

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.app_builder.app_model import AppBrief, AppProject, AppState
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_development_planner import AppDevelopmentPlanner
from tools.app_builder.app_workspace_manager import AppWorkspaceManager
from tools.app_builder.implementation_manifest import ImplementationManifest
from tools.app_builder.api_contract_validator import ApiContractValidator
from tools.app_builder.app_coding_agent import AppCodingAgent

def run_e2e_verification():
    print("======================================================================")
    print("PHASE 4 E2E VERIFICATION: REAL MULTI-FILE CODE GENERATION ENGINE")
    print("======================================================================")

    test_workspace_root = os.path.join(PROJECT_ROOT, "JARVIS App Projects", "E2EPhase4App")
    if os.path.exists(test_workspace_root):
        shutil.rmtree(test_workspace_root, ignore_errors=True)

    # 1. Initialize App & Requirements
    print("\n[STEP 1] Creating AppBrief for arbitrary production app request...")
    brief = AppBrief(
        name="TaskMaster Pro",
        description="Production Task & Expense Management mobile application with auth and analytics",
        features=["User Login", "Task Dashboard", "Add Task", "Task Detail", "User Profile"],
        authentication="JWT Auth"
    )

    # 2. Phase 3 Architecture Planner
    print("\n[STEP 2] Generating Phase 3 Architecture Plan...")
    plan = AppDevelopmentPlanner.generate_plan(brief, app_id="e2e_taskmaster")
    assert "screens" in plan, "Architecture plan missing screens"
    assert "api_contract" in plan, "Architecture plan missing api_contract"
    print(f"-> Phase 3 Architecture Plan generated. Domain: {plan.get('domain')}, Screens: {len(plan.get('screens', []))}")

    # 3. Create Workspace
    print("\n[STEP 3] Initializing physical workspace...")
    app = AppProject(project_id="e2e_taskmaster", name="TaskMaster Pro", brief=brief, development_plan=plan)
    ws_mgr = AppWorkspaceManager(workspace_root=os.path.dirname(test_workspace_root))
    ws_mgr.create_workspace(app, plan)
    workspace_path = app.workspace_path
    print(f"-> Workspace created at: {workspace_path}")

    # 4. Phase 4 Code Generation Engine
    print("\n[STEP 4] Executing Phase 4 AppCodingAgent file-by-file code generation...")
    coding_agent = AppCodingAgent()
    gen_result = coding_agent.generate_project_code(workspace_path, app_id="e2e_taskmaster")
    print(f"-> Generation Result: success={gen_result['success']}, total_files={gen_result['total_files']}, validated={gen_result['validated_files']}")
    assert gen_result["success"], "Code generation failed!"

    # 5. Verify Files On Disk
    print("\n[STEP 5] Verifying physical filesystem existence of generated source files...")
    domain = plan.get("domain", "item")
    expected_files = [
        os.path.join(workspace_path, "implementation_manifest.json"),
        os.path.join(workspace_path, "backend", "package.json"),
        os.path.join(workspace_path, "backend", "src", "server.js"),
        os.path.join(workspace_path, "backend", "src", "app.js"),
        os.path.join(workspace_path, "backend", "src", "routes", f"{domain}Routes.js"),
        os.path.join(workspace_path, "backend", "src", "controllers", f"{domain}Controller.js"),
        os.path.join(workspace_path, "backend", "src", "middleware", "errorHandler.js"),
        os.path.join(workspace_path, "frontend", "pubspec.yaml"),
        os.path.join(workspace_path, "frontend", "lib", "main.dart"),
        os.path.join(workspace_path, "frontend", "lib", "theme", "app_theme.dart"),
        os.path.join(workspace_path, "frontend", "lib", "services", "api_service.dart"),
        os.path.join(workspace_path, "frontend", "lib", "screens", "dashboard_screen.dart"),
        os.path.join(workspace_path, "frontend", "lib", "widgets", "custom_widgets.dart"),
    ]
    for ef in expected_files:
        assert os.path.exists(ef), f"Expected file missing: {ef}"
        print(f"  [OK] {os.path.relpath(ef, workspace_path)}")

    # 6. Syntax Checks
    print("\n[STEP 6] Running syntax validation checks (node --check)...")
    app_js = os.path.join(workspace_path, "backend", "src", "app.js")
    node_check = subprocess.run(["node", "--check", app_js], capture_output=True, text=True)
    assert node_check.returncode == 0, f"Node syntax check failed: {node_check.stderr}"
    print("  [OK] Node.js syntax check passed cleanly.")

    # 7. API Contract Alignment
    print("\n[STEP 7] Verifying API Contract Consistency...")
    api_val = ApiContractValidator.validate_project_api_consistency(workspace_path, plan["api_contract"])
    print(f"-> API Validation: success={api_val['success']}, checked={len(api_val['checked_endpoints'])}, mismatches={len(api_val['mismatches'])}")
    assert api_val["success"], f"API Contract validation failed! Mismatches: {api_val['mismatches']}"

    # 8. Targeted Change Request (Phase 4.21)
    print("\n[STEP 8] Testing targeted user change request...")
    change_res = coding_agent.apply_change_request(workspace_path, "Login page ka color blue kar do", app_id="e2e_taskmaster")
    assert change_res["success"], "Targeted change request failed!"
    print(f"-> Targeted change request applied to {len(change_res['affected_files'])} files: {change_res['affected_files']}")

    print("\n======================================================================")
    print("PHASE 4 E2E VERIFICATION: ALL CHECKS PASSED 100% CLEANLY!")
    print("======================================================================")

if __name__ == "__main__":
    run_e2e_verification()
