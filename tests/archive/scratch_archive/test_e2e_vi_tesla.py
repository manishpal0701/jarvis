"""
scratch/test_e2e_vi_tesla.py
E2E Test 1: Tesla company website build with Visual & Asset Intelligence.
Prompt: "Jarvis, Tesla ke liye ek premium modern responsive website bana do."
"""

import sys
import os
import time
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_state import WebsiteStateManager

def main():
    prompt = "Jarvis, Tesla ke liye ek premium modern responsive website bana do."
    print("=" * 60)
    print(f"[E2E TEST 1 START]: Prompt: '{prompt}'")
    print("=" * 60)

    assistant = CodeAssistant()
    start_time = time.time()
    
    entry_code, entry_path = assistant.build_website(task=prompt, open_browser=False)
    duration = time.time() - start_time
    
    state = WebsiteStateManager.get_instance().get_active_website()
    
    print("\n" + "=" * 60)
    print("E2E TEST 1 SUMMARY REPORT — TESLA COMPANY WEBSITE")
    print("=" * 60)
    print(f"• Project Name: {state.project_name}")
    print(f"• Project Directory: {state.project_dir}")
    print(f"• Build Status: {state.build_status}")
    print(f"• Dependency Validation Passed: {state.dependency_validation_passed}")
    print(f"• Build Passed: {state.build_passed}")
    print(f"• Preview Running: {state.preview_running}")
    print(f"• HTTP Status OK: {state.http_status_ok}")
    print(f"• Visual QA Status: {state.visual_qa_status}")
    print(f"• Visual QA Passed: {state.visual_qa_passed}")
    print(f"• Responsive Passed: {state.responsive_passed}")
    print(f"• Console Errors: {state.console_errors}")
    print(f"• Broken Images: {state.broken_images}")
    print(f"• Authoritative WEBSITE_READY: {state.website_ready}")
    print(f"• Effective Preview URL: {state.get_effective_preview_url()}")
    print(f"• Duration: {duration:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    main()
