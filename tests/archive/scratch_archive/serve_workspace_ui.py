import time
import os
import sys

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.workspace_manager import WorkspaceManager
ws = WorkspaceManager.get_instance()
ws.port = 5000
ws.open_workspace("src/App.tsx", "tsx")
ws.set_status("Website Ready - 4-Panel IDE Active", "writing")
ws.set_preview_url("http://127.0.0.1:5177", 5177)
ws.set_temporary_share_url("https://random-name.trycloudflare.com (cloudflared CLI required)")

print(f"[WORKSPACE UI SERVER ACTIVE] Listening on http://127.0.0.1:5000")

while True:
    time.sleep(1)
