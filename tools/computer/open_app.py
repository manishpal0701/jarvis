"""
tools/computer/open_app.py
Dynamic Application Launcher Bridge for Jarvis AI Assistant.
Forwards all open/launch commands to AppLauncher for dynamic resolution.
"""

from tools.computer.app_launcher import AppLauncher

def open_application(command: str) -> tuple[bool, str]:
    """
    Dynamically launches an application based on the user's natural command.
    """
    return AppLauncher.launch_app(command)

# Backwards compatibility dictionary wrapper
class DynamicAppDict(dict):
    def __getitem__(self, key):
        success, msg = AppLauncher.launch_app(key)
        return msg

    def __contains__(self, key):
        target, _ = AppLauncher.resolve_app(key)
        return target is not None

open_app = DynamicAppDict()
