"""
video_editing/software/safe_keyboard.py
Safe keyboard automation helper that preserves the user's NumLock state
and logs input automation actions.
"""

import sys
from typing import Callable, Any

VK_NUMLOCK = 0x90
KEYEVENTF_KEYUP = 0x0002


class SafeKeyboardAutomation:
    """
    Encapsulates keyboard automation calls to ensure:
    1. The user's NumLock state is captured before key injection.
    2. Any inadvertent NumLock state changes caused by pyautogui / SendKeys are detected and restored.
    3. All key actions emit structured logging.
    """

    @staticmethod
    def get_numlock_state() -> bool:
        """
        Returns True if NumLock is currently ON, False if OFF.
        """
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            return bool(ctypes.windll.user32.GetKeyState(VK_NUMLOCK) & 1)
        except Exception:
            return False

    @staticmethod
    def restore_numlock_state(target_state: bool):
        """
        Toggles NumLock if current state does not match target_state.
        """
        if sys.platform != "win32":
            return
        current_state = SafeKeyboardAutomation.get_numlock_state()
        if current_state != target_state:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                # Press VK_NUMLOCK (0x90) and release
                user32.keybd_event(VK_NUMLOCK, 0x45, 0, 0)
                user32.keybd_event(VK_NUMLOCK, 0x45, KEYEVENTF_KEYUP, 0)
            except Exception:
                pass

    @classmethod
    def send_key_safely(cls, action_description: str, send_func: Callable[[], Any]) -> Any:
        """
        Executes send_func while capturing and preserving the exact NumLock state.
        Emits structured logs:
        [KEYBOARD_AUTOMATION] action=<action_description> numlock_before=<ON/OFF>
        [KEYBOARD_AUTOMATION] action=<action_description> numlock_after=<ON/OFF>
        """
        numlock_before = cls.get_numlock_state()
        before_str = "ON" if numlock_before else "OFF"
        print(f"[KEYBOARD_AUTOMATION] action={action_description} numlock_before={before_str}", flush=True)

        res = None
        try:
            res = send_func()
        finally:
            numlock_after = cls.get_numlock_state()
            if numlock_after != numlock_before:
                cls.restore_numlock_state(numlock_before)
                numlock_after = cls.get_numlock_state()

            after_str = "ON" if numlock_after else "OFF"
            print(f"[KEYBOARD_AUTOMATION] action={action_description} numlock_after={after_str}", flush=True)

        return res
