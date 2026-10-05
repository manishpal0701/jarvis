import json
from tools.app_builder.api_contract_validator import ApiContractValidator

res = ApiContractValidator.validate_project("JARVIS App Projects/ExpenseTracker_Pro_bd885cfe")
print("EXPENSE RESULT:", json.dumps(res, indent=2))
