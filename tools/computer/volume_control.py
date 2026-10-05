"""
tools/computer/volume_control.py
Native System Volume Controller for Windows on Jarvis AI Assistant.
Uses ctypes keybd_event VK_VOLUME_UP/VK_VOLUME_DOWN/VK_VOLUME_MUTE for zero-dependency native audio control.
"""

import sys
import time
import ctypes
from typing import Tuple

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

class VolumeController:
    """
    Handles native Windows audio volume control operations.
    """

    @staticmethod
    def _send_vol_key(vk_code: int, times: int = 1):
        if sys.platform != "win32":
            return
        user32 = ctypes.windll.user32
        for _ in range(times):
            user32.keybd_event(vk_code, 0, 0, 0)
            user32.keybd_event(vk_code, 0, 2, 0)
            time.sleep(0.02)

    @classmethod
    def increase_volume(cls, percent: int = 10) -> Tuple[bool, str]:
        # Each volume keypress changes volume by 2%
        steps = max(1, percent // 2)
        cls._send_vol_key(VK_VOLUME_UP, steps)
        return True, f"Increased volume, Boss."

    @classmethod
    def decrease_volume(cls, percent: int = 10) -> Tuple[bool, str]:
        steps = max(1, percent // 2)
        cls._send_vol_key(VK_VOLUME_DOWN, steps)
        return True, f"Decreased volume, Boss."

    @classmethod
    def set_volume(cls, target_percent: int) -> Tuple[bool, str]:
        target = max(0, min(100, target_percent))
        # Zero out volume first with 50 down keypresses, then increase to target
        cls._send_vol_key(VK_VOLUME_DOWN, 50)
        time.sleep(0.05)
        steps = target // 2
        if steps > 0:
            cls._send_vol_key(VK_VOLUME_UP, steps)
        return True, f"Volume set to {target} percent, Boss."

    @classmethod
    def mute(cls) -> Tuple[bool, str]:
        cls._send_vol_key(VK_VOLUME_MUTE, 1)
        return True, "Muted audio, Boss."

    @classmethod
    def unmute(cls) -> Tuple[bool, str]:
        cls._send_vol_key(VK_VOLUME_MUTE, 1)
        return True, "Unmuted audio, Boss."
