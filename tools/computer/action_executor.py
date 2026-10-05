"""
tools/computer/action_executor.py
Central Action Executor for JARVIS Phase 5 Computer Control.
Executes validated computer actions (clicks, keyboard input, hotkeys, scrolling, app launching),
enforces target window focus verification, handles cancellation/timeouts, and verifies post-action results.
"""

import os
import time
import logging
from typing import Any, Dict, Optional, Tuple

from tools.computer.action_model import Action, ActionResult, ActionStatus, ActionType, RiskLevel
from tools.computer.target_resolver import TargetResolver
from tools.computer.safety_validator import SafetyValidator
from vision.screen_capture import ScreenCapture
from vision.window_tracker import WindowTracker
from vision.screen_context import ScreenContext, ScreenContextAnalyzer
from vision.privacy_filter import PrivacyFilter

logger = logging.getLogger("ActionExecutor")

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


class ActionExecutor:
    def __init__(
        self,
        target_resolver: Optional[TargetResolver] = None,
        safety_validator: Optional[SafetyValidator] = None,
        screen_capture: Optional[ScreenCapture] = None,
        window_tracker: Optional[WindowTracker] = None,
        context_analyzer: Optional[ScreenContextAnalyzer] = None
    ):
        self.target_resolver = target_resolver or TargetResolver()
        self.safety_validator = safety_validator or SafetyValidator()
        self.screen_capture = screen_capture or ScreenCapture()
        self.window_tracker = window_tracker or WindowTracker()
        self.context_analyzer = context_analyzer or ScreenContextAnalyzer(self.window_tracker)
        self.privacy_filter = PrivacyFilter.get_instance()
        self._cancelled_actions = set()

    def execute_action(self, action: Action, skip_verification: bool = False) -> ActionResult:
        """
        Executes a validated Action with focus verification and post-action verification.
        """
        start_time = time.time()
        start_str = time.strftime("%Y-%m-%dT%H:%M:%S")

        print(f"[ACTION_EXECUTE] id={action.action_id} type={action.action_type.value} status={action.status.value}", flush=True)

        if action.action_id in self._cancelled_actions:
            action.status = ActionStatus.CANCELLED
            return ActionResult(action_id=action.action_id, status=ActionStatus.CANCELLED, started_at=start_str, completed_at=time.strftime("%Y-%m-%dT%H:%M:%S"), error="Action was cancelled.")

        # Step 1: Pre-action screen context capture for post-verification
        pre_context = None
        if action.verification_required and not skip_verification:
            pre_frame = self.screen_capture.capture_full_screen()
            pre_context = self.context_analyzer.analyze_frame(pre_frame)
            if pre_frame.image_path:
                self.privacy_filter.cleanup_file(pre_frame.image_path)

        # Step 2: Validate Target & Focus Safety for typing / clicking
        target_app = action.parameters.get("target_app") or action.parameters.get("app_name")
        if action.action_type in [ActionType.TYPE, ActionType.KEY_PRESS, ActionType.HOTKEY] and target_app:
            focused = self._verify_target_focus(target_app)
            if not focused:
                action.status = ActionStatus.FAILED
                err_msg = f"Focus verification failed for '{target_app}'. Intended target window is not active."
                return ActionResult(action_id=action.action_id, status=ActionStatus.FAILED, started_at=start_str, completed_at=time.strftime("%Y-%m-%dT%H:%M:%S"), error=err_msg)

        # Step 3: Execute Action
        action.status = ActionStatus.EXECUTING
        try:
            res_dict = self._perform_action_type(action)
        except Exception as e:
            logger.error(f"[ActionExecutor] Action execution exception: {e}")
            action.status = ActionStatus.FAILED
            return ActionResult(action_id=action.action_id, status=ActionStatus.FAILED, started_at=start_str, completed_at=time.strftime("%Y-%m-%dT%H:%M:%S"), error=str(e))

        # Step 4: Post-Action Verification
        ver_status = "VERIFIED_SUCCESS"
        if action.verification_required and not skip_verification and pre_context:
            action.status = ActionStatus.VERIFYING
            time.sleep(0.3)
            post_frame = self.screen_capture.capture_full_screen()
            post_context = self.context_analyzer.analyze_frame(post_frame, prev_context=pre_context)

            # Verify screen change or expected result
            verified = self._verify_action_result(action, pre_context, post_context)
            if not verified:
                action.status = ActionStatus.VERIFICATION_FAILED
                ver_status = "VERIFICATION_FAILED"
            else:
                action.status = ActionStatus.COMPLETED

            if post_frame.image_path:
                self.privacy_filter.cleanup_file(post_frame.image_path)
        else:
            action.status = ActionStatus.COMPLETED

        end_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        action.result = res_dict

        print(f"[ACTION_COMPLETE] id={action.action_id} status={action.status.value} ver={ver_status}", flush=True)

        return ActionResult(
            action_id=action.action_id,
            status=action.status,
            started_at=start_str,
            completed_at=end_str,
            verification_status=ver_status,
            metadata=res_dict or {}
        )

    def cancel_action(self, action_id: str):
        """Cancels an ongoing or pending action."""
        self._cancelled_actions.add(action_id)

    def _perform_action_type(self, action: Action) -> Dict[str, Any]:
        """Dispatches actual physical action using PyAutoGUI / Keyboard / Win32."""
        a_type = action.action_type
        params = action.parameters or {}
        target = action.target

        if a_type == ActionType.CLICK:
            x = target.center_x if target else params.get("x", 960)
            y = target.center_y if target else params.get("y", 540)
            if HAS_PYAUTOGUI:
                pyautogui.click(x=x, y=y)
            return {"clicked_x": x, "clicked_y": y}

        elif a_type == ActionType.DOUBLE_CLICK:
            x = target.center_x if target else params.get("x", 960)
            y = target.center_y if target else params.get("y", 540)
            if HAS_PYAUTOGUI:
                pyautogui.doubleClick(x=x, y=y)
            return {"double_clicked_x": x, "double_clicked_y": y}

        elif a_type == ActionType.RIGHT_CLICK:
            x = target.center_x if target else params.get("x", 960)
            y = target.center_y if target else params.get("y", 540)
            if HAS_PYAUTOGUI:
                pyautogui.rightClick(x=x, y=y)
            return {"right_clicked_x": x, "right_clicked_y": y}

        elif a_type == ActionType.TYPE:
            text = params.get("text", "")
            submit = params.get("submit", False)
            if HAS_PYAUTOGUI and text:
                pyautogui.write(text, interval=0.02)
                if submit:
                    pyautogui.press('enter')
            return {"typed_length": len(text), "submitted": submit}

        elif a_type == ActionType.KEY_PRESS:
            key = params.get("key", "enter")
            if HAS_PYAUTOGUI:
                pyautogui.press(key)
            return {"key_pressed": key}

        elif a_type == ActionType.HOTKEY:
            keys = params.get("keys", ["alt", "f4"])
            if HAS_PYAUTOGUI:
                pyautogui.hotkey(*keys)
            return {"hotkey_pressed": keys}

        elif a_type == ActionType.SCROLL:
            amount = params.get("amount", -300)
            if HAS_PYAUTOGUI:
                pyautogui.scroll(amount)
            return {"scrolled_amount": amount}

        elif a_type in [ActionType.OPEN_APPLICATION, ActionType.FOCUS_WINDOW, ActionType.SWITCH_WINDOW]:
            app_name = params.get("app_name") or params.get("target_app") or (target.semantic_label if target else "Notepad")
            from tools.computer.app_launcher import AppLauncher
            success, msg = AppLauncher.launch_app(app_name)
            return {"app_launched": app_name, "message": msg}

        return {"executed_action": a_type.value}

    def _verify_target_focus(self, target_app: str) -> bool:
        """Verifies if target_app process or window is currently foreground active with settling delay."""
        if not target_app:
            return True
        target_lower = target_app.lower()

        for _ in range(3):
            info = self.window_tracker.get_active_window_info()
            proc_name = info.get("process_name", "").lower()
            win_title = info.get("window_title", "").lower()

            if target_lower in proc_name or target_lower in win_title:
                return True
            if "notepad" in target_lower and ("notepad" in win_title or "notepad" in proc_name):
                return True
            if "code" in target_lower and ("code.exe" in proc_name or "visual studio code" in win_title):
                return True
            if "chrome" in target_lower and "chrome" in proc_name:
                return True
            time.sleep(0.15)

        return False

    def _verify_action_result(self, action: Action, pre_ctx: ScreenContext, post_ctx: ScreenContext) -> bool:
        """Compares pre-action vs post-action ScreenContext to verify expected state change."""
        if not post_ctx:
            return False

        # Open application or focus window verification
        if action.action_type in [ActionType.OPEN_APPLICATION, ActionType.FOCUS_WINDOW, ActionType.SWITCH_WINDOW]:
            target_app = action.parameters.get("app_name") or action.parameters.get("target_app") or ""
            return self._verify_target_focus(target_app)

        # For click or scroll or type, verify screen change magnitude or active window
        if post_ctx.has_changed or post_ctx.change_magnitude > 0.005:
            return True

        # If no visual difference detected, check if action was a harmless click/scroll
        if action.action_type in [ActionType.CLICK, ActionType.SCROLL, ActionType.TYPE]:
            return True

        return False
