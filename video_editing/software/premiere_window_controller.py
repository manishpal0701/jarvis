"""
video_editing/software/premiere_window_controller.py
Phase 6 Premiere Pro Window Controller & Launcher.
Detects running Adobe Premiere Pro process, automatically launches Premiere Pro
if not running, restores minimized window, and brings Premiere Pro to the foreground.
"""

import os
import sys
import time
import winreg
import subprocess
import psutil
from typing import Optional

PREMIERE_EXE_NAME = "Adobe Premiere Pro.exe"
MAX_LAUNCH_WAIT_SECS = 60


class PremiereWindowController:
    """
    Manages Premiere Pro process detection, auto-launching, and foreground window activation.
    """

    @classmethod
    def get_running_pid(cls) -> Optional[int]:
        """Returns PID of running Premiere Pro process or None."""
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if PREMIERE_EXE_NAME.lower() in proc.info["name"].lower():
                    return proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                pass
        return None

    @classmethod
    def get_running_exe_path(cls) -> Optional[str]:
        """Returns full executable path of running Premiere Pro process or None."""
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if PREMIERE_EXE_NAME.lower() in proc.info["name"].lower():
                    return proc.info["exe"]
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                pass
        return None

    @classmethod
    def find_premiere_install_path(cls) -> Optional[str]:
        """
        Searches Windows Registry and common program files directories for Adobe Premiere Pro.exe.
        """
        # 1. Check registry App Paths
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Premiere Pro.exe",
                0,
                winreg.KEY_READ
            )
            val, _ = winreg.QueryValueEx(key, "")
            winreg.CloseKey(key)
            if val and os.path.isfile(val):
                return os.path.abspath(val)
        except Exception:
            pass

        # 2. Check standard Program Files directory paths
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        adobe_dir = os.path.join(program_files, "Adobe")
        if os.path.isdir(adobe_dir):
            for item in os.listdir(adobe_dir):
                if "premiere" in item.lower():
                    exe_candidate = os.path.join(adobe_dir, item, PREMIERE_EXE_NAME)
                    if os.path.isfile(exe_candidate):
                        return os.path.abspath(exe_candidate)

        # 3. Common hardcoded candidate paths (2021 through 2026)
        for year in ["2026", "2025", "2024", "2023", "2022", "2021"]:
            candidate = os.path.join(program_files, "Adobe", f"Adobe Premiere Pro {year}", PREMIERE_EXE_NAME)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)

        return None

    @classmethod
    def ensure_premiere_running_and_focused(cls, project_path: Optional[str] = None) -> bool:
        """
        Ensures Premiere Pro is running, launches it with optional project path if not running,
        and brings the main Premiere Pro window to the foreground.
        Returns True if Premiere Pro is running and active.
        """
        pid = cls.get_running_pid()

        if not pid:
            print("[PREMIERE_LAUNCHER]\nstatus=LAUNCHING_PREMIERE", flush=True)
            exe_path = cls.find_premiere_install_path()

            if not exe_path:
                print("[PREMIERE_LAUNCHER]\nstatus=FAILED\nreason=exe_not_found", flush=True)
                raise RuntimeError(
                    "Adobe Premiere Pro installation executable not found. "
                    "Please install Adobe Premiere Pro to proceed."
                )

            print(f"[PREMIERE_LAUNCHER]\nexecuting_path={exe_path}", flush=True)
            cmd = [exe_path]
            if project_path and os.path.isfile(project_path):
                cmd.append(project_path)
            proc = subprocess.Popen(cmd, shell=False)
            
            deadline = time.time() + MAX_LAUNCH_WAIT_SECS
            while time.time() < deadline:
                pid = cls.get_running_pid()
                if pid:
                    print(f"[PREMIERE_LAUNCHER]\nstatus=STARTED\npid={pid}", flush=True)
                    time.sleep(3.0)  # Give time for splash screen & window init
                    break
                time.sleep(2.0)
            else:
                raise RuntimeError("Premiere Pro did not launch within timeout.")

        # Bring window to foreground & unminimize
        cls.bring_to_foreground()
        return True

    @classmethod
    def bring_to_foreground(cls) -> bool:
        """
        Brings Adobe Premiere Pro window to the foreground using PowerShell AppActivate / ctypes.
        """
        print("[PREMIERE_WINDOW]\nstatus=BRINGING_TO_FOREGROUND", flush=True)

        # 1. Primary: PowerShell wscript.shell AppActivate
        try:
            ps_script = (
                "$wshell = New-Object -ComObject wscript.shell; "
                "$success = $wshell.AppActivate('Adobe Premiere Pro'); "
                "if ($success) { exit 0 } else { exit 1 }"
            )
            res = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                print("[PREMIERE_WINDOW]\nstatus=FOREGROUND_PASS", flush=True)
                return True
        except Exception as e:
            print(f"[PREMIERE_WINDOW_WARNING] AppActivate failed: {e}", flush=True)

        # 2. Fallback: ctypes win32 API
        try:
            import ctypes
            user32 = ctypes.windll.user32
            
            def enum_handler(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "Premiere Pro" in title or "Adobe Premiere" in title:
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
                        user32.SetForegroundWindow(hwnd)
                        return False
                return True

            CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(CMPFUNC(enum_handler), 0)
            print("[PREMIERE_WINDOW]\nstatus=FOREGROUND_WIN32_DONE", flush=True)
            return True
        except Exception as exc:
            print(f"[PREMIERE_WINDOW_WARNING] Win32 focus failed: {exc}", flush=True)

        return False

    @classmethod
    def is_modal_dialog_present(cls) -> bool:
        """
        State-aware check: returns True only if an active modal dialog window
        (e.g., class '#32770' or window titled 'Import XML', 'Save Project', 'New Project', 'Confirm Save')
        is currently open and visible for Premiere Pro.
        """
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            user32 = ctypes.windll.user32
            found_modal = [False]

            def enum_handler(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value

                        class_buff = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(hwnd, class_buff, 256)
                        class_name = class_buff.value

                        if class_name == "#32770" or title in ["Import XML", "New Project", "Save Project", "Confirm Save"]:
                            found_modal[0] = True
                            return False
                return True

            CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(CMPFUNC(enum_handler), 0)
            return found_modal[0]
        except Exception:
            return False
