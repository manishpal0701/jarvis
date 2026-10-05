import os
import sys
import time
import requests
from config import CODE_GEN_MODEL, RESEARCH_MODEL
from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_state import WebsiteStateManager

def run_e2e():
    sys.stdout.reconfigure(line_buffering=True)
    start_time = time.time()
    print("=" * 60, flush=True)
    print("RUNNING REAL MANUAL E2E WEBSITE BUILD PIPELINE TEST")
    print("Prompt: 'Mere restaurant ke liye ek modern website bana do'")
    print("=" * 60, flush=True)

    assistant = CodeAssistant()
    prompt = "Mere restaurant ke liye ek modern website bana do"
    
    intent = assistant.classify_coding_mode(prompt)
    res, entry_path = assistant.generate_code(prompt, open_browser=False)

    state = WebsiteStateManager.get_instance().get_active_website()

    print("\n" + "=" * 60)
    print("E2E PIPELINE EXECUTION VERIFICATION REPORT")
    print("=" * 60)

    if state:
        generated_files = []
        if os.path.exists(state.output_directory):
            for root, _, files in os.walk(state.output_directory):
                for f in files:
                    rel_f = os.path.relpath(os.path.join(root, f), state.output_directory)
                    generated_files.append(rel_f)

        actual_http_code = "N/A"
        if state.local_url:
            try:
                resp = requests.get(state.local_url, timeout=5)
                actual_http_code = str(resp.status_code)
            except Exception as e:
                actual_http_code = f"Error: {e}"

        print(f"1.  Intent/Model Routing:        {intent}")
        print(f"2.  Research Model Used:          {RESEARCH_MODEL} (Brief / Strategy)")
        print(f"3.  Code Generation Model Used:   {CODE_GEN_MODEL}")
        print(f"4.  Generated UI Files Count:     {len(generated_files)}")
        print(f"5.  Dependency Validation Result: {'PASS' if state.dependency_validation_passed else 'FAIL'}")
        print(f"6.  Dependency Repair Attempts:   {state.repair_attempts}")
        print(f"7.  npm Build Exit Code:          {0 if state.build_passed else 1}")
        print(f"8.  Preview Server Port:          {state.port or 'N/A'}")
        print(f"9.  Actual Preview URL:           {state.local_url or 'N/A'}")
        print(f"10. Actual HTTP Status Code:      {actual_http_code}")
        print(f"11. Visual QA Score:              {state.visual_qa_score}")
        print(f"12. Responsive Result:            {'PASS' if state.responsive_passed else 'FAIL'}")
        print(f"13. Console Errors:               {state.console_errors}")
        print(f"14. Broken Images:                {state.broken_images}")
        total_time = round(time.time() - start_time, 2)

        print("\n" + "=" * 60)
        print("EXACT PIPELINE GATE METRICS")
        print("=" * 60)
        print(f"DEPENDENCY_VALIDATION={'PASS' if state.dependency_validation_passed else 'FAIL'}")
        print(f"BUILD={'PASS' if state.build_passed else 'FAIL'}")
        print(f"PREVIEW_RUNNING={'PASS' if state.preview_running else 'FAIL'}")
        print(f"HTTP_STATUS={actual_http_code}")
        print(f"VISUAL_QA_STATUS={state.visual_qa_status}")
        print(f"VISUAL_QA={'PASS' if state.visual_qa_passed else 'FAIL'}")
        print(f"RESPONSIVE={'PASS' if state.responsive_passed else 'FAIL'}")
        print(f"CONSOLE_ERRORS={state.console_errors}")
        print(f"BROKEN_IMAGES={state.broken_images}")
        print(f"WEBSITE_READY={'TRUE' if state.website_ready else 'FALSE'}")
        print("-" * 60)
        print(f"Actual Preview URL:           {state.local_url}")
        print(f"Actual HTTP Status:           {actual_http_code}")
        print(f"npm Build Exit Code:          {0 if state.build_passed else 1}")
        print(f"Total Build Time:             {total_time}s")
        print(f"Generated File Count:         {len(generated_files)}")
        print("=" * 60)

if __name__ == "__main__":
    run_e2e()
