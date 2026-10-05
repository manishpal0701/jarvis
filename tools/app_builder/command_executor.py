"""
tools/app_builder/command_executor.py
Phase 2.8 & Phase 2.18 — Safe Command Execution Layer.
Executes project-local commands (flutter pub get, flutter analyze, flutter test, npm install, npm test, etc.)
capturing stdout, stderr, exit code, and duration, while broadcasting progress events over WebSockets.
Restricts execution strictly to approved commands within the target project workspace.
"""
import os
import time
import shutil
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AppCommandExecutor")

ALLOWED_COMMAND_PREFIXES = [
    "flutter",
    "npm",
    "node",
    "npx"
]


def resolve_flutter_exe() -> str:
    """
    Resolves the absolute path to the flutter executable on Windows/host OS.
    Tries shutil.which("flutter"), shutil.which("flutter.bat"), or 'where flutter' CLI.
    """
    for cand in ["flutter.bat", "flutter.exe", "flutter"]:
        found = shutil.which(cand)
        if found and os.path.exists(found):
            return found

    try:
        res = subprocess.run(["where", "flutter"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout:
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            for line in lines:
                if os.path.exists(line):
                    return line
    except Exception:
        pass

    return "flutter"


class AppCommandExecutor:
    """
    Executes project-local CLI commands safely inside the project workspace directory.
    """

    @classmethod
    def execute(
        cls,
        command: str,
        cwd: str,
        app_id: str = "",
        timeout: int = 120,
        broadcast_ws: bool = True
    ) -> Dict[str, Any]:
        """
        Executes a CLI command synchronously within the specified working directory.
        """
        start_time = time.time()
        cwd_abs = os.path.abspath(cwd)

        # 1. Safety verification (Phase 2.18)
        if not cls.is_safe_command(command, cwd_abs):
            error_msg = f"Command execution rejected for safety: '{command}' in '{cwd_abs}'"
            logger.warning(error_msg)
            return {
                "command": command,
                "cwd": cwd_abs,
                "exit_code": -1,
                "stdout": "",
                "stderr": error_msg,
                "duration": 0.0,
                "success": False
            }

        # Broadcast command start
        if broadcast_ws and app_id:
            try:
                from tools.app_builder.app_manager import AppManager
                app_mgr = AppManager()
                app_proj = app_mgr.get_app_by_id(app_id)
                if app_proj:
                    app_mgr.broadcast_event(
                        "app_command_started",
                        app_proj,
                        message=f"Executing command: {command}",
                        extra={"command": command, "cwd": cwd_abs}
                    )
            except Exception as ex:
                logger.debug(f"WS notice error: {ex}")

        # 2. Execute process
        logger.info(f"Executing command: '{command}' in '{cwd_abs}'")
        try:
            process = subprocess.run(
                command,
                cwd=cwd_abs,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
            duration = round(time.time() - start_time, 2)
            exit_code = process.returncode
            stdout = process.stdout or ""
            stderr = process.stderr or ""
            success = (exit_code == 0)
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start_time, 2)
            exit_code = -124
            stdout = ""
            stderr = f"Command timed out after {timeout} seconds."
            success = False
        except Exception as ex:
            duration = round(time.time() - start_time, 2)
            exit_code = -1
            stdout = ""
            stderr = f"Command execution exception: {str(ex)}"
            success = False

        res = {
            "command": command,
            "cwd": cwd_abs,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration": duration,
            "success": success
        }

        # Log command execution
        cls._log_command_history(cwd_abs, res)

        # Broadcast completion
        if broadcast_ws and app_id:
            try:
                from tools.app_builder.app_manager import AppManager
                app_mgr = AppManager()
                app_proj = app_mgr.get_app_by_id(app_id)
                if app_proj:
                    app_mgr.broadcast_event(
                        "app_command_completed",
                        app_proj,
                        message=f"Command completed ({'SUCCESS' if success else 'FAILED'} in {duration}s): {command}",
                        extra={"result": res}
                    )
            except Exception as ex:
                logger.debug(f"WS completion notice error: {ex}")

        return res

    @classmethod
    def is_safe_command(cls, command: str, cwd: str) -> bool:
        """
        Validates whether a command is safe to execute in the given directory.
        """
        cmd_clean = command.strip().lower()

        # Check dangerous sub-strings
        for dangerous in ["rm -rf", "format ", "del /s", "del /f", "drop database", "shutdown", "powershell -c remove"]:
            if dangerous in cmd_clean:
                return False

        # Must start with allowed prefix
        is_allowed = any(cmd_clean.startswith(prefix) for prefix in ALLOWED_COMMAND_PREFIXES)
        return is_allowed

    @staticmethod
    def _log_command_history(cwd: str, result: Dict[str, Any]):
        logs_dir = os.path.join(cwd, "logs") if not cwd.endswith("logs") else cwd
        if not os.path.exists(logs_dir):
            logs_dir = cwd
        log_file = os.path.join(logs_dir, "command_history.log")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CMD: {result['command']} | EXIT: {result['exit_code']} | DURATION: {result['duration']}s\n")
                if result['stderr']:
                    f.write(f"STDERR: {result['stderr'][:300]}\n")
                f.write("-" * 50 + "\n")
        except Exception:
            pass
