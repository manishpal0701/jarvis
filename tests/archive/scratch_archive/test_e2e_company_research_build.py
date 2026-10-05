"""
scratch/test_e2e_company_research_build.py
Real E2E verification test for company web research + website build pipeline.
Builds a website for Tesla, Inc., verifying research extraction, structured context injection,
production build, preview server, visual QA, and authoritative website readiness state.
"""

import sys
import os
import time
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_state import WebsiteStateManager

def run_e2e_company_build():
    start_time = time.time()
    task_prompt = "Jarvis Tesla ke liye ek landing page bana do"
    
    print("=" * 60)
    print(f"[E2E TEST START]: Prompt: '{task_prompt}'")
    print("=" * 60)

    assistant = CodeAssistant()
    
    # Execute build_website with open_browser=False for automated test execution
    entry_code, entry_path = assistant.build_website(
        task=task_prompt,
        open_browser=False
    )
    
    duration = time.time() - start_time
    
    state = WebsiteStateManager.get_instance().get_active_website()
    
    print("\n" + "=" * 60)
    print("E2E COMPANY WEBSITE BUILD REPORT")
    print("=" * 60)
    print(f"• Task Prompt: {task_prompt}")
    print(f"• Project Name: {state.project_name}")
    print(f"• Project Directory: {state.project_dir}")
    print(f"• Entry File: {entry_path}")
    print(f"• Build Status: {state.build_status}")
    print(f"• Validation Status: {state.validation_status}")
    print(f"• Preview Running: {state.preview_running}")
    print(f"• Visual QA Status: {state.visual_qa_status}")
    print(f"• Visual QA Passed: {state.visual_qa_passed}")
    print(f"• Authoritative Website Ready: {state.website_ready}")
    print(f"• Total Duration: {duration:.2f} seconds")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_company_build()
