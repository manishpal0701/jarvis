import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import urllib.request
import json
import threading
import time
import tempfile
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager

def run_investigation():
    ws = WorkspaceManager.get_instance()
    ws.ensure_started()

    print("=" * 60)
    print("LINE 31 VISUAL BUG INVESTIGATION")
    print("=" * 60)

    # Generate a long Python script (50+ lines)
    prompt = "weather app"
    assistant = CodeAssistant()
    test_dir = tempfile.mkdtemp()

    tokens_received = []
    stream_events = []

    def capture_broadcast(data):
        if data.get("type") == "code_stream":
            stream_events.append(data)

    ws._broadcast = capture_broadcast

    code, saved_path = assistant.generate_code(prompt, project_dir=test_dir)

    print(f"1. WorkspaceManager generated code total lines: {code.count('\n') + 1}")
    print(f"2. Total code_stream events received: {len(stream_events)}")

    total_streamed_chars = sum(len(e.get("chunk", "")) for e in stream_events)
    print(f"3. Total accumulated streamed length: {total_streamed_chars} chars")

    lines_streamed = [e.get("line") for e in stream_events if e.get("line")]
    if lines_streamed:
        print(f"4. Max line number streamed: {max(lines_streamed)}")

    print(f"5. Saved file path exists: {os.path.exists(saved_path)}")

if __name__ == "__main__":
    run_investigation()
