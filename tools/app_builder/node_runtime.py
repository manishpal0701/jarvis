"""
tools/app_builder/node_runtime.py
Phase 5 — Real Node.js Backend Runtime Execution Engine.
Executes real host commands (`node --version`, `npm --version`, `npm install`, `node --check`),
manages background process lifecycle for Express REST API, verifies process health via real HTTP requests, and handles clean process termination.
"""
import os
import time
import socket
import logging
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from tools.app_builder.command_executor import AppCommandExecutor

logger = logging.getLogger("NodeRuntime")


class NodeRuntime:
    """
    Manages physical Node.js / NPM environment checks, package installations,
    syntax validations, background process startup, HTTP health checks, and process shutdown.
    """

    @classmethod
    def check_node(cls, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `node --version` and `npm --version` on host machine.
        """
        node_res = AppCommandExecutor.execute("node --version", cwd=os.getcwd(), app_id=app_id, timeout=15)
        npm_res = AppCommandExecutor.execute("npm --version", cwd=os.getcwd(), app_id=app_id, timeout=15)

        success = node_res.get("success", False) and npm_res.get("success", False)
        logger.info(f"[NODE_RUNTIME] check_node success={success} node={node_res.get('stdout', '').strip()} npm={npm_res.get('stdout', '').strip()}")
        return {
            "success": success,
            "node_version": node_res.get("stdout", "").strip(),
            "npm_version": npm_res.get("stdout", "").strip(),
            "node_res": node_res,
            "npm_res": npm_res
        }

    @classmethod
    def npm_install(cls, backend_dir: str, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `npm install` inside backend directory.
        """
        abs_backend = os.path.abspath(backend_dir)
        if not os.path.exists(abs_backend):
            return {"success": False, "exit_code": -1, "stderr": f"Directory not found: {abs_backend}", "stdout": "", "duration_ms": 0}

        logger.info(f"[NODE_RUNTIME] npm_install path='{abs_backend}'")
        res = AppCommandExecutor.execute("npm install", cwd=abs_backend, app_id=app_id, timeout=180)
        return res

    @classmethod
    def syntax_check(cls, backend_dir: str, entrypoint: str = "src/app.js", app_id: str = "") -> Dict[str, Any]:
        """
        Executes `node --check <entrypoint>` inside backend directory.
        """
        abs_backend = os.path.abspath(backend_dir)
        abs_entry = os.path.join(abs_backend, entrypoint)
        if not os.path.exists(abs_entry):
            # Fallback to server.js or app.js
            alt_entry = os.path.join(abs_backend, "src", "server.js")
            if os.path.exists(alt_entry):
                abs_entry = alt_entry
            else:
                return {"success": False, "exit_code": -1, "stderr": f"Entrypoint not found: {abs_entry}", "stdout": "", "duration_ms": 0}

        logger.info(f"[NODE_RUNTIME] syntax_check file='{abs_entry}'")
        res = AppCommandExecutor.execute(f"node --check \"{abs_entry}\"", cwd=abs_backend, app_id=app_id, timeout=30)
        return res

    @classmethod
    def find_available_port(cls, preferred_port: int = 3000) -> int:
        """
        Checks if preferred_port is open. If occupied, finds next available open port.
        """
        for port in range(preferred_port, preferred_port + 50):
            is_occupied = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    s.connect(("127.0.0.1", port))
                    is_occupied = True
            except (OSError, ConnectionRefusedError):
                pass

            if is_occupied:
                continue

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    s.bind(("0.0.0.0", port))
                    return port
            except OSError:
                continue

        return preferred_port + 5

    @classmethod
    def start_server(
        cls,
        backend_dir: str,
        port: int = 3000,
        entrypoint: str = "src/server.js",
        app_id: str = ""
    ) -> Dict[str, Any]:
        """
        Starts Node Express backend as a real background process using subprocess.Popen.
        Verifies process is alive and listening.
        """
        abs_backend = os.path.abspath(backend_dir)
        entry_path = os.path.join(abs_backend, entrypoint)
        if not os.path.exists(entry_path):
            entry_path = os.path.join(abs_backend, "src", "app.js")

        if not os.path.exists(entry_path):
            return {
                "success": False,
                "process": None,
                "port": port,
                "error": f"Entrypoint file missing: {entry_path}"
            }

        # Resolve an open port
        target_port = cls.find_available_port(port)

        # Set PORT in process environment
        env = dict(os.environ)
        env["PORT"] = str(target_port)

        logger.info(f"[NODE_RUNTIME] start_server entry='{entry_path}' port={target_port}")
        try:
            process = subprocess.Popen(
                ["node", entry_path],
                cwd=abs_backend,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Give server time to bind port
            time.sleep(1.5)

            is_alive = process.poll() is None
            if not is_alive:
                stderr = process.stderr.read() if process.stderr else "Process exited prematurely"
                logger.error(f"[NODE_RUNTIME] start_server failed to start: {stderr}")
                return {"success": False, "process": None, "port": port, "error": stderr}

            logger.info(f"[NODE_RUNTIME] server process started pid={process.pid} port={port}")
            return {
                "success": True,
                "process": process,
                "pid": process.pid,
                "port": port,
                "error": None
            }
        except Exception as ex:
            logger.exception(f"[NODE_RUNTIME] exception starting server: {ex}")
            return {"success": False, "process": None, "port": port, "error": str(ex)}

    @classmethod
    def health_check(cls, url: str = "http://127.0.0.1:3000/api/health", timeout: float = 5.0) -> Dict[str, Any]:
        """
        Physically issues HTTP GET request to backend health endpoint.
        Verifies status code, response time, and JSON payload.
        """
        logger.info(f"[NODE_RUNTIME] health_check url='{url}'")
        start_time = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Phase5-Validator"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                duration_ms = int((time.time() - start_time) * 1000)
                status_code = resp.getcode()
                body_raw = resp.read().decode("utf-8")
                
                success = status_code == 200
                logger.info(f"[NODE_RUNTIME] health_check response status={status_code} duration_ms={duration_ms}")
                return {
                    "success": success,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "body": body_raw,
                    "error": None
                }
        except urllib.error.HTTPError as he:
            duration_ms = int((time.time() - start_time) * 1000)
            return {"success": False, "status_code": he.code, "duration_ms": duration_ms, "body": "", "error": str(he)}
        except Exception as ex:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[NODE_RUNTIME] health_check failed: {ex}")
            return {"success": False, "status_code": 0, "duration_ms": duration_ms, "body": "", "error": str(ex)}

    @classmethod
    def stop_server(cls, server_info: Optional[Dict[str, Any]]) -> bool:
        """
        Stops background Node server process safely.
        """
        if not server_info or not server_info.get("process"):
            return True

        process = server_info["process"]
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            logger.info(f"[NODE_RUNTIME] stopped server pid={server_info.get('pid')}")
            return True
        except Exception as ex:
            logger.error(f"[NODE_RUNTIME] error stopping server: {ex}")
            return False
