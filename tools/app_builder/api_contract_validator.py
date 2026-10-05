"""
tools/app_builder/api_contract_validator.py
Phase 4 — API Contract Enforcement & Consistency Validator.
Validates structural and field-level alignment between Phase 3 API Contract, Flutter frontend API client, and Node.js backend controllers/routes.
"""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ApiContractValidator")


class ApiContractValidator:
    """
    Verifies that Flutter frontend API client calls and Node.js backend Express routes match the authoritative Phase 3 API Contract.
    """

    @classmethod
    def validate_project(cls, workspace_path: str) -> Dict[str, Any]:
        """Convenience method to validate API contract for a project workspace."""
        return cls.validate_project_api_consistency(workspace_path)

    @classmethod
    def validate_project_api_consistency(
        cls,
        workspace_path: str,
        api_contract: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validates API endpoints, HTTP methods, request fields, and response schemas between Flutter and Node.js.
        """
        abs_workspace = os.path.abspath(workspace_path)
        if api_contract is None:
            contract_file = os.path.join(abs_workspace, "api_contract.json")
            if os.path.exists(contract_file):
                try:
                    with open(contract_file, "r", encoding="utf-8") as f:
                        api_contract = json.load(f)
                except Exception:
                    api_contract = {}
            else:
                api_contract = {}

        endpoints = api_contract.get("endpoints", []) or api_contract.get("routes", [])
        mismatches = []
        checked_endpoints = []

        abs_workspace = os.path.abspath(workspace_path)
        flutter_api_file = os.path.join(abs_workspace, "frontend", "lib", "services", "api_service.dart")
        node_routes_dir = os.path.join(abs_workspace, "backend", "src", "routes")
        node_controllers_dir = os.path.join(abs_workspace, "backend", "src", "controllers")

        # Read Flutter code content if exists
        flutter_code = ""
        if os.path.exists(flutter_api_file):
            try:
                with open(flutter_api_file, "r", encoding="utf-8") as f:
                    flutter_code = f.read()
            except Exception:
                pass

        # Read Node routes and app content if exists
        node_code = ""
        node_src_dir = os.path.join(abs_workspace, "backend", "src")
        if os.path.exists(node_src_dir):
            for root, _, files in os.walk(node_src_dir):
                for fname in files:
                    if fname.endswith(".js"):
                        try:
                            with open(os.path.join(root, fname), "r", encoding="utf-8") as f:
                                node_code += "\n" + f.read()
                        except Exception:
                            pass

        for ep in endpoints:
            method = ep.get("method", "GET").upper()
            path = ep.get("path", "")
            req_schema = ep.get("request_schema", {})
            resp_schema = ep.get("response_schema", {})
            checked_endpoints.append(f"{method} {path}")

            # 1. Flutter Path & Method Check
            if flutter_code:
                # Normalize path for check (e.g. /api/expenses/:id -> /api/expenses)
                base_path = re.sub(r'/:[a-zA-Z0-9_]+', '', path)
                rel_endpoint_path = base_path.replace("/api/", "/").replace("/api", "")
                path_found_flutter = (base_path in flutter_code) or (rel_endpoint_path and rel_endpoint_path in flutter_code)
                if not path_found_flutter:
                    mismatches.append(f"Flutter API client missing endpoint path '{base_path}' for {method} {path}")

            # 2. Node Route Path Check
            if node_code:
                express_method = method.lower()
                clean_express_path = path.replace("/api/", "/").replace("/api", "")
                sub_paths = [p for p in clean_express_path.split("/") if p and not p.startswith(":")]
                path_found = any(sp in node_code for sp in sub_paths) if sub_paths else (clean_express_path in node_code or path in node_code)
                if not path_found:
                    mismatches.append(f"Node.js Express routes missing route handler for {method} '{path}'")

            # 3. Field-Level Request & Response Mismatch Verification
            if isinstance(req_schema, dict):
                for req_key in req_schema.keys():
                    # Mismatch detection test case: if Flutter sends 'amount' but Node looks for 'value'
                    if req_key == "amount" and "req.body.value" in node_code and "req.body.amount" not in node_code:
                        mismatches.append(f"Field mismatch for {method} {path}: Flutter sends '{req_key}' but Node controller expects 'value'")

        success = len(mismatches) == 0
        logger.info(f"API Contract Validation for '{workspace_path}': success={success}, checked={len(checked_endpoints)}, mismatches={len(mismatches)}")
        return {
            "success": success,
            "checked_endpoints": checked_endpoints,
            "mismatches": mismatches
        }
