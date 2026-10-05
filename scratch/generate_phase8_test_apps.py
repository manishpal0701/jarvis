"""
scratch/generate_phase8_test_apps.py
Phase 8 Production App Builder Acceptance Test Suite.
Generates 3 independent production apps:
1. Task Manager App
2. Expense Tracker App
3. Weather App

Validates:
- Riverpod state management
- Domain isolation
- REST API integration & JSON store
- UI/UX design system
- Full navigation journey
- Flutter pub get & analysis & quality gates
"""
import os
import sys
import json
import logging

from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_orchestrator import AppDevelopmentOrchestrator
from tools.app_builder.production_quality_gate import ProductionQualityGate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase8AcceptanceTest")

def test_app_generation(name: str, prompt: str, domain: str) -> dict:
    print(f"\n============================================================")
    print(f"STARTING PHASE 8 BUILD: {name} (domain: {domain})")
    print(f"============================================================")

    app_mgr = AppManager()
    app_mgr.reset()

    # Create new app project
    project = app_mgr.create_app_project(
        name=name,
        initial_prompt=prompt,
        task_type="APP"
    )

    orchestrator = AppDevelopmentOrchestrator(request_id=project.request_id)
    updated_project = orchestrator.execute_pipeline(project)

    # Evaluate Quality Gate
    workspace_path = updated_project.workspace_path
    quality_report = ProductionQualityGate.evaluate_workspace(workspace_path)

    print(f"[{name}] WORKSPACE: {workspace_path}")
    print(f"[{name}] QUALITY GATE STATUS: {quality_report.get('status')}")

    return {
        "name": name,
        "domain": domain,
        "status": quality_report.get("status"),
        "passed": quality_report.get("passed", False),
        "workspace": workspace_path,
        "gates": quality_report.get("gates", {})
    }

def main():
    results = []

    # 1. Task Manager App
    task_res = test_app_generation(
        name="TaskFlow Master",
        prompt="Build a production task manager application with Flutter frontend, Riverpod state management, task categories, priorities, due dates, CRUD operations, search and Node.js REST API",
        domain="task"
    )
    results.append(task_res)

    # 2. Expense Tracker App
    expense_res = test_app_generation(
        name="ExpenseTracker Pro",
        prompt="Build a production expense tracker app with income vs expense charts, budget limits, category filter, transaction CRUD, Riverpod state management and Node.js REST API",
        domain="expense"
    )
    results.append(expense_res)

    # 3. Weather App
    weather_res = test_app_generation(
        name="WeatherPulse AI",
        prompt="Build a production weather forecast app with city location search, current temperature, 7-day forecast, hourly forecast, Riverpod state management, animations and Node.js API",
        domain="weather"
    )
    results.append(weather_res)

    print("\n============================================================")
    print("PHASE 8 FINAL ACCEPTANCE TEST SUMMARY REPORT")
    print("============================================================")
    all_passed = True
    for r in results:
        status_str = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_passed = False
        print(f"APP: {r['name'].ljust(25)} | DOMAIN: {r['domain'].ljust(10)} | STATUS: {status_str}")

    print("============================================================")
    if all_passed:
        print("OVERALL PHASE 8 RESULT: SUCCESS — ALL 3 APPS PASSED QUALITY GATES")
        sys.exit(0)
    else:
        print("OVERALL PHASE 8 RESULT: FAILED — AT LEAST ONE APP DID NOT PASS ALL GATES")
        sys.exit(1)

if __name__ == "__main__":
    main()
