import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import shutil
import tempfile
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.website_planner import WebsiteProjectPlanner

def run_website_regression():
    ws = WorkspaceManager.get_instance()
    ws.ensure_started()

    print("=" * 60)
    print("REGRESSION TEST: MODERN AI PORTFOLIO WEBSITE GENERATION")
    print("=" * 60)

    test_dir = tempfile.mkdtemp()
    prompt = "Jarvis create a modern AI portfolio website"

    assistant = CodeAssistant()

    emitted_stream_events = []
    original_broadcast = ws._broadcast

    def capture_broadcast(payload):
        if payload.get("type") in ("code_stream", "code_set", "file_start", "file_end", "status_update"):
            emitted_stream_events.append(payload)
        original_broadcast(payload)

    ws._broadcast = capture_broadcast

    try:
        html, output_dir = assistant.build_website(prompt, project_dir=test_dir, open_browser=False)

        required_files = [
            "package.json",
            "vite.config.ts",
            "index.html",
            "src/main.tsx",
            "src/App.tsx",
            "src/index.css",
            "src/components/Navbar.tsx",
            "src/components/Hero.tsx",
            "src/components/Footer.tsx"
        ]

        results = {}
        print("\n--- FILE VERIFICATION REPORT ---")
        for req in required_files:
            fp = os.path.join(output_dir, req)
            exists = os.path.isfile(fp)
            line_count = 0
            if exists:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                    line_count = content.count('\n') + 1

            file_stream_events = [e for e in emitted_stream_events if e.get("file_path") == req and e.get("type") == "code_stream"]
            file_final_events = [e for e in emitted_stream_events if e.get("file_path") == req and e.get("type") == "code_set" and e.get("is_final") is True]

            has_streaming = len(file_stream_events) > 0 or not exists # some small config files get written directly
            status_pass = exists and line_count > 0

            results[req] = {
                "exists": exists,
                "lines": line_count,
                "stream_events": len(file_stream_events),
                "final_event": len(file_final_events) > 0,
                "status": "PASS" if status_pass else "FAIL"
            }

            print(f"File: {req:30} | Exists: {str(exists):5} | Lines: {line_count:4} | Stream Events: {len(file_stream_events):3} | Status: {results[req]['status']}")

        all_passed = all(v["status"] == "PASS" for v in results.values())
        print("\nOverall Website Generation Result:", "PASS" if all_passed else "FAIL")

    finally:
        ws._broadcast = original_broadcast
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    run_website_regression()
