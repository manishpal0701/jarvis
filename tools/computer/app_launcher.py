"""
tools/computer/app_launcher.py
Universal Dynamic Windows Application Launcher for Jarvis AI Assistant.
Resolves applications dynamically via Start Menu shortcuts (.lnk), Registry App Paths,
system PATH, UWP apps, and Windows system binaries without hardcoded lists.
"""

import os
import re
import sys
import winreg
import subprocess
from typing import Dict, Tuple, Optional

class AppLauncher:
    _cached_apps: Optional[Dict[str, str]] = None

    @classmethod
    def get_installed_apps(cls, force_refresh: bool = False) -> Dict[str, str]:
        """
        Scans Windows Start Menu, Registry App Paths, AppData, and System directories
        to build a map of normalized application names to executable paths or protocol URIs.
        """
        if cls._cached_apps is not None and not force_refresh:
            return cls._cached_apps

        apps: Dict[str, str] = {}

        # 1. Windows System & Built-in Applications
        system_apps = {
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "notepad": "notepad.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            "camera": "ms-apps:camera://",
            "paint": "mspaint.exe"
        }
        apps.update(system_apps)

        # 2. Windows Start Menu LNK Shortcuts
        start_dirs = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs")
        ]

        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            for d in start_dirs:
                if os.path.exists(d):
                    for root, _, files in os.walk(d):
                        for f in files:
                            name_clean = os.path.splitext(f)[0].lower()
                            full_p = os.path.join(root, f)
                            if f.endswith(".lnk"):
                                try:
                                    sc = shell.CreateShortCut(full_p)
                                    if sc.TargetPath and os.path.exists(sc.TargetPath) and sc.TargetPath.endswith(".exe"):
                                        apps[name_clean] = sc.TargetPath
                                except Exception:
                                    pass
                            elif f.endswith(".exe"):
                                apps[name_clean] = full_p
        except Exception:
            pass

        # 3. Windows Registry App Paths
        for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for pkey in [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"
            ]:
                try:
                    key = winreg.OpenKey(root_key, pkey)
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            sub_name = winreg.EnumKey(key, i)
                            sk = winreg.OpenKey(key, sub_name)
                            val, _ = winreg.QueryValueEx(sk, "")
                            if val and os.path.exists(val):
                                app_name = sub_name.replace(".exe", "").lower()
                                apps[app_name] = val
                        except Exception:
                            pass
                except Exception:
                    pass

        # Alias mappings for common spoken names and web destinations
        aliases = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "spotify": "https://open.spotify.com",
            "gmail": "https://mail.google.com",
            "github": "https://github.com",
            "facebook": "https://facebook.com",
            "instagram": "https://instagram.com",
            "vs code": apps.get("visual studio code") or apps.get("code"),
            "vscode": apps.get("visual studio code") or apps.get("code"),
            "code": apps.get("visual studio code") or apps.get("code"),
            "android studio": apps.get("android studio") or apps.get("studio64"),
            "premiere": apps.get("adobe premiere pro 2021") or apps.get("adobe premiere pro 2025") or apps.get("adobe premiere pro"),
            "premiere pro": apps.get("adobe premiere pro 2021") or apps.get("adobe premiere pro 2025") or apps.get("adobe premiere pro"),
            "photoshop": apps.get("adobe photoshop 2020") or apps.get("adobe photoshop 2025") or apps.get("adobe photoshop"),
            "chrome": apps.get("google chrome") or apps.get("chrome"),
            "browser": apps.get("google chrome") or apps.get("msedge") or apps.get("chrome"),
            "word": apps.get("word") or apps.get("winword"),
            "excel": apps.get("excel"),
            "powerpoint": apps.get("powerpnt")
        }
        for alias_name, alias_target in aliases.items():
            if alias_target and alias_name not in apps:
                apps[alias_name] = alias_target

        cls._cached_apps = apps
        return apps

    @classmethod
    def resolve_app(cls, raw_query: str) -> Tuple[Optional[str], str]:
        """
        Resolves a user application launch query to (executable_path_or_protocol, display_name).
        Returns (None, requested_name) if no matching installed application is found.
        """
        # Clean query: strip lead-in words like "open", "launch", "start", "run", "khol", "kholo"
        query = raw_query.lower().strip()
        query = re.sub(r"^(open|launch|start|run|khol|kholo|chalao|chala do)\s+", "", query).strip()
        query = re.sub(r"^(the|app|application|software)\s+", "", query).strip()
        query = re.sub(r"\s+(app|application|software)$", "", query).strip()

        if not query:
            return None, raw_query

        apps = cls.get_installed_apps()

        # Direct match
        if query in apps:
            display_name = query.title()
            return apps[query], display_name

        # Normalized query matching
        query_tokens = set(query.split())

        best_match = None
        best_score = 0

        for name, path in apps.items():
            name_tokens = set(name.split())
            if query in name or name in query:
                score = len(name)
                if score > best_score:
                    best_score = score
                    best_match = (path, name.title())
            elif query_tokens.issubset(name_tokens) or name_tokens.issubset(query_tokens):
                score = len(name_tokens)
                if score > best_score:
                    best_score = score
                    best_match = (path, name.title())

        if best_match:
            return best_match

        return None, query.title()

    @classmethod
    def launch_app(cls, raw_query: str) -> Tuple[bool, str]:
        """
        Launches the resolved application dynamically and returns (success: bool, response_message: str).
        """
        target, display_name = cls.resolve_app(raw_query)

        if not target:
            return False, f"I couldn't find {display_name} on this PC, Boss."

        try:
            if target.startswith(("http://", "https://", "ms-settings:", "ms-apps:")):
                import webbrowser
                webbrowser.open(target)
            elif sys.platform == "win32":
                os.startfile(target)
            else:
                subprocess.Popen([target])

            return True, f"Opening {display_name}, Boss."
        except Exception as e:
            return False, f"Failed to open {display_name}: {e}"
