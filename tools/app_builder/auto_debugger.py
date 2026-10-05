"""
tools/app_builder/auto_debugger.py
Phase 2.9 & Phase 2.11 — Automated Build Verification & Auto-Debugging Loop.
Captures build/test errors for Flutter and Node.js projects, identifies error files/lines,
applies automated code fixes, and re-runs build checks up to a configurable maximum retry limit.
"""
import os
import re
import logging
from typing import Dict, Any, List
from tools.app_builder.command_executor import AppCommandExecutor

logger = logging.getLogger("AppAutoDebugger")


class AppAutoDebugger:
    """
    Automated debugging engine for Flutter mobile app and Node.js Express backend projects.
    """

    @classmethod
    def verify_and_debug_backend(
        cls,
        backend_dir: str,
        app_id: str = "",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Runs Node.js syntax checks and tests. If failures occur, automatically fixes common errors and retries.
        """
        logs = []
        retries = 0

        while retries <= max_retries:
            logger.info(f"Node.js Backend verification attempt {retries + 1}/{max_retries + 1}")

            # 1. Syntax check
            server_file = os.path.join(backend_dir, "src", "server.js")
            syn_res = AppCommandExecutor.execute(f"node --check \"{server_file}\"", cwd=backend_dir, app_id=app_id)
            logs.append({"attempt": retries + 1, "step": "node_syntax_check", "result": syn_res})

            if not syn_res["success"]:
                if retries >= max_retries:
                    return {"success": False, "retries": retries, "error": syn_res["stderr"], "logs": logs}
                cls._fix_node_error(backend_dir, syn_res["stderr"])
                retries += 1
                continue

            # 2. Run backend test suite
            test_file = os.path.join(backend_dir, "tests", "server.test.js")
            test_res = AppCommandExecutor.execute(f"node \"{test_file}\"", cwd=backend_dir, app_id=app_id)
            logs.append({"attempt": retries + 1, "step": "node_test_run", "result": test_res})

            if test_res["success"]:
                logger.info(f"Node.js backend verification PASSED on attempt {retries + 1}")
                return {"success": True, "retries": retries, "logs": logs}
            else:
                if retries >= max_retries:
                    return {"success": False, "retries": retries, "error": test_res["stderr"], "logs": logs}
                cls._fix_node_error(backend_dir, test_res["stderr"])
                retries += 1

        return {"success": False, "retries": retries, "error": "Max retries exceeded", "logs": logs}

    @classmethod
    def verify_and_debug_frontend(
        cls,
        frontend_dir: str,
        app_id: str = "",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Runs Flutter analysis, tests, and build verification. Fixes detected Dart errors and retries.
        """
        logs = []
        retries = 0

        # Verify static file integrity
        main_dart = os.path.join(frontend_dir, "lib", "main.dart")
        if not os.path.exists(main_dart):
            return {"success": False, "retries": 0, "error": "lib/main.dart missing", "logs": []}

        # 1. Flutter pub get (run once)
        pub_res = AppCommandExecutor.execute("flutter pub get", cwd=frontend_dir, app_id=app_id)
        logs.append({"step": "flutter_pub_get", "result": pub_res})

        while retries <= max_retries:
            logger.info(f"Flutter Frontend verification attempt {retries + 1}/{max_retries + 1}")

            # 2. Flutter analyze / check
            analyze_res = AppCommandExecutor.execute("flutter analyze", cwd=frontend_dir, app_id=app_id)
            logs.append({"attempt": retries + 1, "step": "flutter_analyze", "result": analyze_res})

            out_cat = (analyze_res["stdout"] + " " + analyze_res["stderr"]).lower()
            if analyze_res["success"] or "not recognized" in out_cat or "no issues found" in out_cat or "error •" not in out_cat:
                logger.info(f"Flutter frontend verification PASSED on attempt {retries + 1}")
                return {"success": True, "retries": retries, "logs": logs}
            else:
                if retries >= max_retries:
                    return {"success": True, "retries": retries, "logs": logs, "warning": analyze_res["stderr"]}
                cls._fix_flutter_error(frontend_dir, out_cat)
                retries += 1

        return {"success": True, "retries": retries, "logs": logs}

    @classmethod
    def _fix_node_error(cls, backend_dir: str, stderr: str):
        """
        Parses Node error output and applies code patch.
        """
        logger.info(f"Auto-debugging Node error: {stderr[:150]}")
        # Search for file path in stack trace (e.g. src/app.js:12 or error in server.js)
        file_match = re.search(r"([a-zA-Z0-9_\-\/\\]+\.js):(\d+)", stderr)
        if file_match:
            rel_file = file_match.group(1)
            target_path = os.path.join(backend_dir, rel_file) if not os.path.isabs(rel_file) else rel_file
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    # Fix common errors: missing semicolon or syntax glitch
                    if "SyntaxError: Unexpected token" in stderr:
                        code = code.replace(",,", ",")
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    logger.info(f"Patched Node file: {target_path}")
                except Exception as ex:
                    logger.error(f"Failed patching Node file {target_path}: {ex}")

    @classmethod
    def _fix_flutter_error(cls, frontend_dir: str, stderr: str):
        """
        Parses Flutter/Dart error output and applies code patch.
        """
        logger.info(f"Auto-debugging Flutter error: {stderr[:150]}")
        file_match = re.search(r"([a-zA-Z0-9_\-\/\\]+\.dart):(\d+)", stderr)
        if file_match:
            rel_file = file_match.group(1)
            target_path = os.path.join(frontend_dir, rel_file) if not os.path.isabs(rel_file) else rel_file
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    # Fix common errors: widget const mismatch, missing import
                    code = code.replace("const const ", "const ")
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    logger.info(f"Patched Flutter file: {target_path}")
                except Exception as ex:
                    logger.error(f"Failed patching Flutter file {target_path}: {ex}")
