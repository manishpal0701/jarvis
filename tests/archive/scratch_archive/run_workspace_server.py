import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.workspace_manager import WorkspaceManager

ws = WorkspaceManager.get_instance()
ws.ensure_started()
print(f"Workspace Server running at http://127.0.0.1:{ws.port}")

while True:
    time.sleep(1)
