import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import time
import json
import tempfile
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager

def execute_e2e_acceptance():
    print("=" * 70)
    print("FINAL END-TO-END ACCEPTANCE TEST: JARVIS AI WEBSITE BUILDER")
    print("=" * 70)

    prompt = "Jarvis create a modern premium AI portfolio website for Manish"
    print(f"\n[VOICE COMMAND]: \"{prompt}\"\n")

    t_start = time.perf_counter()

    assistant = CodeAssistant()
    ws = WorkspaceManager.get_instance()
    ws.ensure_started()

    # Track stage timings
    timing_metrics = {
        "planning_time": 0.0,
        "llm_generation_time": 0.0,
        "validation_time": 0.0,
        "repair_time": 0.0,
        "disk_write_time": 0.0,
        "streaming_time": 0.0,
        "build_and_install_time": 0.0,
        "preview_startup_time": 0.0,
        "total_time": 0.0
    }

    test_output_dir = os.path.abspath("workspace_e2e_test")
    os.makedirs(test_output_dir, exist_ok=True)

    t0 = time.perf_counter()
    print("Step 1: Running build_website orchestrator...")

    code_res, entry_path = assistant.build_website(prompt, project_dir=test_output_dir, open_browser=False)

    t_end = time.perf_counter()
    total_sec = t_end - t_start
    timing_metrics["total_time"] = total_sec

    print("\n" + "=" * 70)
    print("E2E ACCEPTANCE RUN COMPLETED")
    print("=" * 70)
    print(f"Entry File Path: {entry_path}")
    print(f"Total Execution Time: {total_sec:.2f} seconds ({total_sec/60:.2f} minutes)")

    # Output detailed metrics file for report
    metrics_file = os.path.join(test_output_dir, "e2e_timing_report.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(timing_metrics, f, indent=2)

    return entry_path, total_sec

if __name__ == "__main__":
    execute_e2e_acceptance()
