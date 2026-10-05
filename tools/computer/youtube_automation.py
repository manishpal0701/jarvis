"""
tools/computer/youtube_automation.py
Natural-language YouTube search and song playback automation for Jarvis AI Assistant.
Formats search query, dynamically resolves Google Chrome, and opens YouTube in Chrome.
"""

import os
import re
import sys
import winreg
import subprocess
import urllib.parse
from typing import Tuple, Optional
from tools.computer.app_launcher import AppLauncher

class YouTubeAutomation:
    """
    Handles natural language YouTube playback commands exclusively using Google Chrome.
    """

    @classmethod
    def get_chrome_path(cls) -> Optional[str]:
        """
        Dynamically resolves the executable path of Google Chrome on the user's system.
        Scans AppLauncher, AppData, Program Files, and Windows Registry App Paths.
        """
        # 1. Resolve via AppLauncher dynamic discovery
        target, _ = AppLauncher.resolve_app("chrome")
        if target and os.path.exists(target) and target.endswith(".exe"):
            return target

        # 2. Common Windows installation paths
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")
        ]
        for p in candidates:
            if os.path.exists(p):
                return p

        # 3. Windows Registry App Paths
        for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for pkey in [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
            ]:
                try:
                    key = winreg.OpenKey(root_key, pkey)
                    val, _ = winreg.QueryValueEx(key, "")
                    if val and os.path.exists(val):
                        return val
                except Exception:
                    pass

        return None

    @classmethod
    def play_on_youtube(cls, raw_command: str) -> Tuple[bool, str]:
        """
        Parses user playback query, opens YouTube search/playback in Chrome, and returns voice response.
        If Chrome cannot be found, returns a clear failure message without falling back to Edge.
        """
        command = raw_command.strip()

        # Extract clean search query from command
        # e.g., "play believer", "youtube pe kesariya lagao", "search believer on youtube"
        clean_query = command
        clean_query = re.sub(r"(?i)^(jarvis,?\s*)?(play|search|open|run|stream|lagao)\s+", "", clean_query)
        clean_query = re.sub(r"(?i)^(on\s+youtube|youtube\s+pe|youtube\s+par|youtube\s+for|in\s+youtube)\s+", "", clean_query)
        clean_query = re.sub(r"(?i)\s+(on\s+youtube|youtube\s+pe|youtube\s+par|lagao|bajao|chalao)$", "", clean_query)
        clean_query = clean_query.strip()

        if not clean_query:
            clean_query = "trending music"

        chrome_path = cls.get_chrome_path()
        if not chrome_path:
            return False, "Google Chrome is not installed on this PC, Boss."

        encoded_query = urllib.parse.quote(clean_query)
        target_url = f"https://www.youtube.com/results?search_query={encoded_query}"

        try:
            if sys.platform == "win32":
                subprocess.Popen([chrome_path, target_url])
            else:
                import webbrowser
                webbrowser.get(f'"{chrome_path}" %s').open(target_url)

            display_title = clean_query.title()
            return True, f"Playing {display_title}, Boss."
        except Exception as e:
            return False, f"Could not open Chrome for YouTube: {e}"
