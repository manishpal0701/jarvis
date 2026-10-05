"""
tools/app_builder/ide_interfaces.py
Phase 2.5, Phase 2.12, Phase 2.13, Phase 2.1 — IDE Automation Interfaces for Android Studio (Flutter) and VS Code (Node.js).
Provides concrete runners to launch target workspaces in appropriate IDEs and execute build pipelines.
"""
import os
import time
import shutil
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("IDEInterfaces")


def resolve_android_studio_path() -> Optional[str]:
    """
    Dynamically locates Android Studio executable on Windows/host OS.
    Checks PATH via shutil.which, environment variables, and standard installation directories.
    """
    # 1. Check PATH
    for name in ["studio64.exe", "studio.exe", "studio64", "studio"]:
        found = shutil.which(name)
        if found and os.path.exists(found):
            logger.info(f"[APP_IDE] ide=ANDROID_STUDIO executable='{found}' status=FOUND")
            return found

    # 2. Check environment variables
    env_paths = [os.environ.get("ANDROID_STUDIO_PATH"), os.environ.get("STUDIO_PATH")]
    for ep in env_paths:
        if ep and os.path.exists(ep):
            logger.info(f"[APP_IDE] ide=ANDROID_STUDIO executable='{ep}' status=FOUND")
            return ep

    # 3. Standard Windows install paths
    pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    pf86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    local_appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local")

    candidates = [
        os.path.join(pf, "Android", "Android Studio", "bin", "studio64.exe"),
        os.path.join(pf, "Android", "Android Studio", "bin", "studio.exe"),
        os.path.join(pf86, "Android", "Android Studio", "bin", "studio64.exe"),
        os.path.join(local_appdata, "Programs", "Android Studio", "bin", "studio64.exe"),
        os.path.join(local_appdata, "Android", "Android Studio", "bin", "studio64.exe")
    ]

    for cand in candidates:
        if os.path.exists(cand):
            logger.info(f"[APP_IDE] ide=ANDROID_STUDIO executable='{cand}' status=FOUND")
            return cand

    logger.warning("[APP_IDE] ide=ANDROID_STUDIO status=NOT_FOUND")
    return None


def resolve_vscode_path() -> Optional[str]:
    """
    Dynamically locates VS Code executable on Windows/host OS.
    """
    for name in ["code.cmd", "code.exe", "code"]:
        found = shutil.which(name)
        if found and os.path.exists(found):
            logger.info(f"[APP_IDE] ide=VS_CODE executable='{found}' status=FOUND")
            return found

    pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    pf86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    local_appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local")

    candidates = [
        os.path.join(local_appdata, "Programs", "Microsoft VS Code", "Code.exe"),
        os.path.join(local_appdata, "Programs", "Microsoft VS Code", "bin", "code.cmd"),
        os.path.join(pf, "Microsoft VS Code", "Code.exe"),
        os.path.join(pf, "Microsoft VS Code", "bin", "code.cmd"),
        os.path.join(pf86, "Microsoft VS Code", "Code.exe")
    ]

    for cand in candidates:
        if os.path.exists(cand):
            logger.info(f"[APP_IDE] ide=VS_CODE executable='{cand}' status=FOUND")
            return cand

    logger.warning("[APP_IDE] ide=VS_CODE status=NOT_FOUND")
    return None


