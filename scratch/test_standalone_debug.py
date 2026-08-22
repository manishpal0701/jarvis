import sys
import os
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.code_assistant import CodeAssistant

print("=== EXECUTING COMMAND: ek python calculator program banaa kar ===")
assistant = CodeAssistant()

fake_calc_code = """class Calculator:
    def add(self, a, b):
        return a + b
    def subtract(self, a, b):
        return a - b
"""

with patch.object(assistant.ai_manager, 'generate_response', return_value=fake_calc_code):
    code, path = assistant.generate_code("ek python calculator program banaa kar")

print("\n=== GENERATE_CODE RETURNED ===")
print("Path:", path)
print("Code snippet:\n", code[:200])
