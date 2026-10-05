"""
tools/app_builder/flutter_runtime.py
Phase 5 — Real Flutter Build & Runtime Execution Engine.
Executes real host commands (`flutter --version`, `flutter pub get`, `flutter analyze`, `flutter build apk --debug`, `flutter devices`, `flutter run`).
Physically verifies build outputs (`app-debug.apk`) on disk and handles device detection/launch states.
"""
import os
import re
import time
import logging
from typing import Dict, Any, List, Optional
from tools.app_builder.command_executor import AppCommandExecutor

logger = logging.getLogger("FlutterRuntime")


class FlutterRuntime:
    """
    Manages physical Flutter SDK command execution, static code analysis,
    Android debug/release APK compilation, physical artifact validation, and device runtime launch.
    """

    @classmethod
    def check_flutter(cls, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `flutter --version` on host system.
        """
        res = AppCommandExecutor.execute("flutter --version", cwd=os.getcwd(), app_id=app_id, timeout=30)
        logger.info(f"[FLUTTER_RUNTIME] check_flutter exit_code={res.get('exit_code')} success={res.get('success')}")
        return res

    @classmethod
    def pub_get(cls, frontend_dir: str, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `flutter pub get` inside frontend directory.
        """
        abs_frontend = os.path.abspath(frontend_dir)
        if not os.path.exists(abs_frontend):
            return {"success": False, "exit_code": -1, "stderr": f"Directory not found: {abs_frontend}", "stdout": "", "duration_ms": 0}

        logger.info(f"[FLUTTER_RUNTIME] pub_get path='{abs_frontend}'")
        res = AppCommandExecutor.execute("flutter pub get", cwd=abs_frontend, app_id=app_id, timeout=120)
        return res

    @classmethod
    def analyze(cls, frontend_dir: str, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `flutter analyze` inside frontend directory.
        """
        abs_frontend = os.path.abspath(frontend_dir)
        if not os.path.exists(abs_frontend):
            return {"success": False, "exit_code": -1, "stderr": f"Directory not found: {abs_frontend}", "stdout": "", "duration_ms": 0}

        logger.info(f"[FLUTTER_RUNTIME] analyze path='{abs_frontend}'")
        res = AppCommandExecutor.execute("flutter analyze", cwd=abs_frontend, app_id=app_id, timeout=120)
        return res

    @classmethod
    def build_debug_apk(cls, frontend_dir: str, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `flutter build apk --debug` inside frontend directory.
        Physically verifies existence and non-zero size of `app-debug.apk`.
        """
        abs_frontend = os.path.abspath(frontend_dir)
        if not os.path.exists(abs_frontend):
            return {
                "success": False,
                "exit_code": -1,
                "stderr": f"Directory not found: {abs_frontend}",
                "apk_path": None,
                "apk_exists": False,
                "apk_size": 0
            }

        logger.info(f"[FLUTTER_RUNTIME] build_debug_apk path='{abs_frontend}'")
        
        # Ensure Android Gradle project structure is initialized
        has_android_gradle = (
            os.path.exists(os.path.join(abs_frontend, "android")) or
            os.path.exists(os.path.join(abs_frontend, "android", "build.gradle")) or
            os.path.exists(os.path.join(abs_frontend, "android", "build.gradle.kts"))
        )
        if not has_android_gradle:
            logger.info("[FLUTTER_RUNTIME] android gradle files missing, running flutter create . to initialize Gradle structure")
            AppCommandExecutor.execute("flutter create --org com.jarvis .", cwd=abs_frontend, app_id=app_id, timeout=120)
            AppCommandExecutor.execute("flutter pub get", cwd=abs_frontend, app_id=app_id, timeout=120)

        start_time = time.time()
        res = AppCommandExecutor.execute("flutter build apk --debug", cwd=abs_frontend, app_id=app_id, timeout=300)
        duration_ms = int((time.time() - start_time) * 1000)

        # Check physical output locations for app-debug.apk
        possible_paths = [
            os.path.join(abs_frontend, "build", "app", "outputs", "flutter-apk", "app-debug.apk"),
            os.path.join(abs_frontend, "build", "app", "outputs", "apk", "debug", "app-debug.apk"),
            os.path.join(abs_frontend, "build", "outputs", "apk", "debug", "app-debug.apk")
        ]

        apk_path = None
        apk_exists = False
        apk_size = 0

        for p in possible_paths:
            if os.path.exists(p):
                apk_path = os.path.abspath(p)
                apk_exists = True
                apk_size = os.path.getsize(p)
                break

        success = res.get("success", False) and apk_exists and apk_size > 0

        logger.info(
            f"[FLUTTER_RUNTIME] build_debug_apk_complete success={success} "
            f"apk_exists={apk_exists} apk_size={apk_size} duration_ms={duration_ms}"
        )

        return {
            "success": success,
            "exit_code": res.get("exit_code", -1),
            "stdout": res.get("stdout", ""),
            "stderr": res.get("stderr", ""),
            "duration_ms": duration_ms,
            "apk_path": apk_path,
            "apk_exists": apk_exists,
            "apk_size": apk_size
        }

    @classmethod
    def build_release_apk(cls, frontend_dir: str, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `flutter build apk --release` inside frontend directory.
        """
        abs_frontend = os.path.abspath(frontend_dir)
        logger.info(f"[FLUTTER_RUNTIME] build_release_apk path='{abs_frontend}'")
        res = AppCommandExecutor.execute("flutter build apk --release", cwd=abs_frontend, app_id=app_id, timeout=300)
        return res

    @classmethod
    def detect_devices(cls, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `flutter devices` on host machine to detect connected Android physical devices or emulators.
        Does NOT fake device detection.
        """
        logger.info("[FLUTTER_RUNTIME] detect_devices")
        res = AppCommandExecutor.execute("flutter devices", cwd=os.getcwd(), app_id=app_id, timeout=30)
        
        devices = []
        stdout = res.get("stdout", "")
        if res.get("success") and stdout:
            lines = stdout.splitlines()
            for line in lines:
                # Example: "sdk gphone64 x86 64 (mobile) • emulator-5554 • android-x64 • Android 12 (API 31) (emulator)"
                if "•" in line and not line.startswith("Found") and not line.startswith("No devices"):
                    parts = [p.strip() for p in line.split("•")]
                    if len(parts) >= 2:
                        dev_name = parts[0]
                        dev_id = parts[1]
                        platform = parts[2] if len(parts) > 2 else ""
                        devices.append({"id": dev_id, "name": dev_name, "platform": platform, "raw": line})

        has_devices = len(devices) > 0
        logger.info(f"[FLUTTER_RUNTIME] detect_devices count={len(devices)}")
        return {
            "success": res.get("success", False),
            "has_devices": has_devices,
            "devices": devices,
            "stdout": stdout,
            "stderr": res.get("stderr", "")
        }

    @classmethod
    def run_app(cls, frontend_dir: str, device_id: Optional[str] = None, app_id: str = "") -> Dict[str, Any]:
        """
        Executes `flutter run -d <device_id>` if an Android device/emulator is detected.
        If no device is available, sets status = BLOCKED without falsely reporting PASS.
        """
        abs_frontend = os.path.abspath(frontend_dir)
        det = cls.detect_devices(app_id=app_id)

        if not det["has_devices"] and not device_id:
            logger.info("[FLUTTER_RUNTIME] run_app BLOCKED: No Android device/emulator available")
            return {
                "success": False,
                "status": "BLOCKED",
                "reason": "No Android device/emulator available",
                "detail": "flutter devices reported 0 active devices/emulators"
            }

        target_device = device_id or det["devices"][0]["id"]
        cmd = f"flutter run -d {target_device}"
        logger.info(f"[FLUTTER_RUNTIME] run_app cmd='{cmd}' path='{abs_frontend}'")
        res = AppCommandExecutor.execute(cmd, cwd=abs_frontend, app_id=app_id, timeout=180)

        return {
            "success": res.get("success", False),
            "status": "PASS" if res.get("success") else "FAILED",
            "device_id": target_device,
            "stdout": res.get("stdout", ""),
            "stderr": res.get("stderr", "")
        }
