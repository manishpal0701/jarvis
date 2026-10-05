"""
tools/computer/brightness_control.py
Native Windows Screen Brightness Controller for Jarvis AI Assistant.
Queries and sets monitor display brightness using WmiMonitorBrightnessMethods via PowerShell/WMI.

IMPORTANT: All user-facing strings must NEVER expose subprocess commands, PowerShell strings,
Python tracebacks, or internal implementation details. Only clean, friendly messages are returned.
"""

import sys
import subprocess
from typing import Tuple, Optional

# Cached WMI availability flag.
# None = not probed yet; True = available; False = unavailable on this hardware.
_wmi_brightness_available: Optional[bool] = None


def _probe_wmi_brightness() -> bool:
    """
    Probes whether WmiMonitorBrightnessMethods is available on this hardware.
    Only runs once; result cached in module-level _wmi_brightness_available.
    Returns True if the WMI interface is available, False otherwise.
    """
    global _wmi_brightness_available
    if _wmi_brightness_available is not None:
        return _wmi_brightness_available

    if sys.platform != "win32":
        _wmi_brightness_available = False
        return False

    try:
        # Probe the SETTER interface (WmiMonitorBrightnessMethods), not just the getter.
        # On many laptops, the getter (WmiMonitorBrightness) exists but the setter times out.
        # Probing the setter prevents a false-positive that leads to a guaranteed timeout.
        cmd = ['powershell', '-Command',
               '(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue) -ne $null']
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0)
        output = res.stdout.strip().lower()
        _wmi_brightness_available = (output == "true")
        print(f"[BRIGHTNESS_PROBE] wmi_setter_available={_wmi_brightness_available}", flush=True)
    except Exception as probe_err:
        # Log internally only — never surface to user
        print(f"[BRIGHTNESS_PROBE_INTERNAL] probe failed: {type(probe_err).__name__}", flush=True)
        _wmi_brightness_available = False

    return _wmi_brightness_available


class BrightnessController:
    """
    Handles monitor brightness adjustments on Windows hardware.
    All public methods return (success: bool, user_facing_message: str).
    Internal errors are logged to stdout with [BRIGHTNESS_ERROR_INTERNAL] prefix only.
    """

    @staticmethod
    def get_brightness() -> Optional[int]:
        """Queries current screen brightness percentage (0-100). Returns None if unavailable."""
        if sys.platform != "win32":
            return None
        if not _probe_wmi_brightness():
            return None
        try:
            cmd = ['powershell', '-Command',
                   '(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=4.0)
            val_str = res.stdout.strip()
            if val_str.isdigit():
                return int(val_str)
        except Exception as e:
            # Internal log only
            print(f"[BRIGHTNESS_ERROR_INTERNAL] get_brightness: {type(e).__name__}", flush=True)
        return None

    @classmethod
    def set_brightness(cls, percent: int) -> Tuple[bool, str]:
        """
        Sets display brightness to specified percentage (0-100).
        Returns (success, user_friendly_message). Never exposes raw commands or exceptions.
        """
        if sys.platform != "win32":
            return False, "Sorry Boss, brightness control Windows pe hi available hai."

        if not _probe_wmi_brightness():
            # WMI interface not available on this hardware (likely external monitor)
            print("[BRIGHTNESS_ERROR_INTERNAL] WmiMonitorBrightnessMethods not available on this hardware.", flush=True)
            return False, "Sorry Boss, is display pe brightness control support nahi karta."

        target = max(0, min(100, percent))
        try:
            ps_cmd = (
                f"Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods "
                f"| Invoke-CimMethod -MethodName WmiSetBrightness "
                f"-Arguments @{{Timeout = 1; Brightness = {target}}}"
            )
            res = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True, text=True, timeout=3.0
            )
            if res.returncode == 0 and "error" not in res.stderr.lower():
                return True, f"Brightness {target} percent kar diya, Boss."

            # returncode != 0 — command failed but did not raise an exception
            print(f"[BRIGHTNESS_ERROR_INTERNAL] set_brightness returncode={res.returncode} stderr={res.stderr[:100]}", flush=True)
            return False, "Sorry Boss, brightness change nahi ho paya."

        except subprocess.TimeoutExpired:
            # Timeout — mark WMI as unavailable so future calls skip immediately
            global _wmi_brightness_available
            _wmi_brightness_available = False
            print("[BRIGHTNESS_ERROR_INTERNAL] WmiSetBrightness timed out. Marking WMI brightness as unavailable.", flush=True)
            return False, "Sorry Boss, brightness change nahi ho paya."

        except Exception as e:
            # Any other error — log type only, never surface details
            print(f"[BRIGHTNESS_ERROR_INTERNAL] set_brightness: {type(e).__name__}", flush=True)
            return False, "Sorry Boss, brightness change nahi ho paya."

    @classmethod
    def increase_brightness(cls, step: int = 15) -> Tuple[bool, str]:
        curr = cls.get_brightness()
        if curr is not None:
            return cls.set_brightness(curr + step)
        return cls.set_brightness(80)

    @classmethod
    def decrease_brightness(cls, step: int = 15) -> Tuple[bool, str]:
        curr = cls.get_brightness()
        if curr is not None:
            return cls.set_brightness(curr - step)
        return cls.set_brightness(40)
