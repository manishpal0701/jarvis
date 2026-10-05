"""
tools/computer/keyboard_automation.py
Universal Keyboard and Text Input Controller for Jarvis AI Assistant.
Provides window-focus aware text typing, hotkeys, and safe keyboard automation
routed through SafeKeyboardAutomation to preserve NumLock and CapsLock states.
"""

import sys
import time
import ctypes
import pyautogui
from typing import Optional, Tuple
from video_editing.software.safe_keyboard import SafeKeyboardAutomation

class KeyboardController:
    """
    Handles typing, pasting, key pressing, and window focus management.
    """

    @staticmethod
    def get_active_window_title() -> str:
        """Returns the title of the currently focused foreground window."""
        if sys.platform != "win32":
            return ""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                return buf.value
        except Exception:
            pass
        return ""

    @staticmethod
    def focus_window_by_title(target_name: str, timeout: float = 3.0) -> bool:
        """
        Searches open top-level windows for target_name and brings the matching window to focus.
        Returns True if focus succeeded.
        """
        if sys.platform != "win32":
            return False

        target_lower = target_name.lower().strip()
        user32 = ctypes.windll.user32

        matched_hwnd = None

        def enum_windows_proc(hwnd, lParam):
            nonlocal matched_hwnd
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.lower()
                    if target_lower in title:
                        matched_hwnd = hwnd
                        return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        try:
            user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
        except Exception:
            pass

        if matched_hwnd:
            try:
                # Bring window to foreground
                user32.ShowWindow(matched_hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(matched_hwnd)
                time.sleep(0.3)
                return True
            except Exception:
                pass

        return False

    @classmethod
    def type_text(cls, text: str, target_app: Optional[str] = None, submit: bool = False) -> Tuple[bool, str]:
        """
        Types or pastes the specified text into the active window or target_app field.
        Uses clipboard paste (Ctrl+V) wrapped in SafeKeyboardAutomation for 100% reliable Unicode handling.
        Does NOT press Enter/Submit unless submit=True is explicitly set.
        """
        if not text or not text.strip():
            return False, "No text specified to type, Boss."

        clean_text = text.strip()

        # If a target application was requested, bring it to focus
        if target_app:
            cls.focus_window_by_title(target_app)
            time.sleep(0.2)

        def _perform_paste():
            import pyperclip
            prev_clip = ""
            try:
                prev_clip = pyperclip.paste()
            except Exception:
                pass

            try:
                pyperclip.copy(clean_text)
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.1)
            finally:
                try:
                    if prev_clip:
                        pyperclip.copy(prev_clip)
                except Exception:
                    pass

            if submit:
                time.sleep(0.2)
                pyautogui.press('enter')

        # Route through SafeKeyboardAutomation to preserve NumLock state
        SafeKeyboardAutomation.send_key_safely(
            f"type_text submit={submit} len={len(clean_text)}",
            _perform_paste
        )

        active_title = cls.get_active_window_title()
        app_desc = f"in {active_title}" if active_title else ""
        return True, f"Done, typed text {app_desc}, Boss."
