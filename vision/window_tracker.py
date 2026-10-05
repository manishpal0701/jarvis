"""
vision/window_tracker.py
Active foreground window tracker for JARVIS Phase 4 Vision.
Extracts window title, process ID, process name, window coordinates, and application classification on Windows.
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("WindowTracker")

try:
    import win32gui
    import win32process
    import psutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class WindowTracker:
    def __init__(self):
        pass

    def get_active_window_info(self) -> Dict[str, Any]:
        """
        Returns structured dictionary containing details of the foreground active window:
        - window_title: str
        - process_name: str
        - pid: int
        - rect: (left, top, right, bottom)
        - app_category: str (IDE, Browser, Terminal, Media, Document, System)
        """
        if not HAS_WIN32:
            return self._get_fallback_info()

        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return self._get_fallback_info()

            title = win32gui.GetWindowText(hwnd) or "Desktop / Unknown"
            rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = "Unknown"
            if pid:
                try:
                    proc = psutil.Process(pid)
                    process_name = proc.name()
                except Exception:
                    process_name = "Unknown"

            app_category = self._classify_app(process_name, title)

            return {
                "window_title": title,
                "process_name": process_name,
                "pid": pid,
                "rect": rect,  # (left, top, right, bottom)
                "width": max(0, rect[2] - rect[0]),
                "height": max(0, rect[3] - rect[1]),
                "app_category": app_category
            }
        except Exception as e:
            logger.error(f"[WindowTracker] Error tracking active window: {e}")
            return self._get_fallback_info()

    def _classify_app(self, process_name: str, title: str) -> str:
        proc_lower = process_name.lower()
        title_lower = title.lower()

        if any(x in proc_lower for x in ["code.exe", "devenv.exe", "idea64.exe", "pycharm", "sublime", "atom"]):
            return "IDE"
        if any(x in proc_lower for x in ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"]):
            return "Browser"
        if any(x in proc_lower for x in ["cmd.exe", "powershell.exe", "wt.exe", "terminal.exe", "bash.exe"]):
            return "Terminal"
        if any(x in proc_lower for x in ["winword.exe", "excel.exe", "powerpnt.exe", "acrord32.exe", "notepad.exe"]):
            return "Document"
        if any(x in proc_lower for x in ["vlc.exe", "spotify.exe", "wmplayer.exe"]):
            return "Media"

        # Check title strings as fallback
        if "visual studio code" in title_lower or ".py" in title_lower or ".dart" in title_lower:
            return "IDE"
        if "chrome" in title_lower or "edge" in title_lower or "http" in title_lower:
            return "Browser"

        return "System / Other"

    def _get_fallback_info(self) -> Dict[str, Any]:
        return {
            "window_title": "Primary Screen / Desktop",
            "process_name": "explorer.exe",
            "pid": 0,
            "rect": (0, 0, 1920, 1080),
            "width": 1920,
            "height": 1080,
            "app_category": "System / Other"
        }
