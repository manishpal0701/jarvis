import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import urllib.request
import json
import threading
import time
import tempfile
import os
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager

def run_sse_tracer():
    ws = WorkspaceManager.get_instance()
    ws.ensure_started()
    url = f"http://127.0.0.1:{ws.port}/api/stream"

    events_captured = []

    def listen_sse():
        try:
            req = urllib.request.urlopen(url)
            buffer = ""
            while True:
                line = req.readline().decode('utf-8')
                if not line:
                    break
                if line.startswith("data: "):
                    payload = line[6:].strip()
                    try:
                        data = json.loads(payload)
                        events_captured.append(data)
                        first100 = payload[:100]
                        print(f"[CLIENT RECEIVE] Event: {data.get('type')} | Length: {len(payload)} | First 100: {first100}")
                    except Exception as e:
                        pass
        except Exception as e:
            print("SSE listener error:", e)

    t = threading.Thread(target=listen_sse, daemon=True)
    t.start()
    time.sleep(1)

    assistant = CodeAssistant()
    test_dir = tempfile.mkdtemp()
    print("\n--- TRIGGERING STANDALONE CODE GENERATION ---")
    code, path = assistant.generate_code("calculator", project_dir=test_dir)
    time.sleep(1)

    print("\n--- TRACE SUMMARY OF SSE EVENTS ---")
    for idx, evt in enumerate(events_captured):
        event_name = evt.get("type")
        raw_json = json.dumps(evt)
        print(f"{idx+1}. Event name: {event_name} | Length: {len(raw_json)} | First 100 chars: {raw_json[:100]}")

if __name__ == "__main__":
    run_sse_tracer()