class FlutterAndroidStudioRunner(ABC):
    """
    Abstract interface for Android Studio IDE automation & Flutter mobile app runner.
    """

    @abstractmethod
    def create_flutter_project(self, project_name: str, target_dir: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_dart_code(self, project_dir: str, brief: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def build_flutter_apk(self, project_dir: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def open_in_android_studio(self, project_dir: str) -> Dict[str, Any]:
        pass


class NodeVSCodeRunner(ABC):
    """
    Abstract interface for VS Code IDE automation & Node.js backend runner.
    """

    @abstractmethod
    def create_node_project(self, project_name: str, target_dir: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_backend_code(self, project_dir: str, brief: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def run_npm_install(self, project_dir: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def open_in_vscode(self, project_dir: str) -> Dict[str, Any]:
        pass


class ConcreteFlutterAndroidStudioRunner(FlutterAndroidStudioRunner):
    """
    Concrete implementation launching Android Studio for Flutter frontend workspaces.
    """

    def create_flutter_project(self, project_name: str, target_dir: str) -> Dict[str, Any]:
        from tools.app_builder.flutter_generator import FlutterProjectGenerator
        res = FlutterProjectGenerator.create_real_flutter_project(target_dir, project_name)
        if res["success"]:
            plan = {"app_name": project_name, "sanitized_name": project_name.lower(), "domain": "item"}
            files = FlutterProjectGenerator.generate_frontend(target_dir, plan)
            return {"status": "SUCCESS", "files_created": len(files), "target_dir": target_dir}
        return {"status": "FAILED", "error": res.get("error"), "target_dir": target_dir}

    def generate_dart_code(self, project_dir: str, brief: Dict[str, Any]) -> Dict[str, Any]:
        from tools.app_builder.flutter_generator import FlutterProjectGenerator
        files = FlutterProjectGenerator.generate_frontend(project_dir, brief)
        return {"status": "SUCCESS", "files_created": len(files)}

    def build_flutter_apk(self, project_dir: str) -> Dict[str, Any]:
        from tools.app_builder.command_executor import AppCommandExecutor
        return AppCommandExecutor.execute("flutter build apk", cwd=project_dir)

    def open_in_android_studio(self, project_dir: str) -> Dict[str, Any]:
        """
        Attempts to launch Android Studio targeting the Flutter frontend workspace directory.
        Performs physical filesystem checks for frontend/, pubspec.yaml, and android/.
        """
        abs_path = os.path.abspath(project_dir)
        if not os.path.exists(os.path.join(abs_path, "pubspec.yaml")) and os.path.exists(os.path.join(abs_path, "frontend", "pubspec.yaml")):
            abs_path = os.path.join(abs_path, "frontend")

        pubspec = os.path.join(abs_path, "pubspec.yaml")
        android_dir = os.path.join(abs_path, "android")

        # Step 8 Verification: Ensure physical Flutter files exist
        if not (os.path.exists(abs_path) and os.path.exists(pubspec) and os.path.exists(android_dir)):
            error_msg = f"Cannot open Android Studio: Required Flutter project files missing in '{abs_path}'"
            logger.error(f"[APP_IDE] stage=ANDROID_STUDIO_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
            return {
                "success": False,
                "ide": "Android Studio",
                "project_dir": abs_path,
                "error": error_msg
            }

        studio_exe = resolve_android_studio_path()
        if not studio_exe or not os.path.exists(studio_exe):
            error_msg = f"Android Studio executable not found on system: {studio_exe}"
            logger.error(f"[APP_IDE] stage=ANDROID_STUDIO_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
            return {
                "success": False,
                "ide": "Android Studio",
                "project_dir": abs_path,
                "error": error_msg
            }

        logger.info(f"[APP_RUNTIME] stage=ANDROID_STUDIO_RESOLVE path={studio_exe}")
        logger.info(f"[APP_RUNTIME] stage=ANDROID_STUDIO_LAUNCH_START path={abs_path}")
        logger.info(f"Opening Flutter project in Android Studio: '{studio_exe}' '{abs_path}'")
        try:
            # Launch in background subprocess without shell=True so exact executable path is run
            proc = subprocess.Popen([studio_exe, abs_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            poll_res = proc.poll()
            if poll_res is not None and poll_res != 0:
                error_msg = f"Android Studio process failed to stay running (exit code {poll_res})"
                logger.error(f"[APP_IDE] stage=ANDROID_STUDIO_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
                return {
                    "success": False,
                    "ide": "Android Studio",
                    "project_dir": abs_path,
                    "error": error_msg
                }

            logger.info(f"[APP_RUNTIME] stage=ANDROID_STUDIO_LAUNCH_SUCCESS pid={proc.pid} workspace={abs_path}")
            logger.info(f"[APP_IDE] stage=ANDROID_STUDIO_LAUNCH path={abs_path} executable='{studio_exe}' status=STARTED pid={proc.pid}")
            return {
                "success": True,
                "ide": "Android Studio",
                "executable": studio_exe,
                "project_dir": abs_path,
                "pid": proc.pid,
                "message": f"Opened in Android Studio at {abs_path}"
            }
        except Exception as ex:
            error_msg = f"Failed to spawn Android Studio process: {ex}"
            logger.error(f"[APP_IDE] stage=ANDROID_STUDIO_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
            return {
                "success": False,
                "ide": "Android Studio",
                "project_dir": abs_path,
                "error": error_msg
            }


class ConcreteNodeVSCodeRunner(NodeVSCodeRunner):
    """
    Concrete implementation launching VS Code for Node.js backend workspaces.
    """

    def create_node_project(self, project_name: str, target_dir: str) -> Dict[str, Any]:
        logger.info(f"[APP_RUNTIME] stage=NODE_BACKEND_CREATE_START path={target_dir}")
        from tools.app_builder.node_generator import NodeProjectGenerator
        plan = {"app_name": project_name, "domain": "item"}
        files = NodeProjectGenerator.generate_backend(target_dir, plan)
        return {"status": "SUCCESS", "files_created": len(files), "target_dir": target_dir}

    def generate_backend_code(self, project_dir: str, brief: Dict[str, Any]) -> Dict[str, Any]:
        from tools.app_builder.node_generator import NodeProjectGenerator
        files = NodeProjectGenerator.generate_backend(project_dir, brief)
        return {"status": "SUCCESS", "files_created": len(files)}

    def run_npm_install(self, project_dir: str) -> Dict[str, Any]:
        from tools.app_builder.command_executor import AppCommandExecutor
        return AppCommandExecutor.execute("npm install", cwd=project_dir)

    def open_in_vscode(self, project_dir: str) -> Dict[str, Any]:
        """
        Launches VS Code targeting the Node.js backend workspace directory.
        """
        abs_path = os.path.abspath(project_dir)
        if not os.path.exists(os.path.join(abs_path, "package.json")) and os.path.exists(os.path.join(abs_path, "backend", "package.json")):
            abs_path = os.path.join(abs_path, "backend")

        pkg_json = os.path.join(abs_path, "package.json")

        if not (os.path.exists(abs_path) and os.path.exists(pkg_json)):
            error_msg = f"Cannot open VS Code: Node.js backend package.json missing in '{abs_path}'"
            logger.error(f"[APP_IDE] stage=VSCODE_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
            return {
                "success": False,
                "ide": "VS Code",
                "project_dir": abs_path,
                "error": error_msg
            }

        vscode_exe = resolve_vscode_path()
        if not vscode_exe or not os.path.exists(vscode_exe):
            error_msg = f"VS Code executable not found on system: {vscode_exe}"
            logger.error(f"[APP_IDE] stage=VSCODE_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
            return {
                "success": False,
                "ide": "VS Code",
                "project_dir": abs_path,
                "error": error_msg
            }

        logger.info(f"Opening Node.js backend in VS Code: '{vscode_exe}' '{abs_path}'")
        try:
            is_cmd = vscode_exe.lower().endswith(".cmd") or vscode_exe.lower().endswith(".bat")
            proc = subprocess.Popen([vscode_exe, abs_path], shell=is_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            poll_res = proc.poll()
            if poll_res is not None and poll_res != 0:
                error_msg = f"VS Code process failed to stay running (exit code {poll_res})"
                logger.error(f"[APP_IDE] stage=VSCODE_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
                return {
                    "success": False,
                    "ide": "VS Code",
                    "project_dir": abs_path,
                    "error": error_msg
                }

            logger.info(f"[APP_RUNTIME] stage=VSCODE_LAUNCH_SUCCESS pid={proc.pid} workspace={abs_path}")
            logger.info(f"[APP_IDE] stage=VSCODE_LAUNCH path={abs_path} executable='{vscode_exe}' status=STARTED pid={proc.pid}")
            return {
                "success": True,
                "ide": "VS Code",
                "executable": vscode_exe,
                "project_dir": abs_path,
                "pid": proc.pid,
                "message": f"Opened in VS Code at {abs_path}"
            }
        except Exception as ex:
            error_msg = f"Failed to spawn VS Code process: {ex}"
            logger.error(f"[APP_IDE] stage=VSCODE_LAUNCH path={abs_path} status=FAILED reason='{error_msg}'")
            return {
                "success": False,
                "ide": "VS Code",
                "project_dir": abs_path,
                "error": error_msg
            }
