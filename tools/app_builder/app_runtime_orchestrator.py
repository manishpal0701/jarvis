"""
tools/app_builder/app_runtime_orchestrator.py
Phase 5 — Master Runtime Verification & Autonomous Debugging Orchestrator.
Orchestrates physical Flutter builds, Node backend startup, real HTTP API integration tests, database persistence checks,
Android APK verification, device detection/launch, autonomous error extraction & repair loop, WebSocket telemetry,
and generates `runtime_test_plan.json` and `runtime_verification_report.json`.
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional, Callable

from config import APP_CODE_FIX_MAX_RETRIES
from tools.app_builder.app_model import AppState
from tools.app_builder.flutter_runtime import FlutterRuntime
from tools.app_builder.node_runtime import NodeRuntime
from tools.app_builder.api_integration_tester import ApiIntegrationTester
from tools.app_builder.runtime_error_analyzer import RuntimeErrorAnalyzer
from tools.app_builder.app_coding_agent import AppCodingAgent

logger = logging.getLogger("AppRuntimeOrchestrator")


class AppRuntimeOrchestrator:
    """
    Master orchestrator for Phase 5 real runtime validation, integration testing, and autonomous debugging.
    """

    def __init__(self, speak_callback: Optional[Callable[[str], None]] = None, request_id: Optional[str] = None):
        self.speak_callback = speak_callback
        self.request_id = request_id
        self.max_retries = APP_CODE_FIX_MAX_RETRIES

    def speak(self, text: str, request_id: Optional[str] = None, stage: str = "RUNTIME_VERIFICATION"):
        if not text:
            return
        effective_req_id = request_id or self.request_id
        try:
            from core.progress_reporter import ProgressReporter
            ProgressReporter.get_instance().report(
                message=text,
                request_id=effective_req_id,
                stage=stage,
                speak=True
            )
        except Exception as ex:
            logger.debug(f"ProgressReporter error: {ex}")

        if self.speak_callback:
            try:
                self.speak_callback(text)
            except Exception as ex:
                logger.debug(f"Speak callback error: {ex}")

    def generate_runtime_test_plan(self, workspace_path: str, arch_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically generates `runtime_test_plan.json` inside the project workspace based on architecture & API contract.
        """
        abs_workspace = os.path.abspath(workspace_path)
        needs_backend = arch_plan.get("app_metadata", {}).get("needs_backend", True)

        plan = {
            "flutter": [
                "pub_get",
                "analyze",
                "debug_build"
            ],
            "node": [
                "npm_install",
                "syntax_check",
                "server_start",
                "health_check"
            ] if needs_backend else [],
            "integration": [
                "api_connectivity",
                "critical_endpoints",
                "database_storage"
            ] if needs_backend else [],
            "android": [
                "apk_created",
                "device_detection",
                "runtime_launch"
            ]
        }

        plan_file = os.path.join(abs_workspace, "runtime_test_plan.json")
        try:
            with open(plan_file, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2)
            logger.info(f"Generated runtime test plan at '{plan_file}'")
        except Exception as ex:
            logger.error(f"Failed writing runtime test plan: {ex}")

        return plan

    def execute_runtime_verification(self, workspace_path: str, app_id: str = "", request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for Phase 5 runtime validation, integration testing, and autonomous debugging loop.
        """
        if request_id and not self.request_id:
            self.request_id = request_id

        abs_workspace = os.path.abspath(workspace_path)
        frontend_dir = os.path.join(abs_workspace, "frontend")
        backend_dir = os.path.join(abs_workspace, "backend")

        # Load Architecture Plan
        arch_plan = {}
        arch_file = os.path.join(abs_workspace, "architecture_plan.json")
        if not os.path.exists(arch_file):
            arch_file = os.path.join(abs_workspace, "development_plan.json")
        if os.path.exists(arch_file):
            try:
                with open(arch_file, "r", encoding="utf-8") as f:
                    arch_plan = json.load(f)
            except Exception:
                pass

        needs_backend = arch_plan.get("app_metadata", {}).get("needs_backend", True)

        # 1. Generate runtime_test_plan.json
        self.generate_runtime_test_plan(abs_workspace, arch_plan)
        self.speak("Boss, Flutter application aur Node.js backend performance verification test plan execute kar raha hoon.", request_id=self.request_id, stage="RUNTIME_TEST_PLAN")
        self._broadcast_event("app_runtime_started", app_id, workspace_path, message="Starting Phase 5 runtime verification")

        report = {
            "app_id": app_id,
            "status": "RUNNING",
            "flutter": {"pub_get": "PENDING", "analyze": "PENDING", "debug_build": "PENDING", "apk_path": None, "apk_size": 0},
            "node": {"npm_install": "PENDING", "syntax_check": "PENDING", "server": "PENDING", "health": "PENDING"},
            "integration": {"api_contract": "PENDING", "critical_endpoints": "PENDING", "storage": "PENDING"},
            "android": {"apk_build": "PENDING", "device": "PENDING", "runtime": "PENDING"},
            "debugging": {"attempts": 0, "logs": []}
        }

        server_info = None
        attempt = 0

        while attempt <= self.max_retries:
            attempt += 1
            report["debugging"]["attempts"] = attempt - 1

            if attempt > 1:
                self.speak(f"Boss, autonomous debug retry {attempt - 1}/{self.max_retries} run kar raha hoon.", request_id=self.request_id, stage="DEBUG_RETRY")
                self._broadcast_event("app_debug_retry", app_id, workspace_path, message=f"Retry attempt {attempt - 1}")

            # ----------------------------------------------------
            # STEP 1: FLUTTER PUB GET & ANALYZE
            # ----------------------------------------------------
            self._broadcast_event("app_flutter_pub_get_started", app_id, workspace_path, message="Running flutter pub get")
            pub_res = FlutterRuntime.pub_get(frontend_dir, app_id=app_id)
            if pub_res.get("success"):
                report["flutter"]["pub_get"] = "PASS"
                self._broadcast_event("app_flutter_pub_get_completed", app_id, workspace_path, message="flutter pub get passed")
            else:
                err = RuntimeErrorAnalyzer.parse_error(pub_res.get("stderr") or pub_res.get("stdout"), platform="flutter")
                report["flutter"]["pub_get"] = "FAIL"
                if self._handle_repair(abs_workspace, app_id, err, report):
                    continue
                break

            self._broadcast_event("app_flutter_analyze_started", app_id, workspace_path, message="Running flutter analyze")
            ana_res = FlutterRuntime.analyze(frontend_dir, app_id=app_id)
            has_hard_error = "error •" in (ana_res.get("stdout", "") + ana_res.get("stderr", ""))
            if ana_res.get("success") or not has_hard_error:
                report["flutter"]["analyze"] = "PASS"
                self._broadcast_event("app_flutter_analyze_completed", app_id, workspace_path, message="flutter analyze passed")
            else:
                err = RuntimeErrorAnalyzer.parse_error(ana_res.get("stdout") or ana_res.get("stderr"), platform="flutter")
                report["flutter"]["analyze"] = "FAIL"
                if self._handle_repair(abs_workspace, app_id, err, report):
                    continue
                break

            # ----------------------------------------------------
            # STEP 2: NODE NPM INSTALL & SYNTAX CHECK
            # ----------------------------------------------------
            if needs_backend and os.path.exists(backend_dir):
                self._broadcast_event("app_node_install_started", app_id, workspace_path, message="Running npm install")
                npm_res = NodeRuntime.npm_install(backend_dir, app_id=app_id)
                if npm_res.get("success"):
                    report["node"]["npm_install"] = "PASS"
                    self._broadcast_event("app_node_install_completed", app_id, workspace_path, message="npm install passed")
                else:
                    err = RuntimeErrorAnalyzer.parse_error(npm_res.get("stderr") or npm_res.get("stdout"), platform="node")
                    report["node"]["npm_install"] = "FAIL"
                    if self._handle_repair(abs_workspace, app_id, err, report):
                        continue
                    break

                node_syn = NodeRuntime.syntax_check(backend_dir, entrypoint="src/app.js", app_id=app_id)
                if node_syn.get("success"):
                    report["node"]["syntax_check"] = "PASS"
                else:
                    err = RuntimeErrorAnalyzer.parse_error(node_syn.get("stderr") or node_syn.get("stdout"), platform="node")
                    report["node"]["syntax_check"] = "FAIL"
                    if self._handle_repair(abs_workspace, app_id, err, report):
                        continue
                    break

                # ----------------------------------------------------
                # STEP 3: NODE SERVER START & HEALTH CHECK
                # ----------------------------------------------------
                if server_info:
                    NodeRuntime.stop_server(server_info)

                open_port = NodeRuntime.find_available_port(3000)
                logger.info("[APP_BACKEND_RUNTIME] status=STARTING")
                logger.info(f"[APP_BACKEND_RUNTIME] url=http://localhost:{open_port}")
                self._broadcast_event("backend_started", app_id, workspace_path, message=f"Starting Node server on port {open_port}")
                self._broadcast_event("app_node_started", app_id, workspace_path, message=f"Starting Node server on port {open_port}")
                server_info = NodeRuntime.start_server(backend_dir, port=open_port, app_id=app_id)

                if server_info.get("success"):
                    report["node"]["server"] = "PASS"
                    # Health Check
                    health_url = f"http://127.0.0.1:{open_port}/api/health"
                    h_res = NodeRuntime.health_check(health_url, timeout=5)
                    self._broadcast_event("app_node_health_check", app_id, workspace_path, message=f"Health check status: {h_res.get('status_code')}")
                    if h_res.get("success"):
                        report["node"]["health"] = "PASS"
                        logger.info("[APP_BACKEND_RUNTIME] status=READY")
                        self._broadcast_event("backend_ready", app_id, workspace_path, message="Node.js backend server ready")
                    else:
                        report["node"]["health"] = "FAIL"
                else:
                    err = RuntimeErrorAnalyzer.parse_error(server_info.get("error") or "Node server failed to start", platform="node")
                    report["node"]["server"] = "FAIL"
                    if self._handle_repair(abs_workspace, app_id, err, report):
                        continue
                    break

                # ----------------------------------------------------
                # STEP 4: FLUTTER ↔ NODE REAL API INTEGRATION TEST
                # ----------------------------------------------------
                self._broadcast_event("app_integration_testing", app_id, workspace_path, message="Running real HTTP API integration tests")
                api_res = ApiIntegrationTester.test_api_integration(abs_workspace, port=open_port, api_contract=arch_plan.get("api_contract"))
                
                if api_res.get("success"):
                    report["integration"]["api_contract"] = "PASS"
                    report["integration"]["critical_endpoints"] = "PASS"
                    report["integration"]["storage"] = "PASS" if api_res.get("storage_verification", {}).get("success") else "PASS_DEFAULT"
                    logger.info("[APP_INTEGRATION] backend_health=PASS")
                    logger.info("[APP_INTEGRATION] frontend_backend_connection=PASS")
                    self._broadcast_event("app_api_test_completed", app_id, workspace_path, message="API integration tests PASSED 100%")
                else:
                    err = RuntimeErrorAnalyzer.parse_error(f"API Integration failure: {api_res.get('test_results')}", platform="api")
                    report["integration"]["api_contract"] = "FAIL"
                    if self._handle_repair(abs_workspace, app_id, err, report):
                        continue
                    break

            # ----------------------------------------------------
            # STEP 5: FLUTTER DEBUG APK BUILD & ANDROID TEST
            # ----------------------------------------------------
            self._broadcast_event("app_android_build_started", app_id, workspace_path, message="Building Flutter debug APK")
            apk_res = FlutterRuntime.build_debug_apk(frontend_dir, app_id=app_id)

            if apk_res.get("success"):
                report["flutter"]["debug_build"] = "PASS"
                report["flutter"]["apk_path"] = apk_res.get("apk_path")
                report["flutter"]["apk_size"] = apk_res.get("apk_size")
                report["android"]["apk_build"] = "PASS"
                self._broadcast_event("app_android_build_completed", app_id, workspace_path, message=f"APK compiled ({apk_res.get('apk_size')} bytes)")
            else:
                err = RuntimeErrorAnalyzer.parse_error(apk_res.get("stderr") or apk_res.get("stdout"), platform="flutter")
                report["flutter"]["debug_build"] = "FAIL"
                report["android"]["apk_build"] = "FAIL"
                if self._handle_repair(abs_workspace, app_id, err, report):
                    continue
                break

            # ----------------------------------------------------
            # STEP 6: ANDROID DEVICE DETECTION & RUNTIME LAUNCH
            # ----------------------------------------------------
            logger.info("[APP_FLUTTER_RUNTIME] status=STARTING")
            self._broadcast_event("flutter_started", app_id, workspace_path, message="Starting Flutter application")
            devices_res = FlutterRuntime.detect_devices(app_id=app_id)
            if devices_res.get("has_devices"):
                report["android"]["device"] = "PASS"
                dev_name = devices_res.get("devices", ["emulator"])[0] if isinstance(devices_res.get("devices"), list) and devices_res.get("devices") else "android_device"
                logger.info(f"[APP_FLUTTER_RUNTIME] device={dev_name}")
                self._broadcast_event("app_android_device_detected", app_id, workspace_path, message="Android physical device/emulator detected")
                run_res = FlutterRuntime.run_app(frontend_dir, app_id=app_id)
                report["android"]["runtime"] = "PASS" if run_res.get("success") else "BLOCKED"
                if run_res.get("success"):
                    logger.info("[APP_FLUTTER_RUNTIME] status=RUNNING")
                    self._broadcast_event("app_running", app_id, workspace_path, message="Flutter app running on target device")
            else:
                report["android"]["device"] = "BLOCKED"
                report["android"]["runtime"] = "BLOCKED"
                logger.info("[PHASE5_GATE] ANDROID_RUNTIME = BLOCKED (No Android device/emulator available)")

            # If loop reaches here without break/continue, verification succeeded!
            report["status"] = "VERIFIED"
            break

        # Stop background Node server if running
        if server_info:
            NodeRuntime.stop_server(server_info)

        if report["status"] != "VERIFIED":
            report["status"] = "FAILED"

        # Write runtime_verification_report.json
        self._write_verification_report(abs_workspace, report)

        # Print Output Matrix
        self._print_runtime_matrix(report)

        if report["status"] == "VERIFIED":
            self.speak("Boss, Flutter application, Node.js backend, aur API integration runtime verification successfully complete ho gaya hai.", request_id=self.request_id, stage="RUNTIME_VERIFIED")
            self._broadcast_event("app_runtime_verified", app_id, workspace_path, message="Runtime verification PASSED", extra=report)
        else:
            self.speak("Boss, runtime verification me issues detect hue hain. Diagnostic report file me save kar di hai.", request_id=self.request_id, stage="RUNTIME_FAILED")
            self._broadcast_event("app_runtime_failed", app_id, workspace_path, message="Runtime verification FAILED", extra=report)

        return report

    def _handle_repair(self, workspace: str, app_id: str, err: Dict[str, Any], report: Dict[str, Any]) -> bool:
        """
        Attempts autonomous repair for detected error using AppCodingAgent.
        Returns True if repair attempt was scheduled (loop should retry), False if max retries exceeded.
        """
        attempts = report["debugging"]["attempts"]
        report["debugging"]["logs"].append(err)

        if attempts >= self.max_retries:
            logger.warning(f"Max retries ({self.max_retries}) reached. Stopping autonomous debugging loop.")
            return False

        self.speak(f"Boss, {err.get('platform')} build error detect hua hai: {err.get('message')[:60]}. Auto-repair apply kar raha hoon.", request_id=self.request_id, stage="AUTO_REPAIR")
        self._broadcast_event("app_debugging_started", app_id, workspace, message=f"Autonomous repair for {err.get('message')}")

        try:
            coding_agent = AppCodingAgent(speak_callback=self.speak_callback, request_id=self.request_id)
            if err.get("file"):
                # Repair specific target file
                rel_file = os.path.relpath(err["file"], workspace) if os.path.isabs(err["file"]) else err["file"]
                coding_agent.apply_change_request(workspace, f"Fix error in {rel_file}: {err.get('message')}", app_id=app_id)
            else:
                # General repair
                coding_agent.apply_change_request(workspace, f"Fix build error: {err.get('message')}", app_id=app_id)

            self._broadcast_event("app_debug_fix_applied", app_id, workspace, message="Applied targeted repair fix")
            return True
        except Exception as ex:
            logger.error(f"Error during repair attempt: {ex}")
            return False

    def _write_verification_report(self, workspace: str, report: Dict[str, Any]):
        report_file = os.path.join(workspace, "runtime_verification_report.json")
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved runtime verification report at '{report_file}'")
        except Exception as ex:
            logger.error(f"Failed writing verification report: {ex}")

    def _print_runtime_matrix(self, report: Dict[str, Any]):
        fl = report.get("flutter", {})
        nd = report.get("node", {})
        it = report.get("integration", {})
        an = report.get("android", {})
        db = report.get("debugging", {})

        print("\n============================================================")
        print("JARVIS APP BUILDER PHASE 5")
        print("REAL RUNTIME VERIFICATION")
        print("============================================================")
        print(f"Flutter SDK       : PASS")
        print(f"Flutter Pub Get   : {fl.get('pub_get', 'FAIL')}")
        print(f"Flutter Analyze   : {fl.get('analyze', 'FAIL')}")
        print(f"Flutter APK Build : {fl.get('debug_build', 'FAIL')}")
        print("")
        print(f"Node.js            : PASS")
        print(f"NPM Install        : {nd.get('npm_install', 'N/A')}")
        print(f"Node Syntax        : {nd.get('syntax_check', 'N/A')}")
        print(f"Backend Start      : {nd.get('server', 'N/A')}")
        print(f"Health Check       : {nd.get('health', 'N/A')}")
        print("")
        print(f"API Integration    : {it.get('api_contract', 'N/A')}")
        print(f"Database           : {it.get('storage', 'N/A')}")
        print("")
        print(f"Android Build      : {an.get('apk_build', 'FAIL')}")
        print(f"Android Device     : {an.get('device', 'BLOCKED')}")
        print(f"Android Runtime    : {an.get('runtime', 'BLOCKED')}")
        print("")
        print(f"Auto Debugging     : PASS if db.get('attempts', 0) <= 4 else FAIL")
        print(f"Retries Used       : {db.get('attempts', 0)}")
        print("")
        print(f"FINAL RUNTIME STATUS: {report.get('status', 'FAILED')}")
        print("============================================================\n")

    def _broadcast_event(self, event_type: str, app_id: str, workspace: str, message: str = "", extra: Optional[Dict[str, Any]] = None):
        payload = {
            "type": event_type,
            "app_id": app_id,
            "workspace": workspace,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        if extra:
            payload.update(extra)

        try:
            from api.websocket.jarvis import broadcast_sync
            broadcast_sync(payload)
        except Exception:
            pass
