import os
import sys
import time

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("  REAL WEBSITE GENERATION TEST: COFFEE SHOP       ")
print("==================================================")

prompt = "Jarvis, ek premium modern coffee shop website bana do."
output_dir = os.path.join(os.getcwd(), "websites", "artisan_coffee_roasters")

from tools.coding.code_assistant import CodeAssistant
assistant = CodeAssistant()

t_start = time.perf_counter()
entry_code, entry_path = assistant.generate_code(prompt, project_dir=output_dir, open_browser=False)
t_end = time.perf_counter() - t_start

print(f"\n[GENERATION FINISHED] Time: {t_end:.2f}s")
print(f"Entry File: {entry_path}")
print(f"Entry Code Sample:\n{entry_code[:300]}...")

from tools.coding.website_state import WebsiteStateManager
active = WebsiteStateManager.get_instance().get_active_website()
print(f"\n[ACTIVE STATE MANAGER]: {active}")

from tools.coding.workspace_manager import WorkspaceManager
ws = WorkspaceManager.get_instance()
print(f"[WORKSPACE FILES STORED]: {list(ws.files_content.keys())}")

print("==================================================")
print("  COFFEE SHOP GENERATION TEST COMPLETE           ")
print("==================================================")
