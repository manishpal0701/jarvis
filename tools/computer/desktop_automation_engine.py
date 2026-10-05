"""
tools/computer/desktop_automation_engine.py
General Desktop Automation Engine for Jarvis AI Assistant.
Extracts desktop action intents and routes execution through application launcher,
keyboard controller, YouTube automation, volume controller, and brightness controller.
"""

import re
from typing import Tuple, Optional, Dict, Any
from tools.computer.app_launcher import AppLauncher
from tools.computer.keyboard_automation import KeyboardController
from tools.computer.youtube_automation import YouTubeAutomation
from tools.computer.volume_control import VolumeController
from tools.computer.brightness_control import BrightnessController
from tools.computer.sleep_control import SleepController

class DesktopAutomationEngine:
    """
    Unified Desktop Action Planner & Executor facade.
    """

    @classmethod
    def is_desktop_command(cls, query: str) -> bool:
        """
        Determines if a natural language query is a desktop automation command.
        """
        q = query.lower().strip()

        # 0. Laptop Sleep / Lock commands
        if SleepController.is_sleep_command(query) or any(kw in q for kw in ["lock laptop", "sleep mode", "lock screen", "sleep pc", "lock pc"]):
            return True

        # 1. Volume commands
        if any(kw in q for kw in ["volume", "mute", "unmute", "sound up", "sound down", "volume up", "volume down", "aawaz", "awaz"]):
            return True

        # 2. Brightness commands
        if any(kw in q for kw in ["brightness", "screen light", "roshni"]):
            return True

        # 3. YouTube commands
        if "youtube" in q or q.startswith("play ") or "search youtube" in q or "youtube search" in q:
            return True

        # 4. Keyboard / typing commands
        if any(kw in q for kw in ["type ", "write ", "write: ", "type: ", "enter text "]) or q.startswith("type") or q.startswith("write"):
            return True

        # 5. Open / Launch / Close app / Web keywords anywhere in query
        if any(kw in q for kw in ["kholo", "khol", "chalao", "chala do", "band karo", "band kar do", "close window", "close app"]):
            return True

        if any(q.startswith(kw) for kw in ["open ", "launch ", "start ", "run ", "close ", "exit "]):
            return True

        # 6. Screenshot commands
        if any(kw in q for kw in ["screenshot", "screen shot", "snip"]):
            return True

        # 7. Common desktop apps combined with launch/open/close verbs
        app_names = ["chrome", "notepad", "calculator", "calc", "browser", "vlc", "spotify", "word", "excel", "powerpoint", "vscode", "vs code", "cmd", "terminal", "command prompt", "task manager"]
        action_verbs = ["open", "launch", "start", "run", "khol", "kholo", "chalao", "chala do", "close", "band", "exit", "switch", "focus", "search"]

        if any(app in q for app in app_names) and any(verb in q for verb in action_verbs):
            return True

        return False

    @classmethod
    def execute_command(cls, query: str, request_id: str = None) -> Tuple[bool, str]:
        """
        Parses intent and executes desktop automation action plan.
        Returns (success: bool, spoken_response: str).
        request_id is forwarded through the chain for correct request lifecycle logging.
        """
        q = query.lower().strip()

        # Handle compound commands (e.g. "chrome kholo aur youtube search karo")
        if re.search(r"\s+(?:aur|and|then|phir)\s+", q):
            parts = [p.strip() for p in re.split(r"\s+(?:aur|and|then|phir)\s+", query, flags=re.IGNORECASE) if p.strip()]
            if len(parts) > 1:
                responses = []
                all_ok = True
                for part in parts:
                    ok, resp = cls._execute_single_command(part, request_id=request_id)
                    if ok:
                        responses.append(resp)
                    else:
                        all_ok = False
                        responses.append(resp)
                combined_resp = " ".join(responses) if responses else "Executed compound actions, Boss."
                return all_ok, combined_resp

        return cls._execute_single_command(query, request_id=request_id)

    @classmethod
    def _execute_single_command(cls, query: str, request_id: str = None) -> Tuple[bool, str]:
        """
        Executes a single desktop automation command string.
        request_id is carried through for correct request lifecycle correlation.
        """
        q = query.lower().strip()

        # ─── 0. Laptop Sleep Control ──────────────────────────────────────────
        if SleepController.is_sleep_command(query):
            return True, "Okay Boss, main laptop sleep pe daal deti hoon."

        # ─── 1. Volume Control ────────────────────────────────────────────────
        if any(kw in q for kw in ["volume", "mute", "unmute", "sound up", "sound down", "aawaz", "awaz"]):
            if "mute" in q and "unmute" not in q:
                return VolumeController.mute()
            if "unmute" in q:
                return VolumeController.unmute()

            match_pct = re.search(r"(\d+)\s*(percent|%)?", q)
            if match_pct and any(w in q for w in ["set", "to", "at", "level"]):
                val = int(match_pct.group(1))
                return VolumeController.set_volume(val)

            if any(kw in q for kw in ["increase", "raise", "up", "plus", "badha", "badhao", "badha do", "tez"]):
                pct = int(match_pct.group(1)) if match_pct else 10
                return VolumeController.increase_volume(pct)

            if any(kw in q for kw in ["decrease", "lower", "down", "minus", "reduce", "kam", "kam kar", "kam karo", "ghatao", "ghata do"]):
                pct = int(match_pct.group(1)) if match_pct else 10
                return VolumeController.decrease_volume(pct)

            if match_pct:
                return VolumeController.set_volume(int(match_pct.group(1)))

        # ─── 2. Brightness Control ────────────────────────────────────────────
        if any(kw in q for kw in ["brightness", "screen light", "roshni"]):
            match_pct = re.search(r"(\d+)\s*(percent|%)?", q)
            if match_pct and any(w in q for w in ["set", "to", "at", "level"]):
                val = int(match_pct.group(1))
                return BrightnessController.set_brightness(val)

            if any(kw in q for kw in ["increase", "raise", "up", "more", "badha", "badhao", "badha do"]):
                step = int(match_pct.group(1)) if match_pct else 15
                return BrightnessController.increase_brightness(step)

            if any(kw in q for kw in ["decrease", "lower", "down", "less", "kam", "kam kar", "kam karo", "ghatao", "ghata do"]):
                step = int(match_pct.group(1)) if match_pct else 15
                return BrightnessController.decrease_brightness(step)

            if match_pct:
                return BrightnessController.set_brightness(int(match_pct.group(1)))

        # ─── 3. YouTube Playback / Search ─────────────────────────────────────
        if "youtube" in q or q.startswith("play ") or "on youtube" in q or "youtube pe" in q or "youtube par" in q or q.startswith("search youtube"):
            return YouTubeAutomation.play_on_youtube(query)

        # ─── 4. Keyboard / Text Input ─────────────────────────────────────────
        if any(q.startswith(kw) for kw in ["type ", "write ", "write: ", "type: ", "enter text "]):
            # Check for "open X and write Y"
            match_open_type = re.search(r"(?i)^(open|khol|kholo)\s+([a-zA-Z0-9_\-\. ]+)\s+and\s+(write|type)\s+(.*)$", query)
            if match_open_type:
                target_app = match_open_type.group(2).strip()
                text_content = match_open_type.group(4).strip().strip("'\"")
                AppLauncher.launch_app(target_app)
                import time
                time.sleep(1.0)
                submit_flag = "and send" in query.lower() or "and enter" in query.lower()
                return KeyboardController.type_text(text_content, target_app=target_app, submit=submit_flag)

            # Standard type/write command
            clean_text = re.sub(r"(?i)^(type|write|write:|type:|enter text)\s+", "", query).strip().strip("'\"")
            submit_flag = "and send" in query.lower() or "and submit" in query.lower() or "and enter" in query.lower()
            return KeyboardController.type_text(clean_text, submit=submit_flag)

        # ─── 5. Universal Application Launcher ────────────────────────────────
        if any(kw in q for kw in ["open", "launch", "start", "run", "khol", "kholo", "chalao", "chala do"]):
            return AppLauncher.launch_app(query)

        # ─── 6. Close Application ─────────────────────────────────────────────
        if any(q.startswith(kw) for kw in ["close ", "band karo ", "band kar do ", "exit "]) or any(kw in q for kw in ["band karo", "band kar do", "close window", "close app"]):
            import os
            import subprocess
            app_query = re.sub(r"(?i)^(close|band karo|band kar do|exit)\s+", "", query).strip()
            app_query = re.sub(r"\s+(band karo|band kar do|ko band karo|ko band kar do)$", "", app_query).strip()
            if not app_query or app_query in ["app", "application", "window"]:
                import pyautogui
                pyautogui.hotkey('alt', 'f4')
                return True, "Closed active window, Boss."
            else:
                target_path, display_name = AppLauncher.resolve_app(app_query)
                if target_path and target_path.endswith(".exe"):
                    proc_name = os.path.basename(target_path)
                    subprocess.run(f"taskkill /f /im {proc_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True, f"Closed {display_name}, Boss."
                else:
                    import pyautogui
                    pyautogui.hotkey('alt', 'f4')
                    return True, f"Closed {display_name}, Boss."

        # ─── 8. Phase 5 Action Execution Pipeline ────────────────────────────
        from tools.computer.confirmation_manager import ConfirmationManager
        conf_mgr = ConfirmationManager.get_instance()

        if conf_mgr.has_pending_confirmation():
            pending = conf_mgr.get_pending_confirmation()
            if conf_mgr.is_affirmative_response(query):
                conf_mgr.clear()
                from tools.computer.action_executor import ActionExecutor
                executor = ActionExecutor()
                if pending.action:
                    res = executor.execute_action(pending.action, skip_verification=False)
                    return (res.status.value in ["COMPLETED", "VERIFIED_SUCCESS"]), f"Action executed successfully, Boss."
                elif pending.plan:
                    all_ok = True
                    for act in pending.plan.actions:
                        res = executor.execute_action(act, skip_verification=False)
                        if res.status.value not in ["COMPLETED", "VERIFIED_SUCCESS"]:
                            all_ok = False
                            break
                    return all_ok, "Action plan executed, Boss." if all_ok else "Plan execution encountered a problem."
            elif conf_mgr.is_negative_response(query):
                conf_mgr.clear()
                return True, "Action cancel kar diya gaya hai, Boss."

        # Process through ActionPlanner & SafetyValidator
        try:
            from tools.computer.action_planner import ActionPlanner
            from tools.computer.action_executor import ActionExecutor
            from tools.computer.action_model import ActionStatus

            planner = ActionPlanner()
            plan = planner.create_plan_from_request(query)

            if plan.requires_confirmation:
                conf_mgr.register_pending_confirmation(
                    request_id=plan.request_id,
                    plan=plan,
                    action=plan.actions[0] if plan.actions else None,
                    prompt=plan.actions[0].error or "Confirmation required"
                )
                conf_msg = plan.actions[0].error if plan.actions and plan.actions[0].error else f"Boss, ye action ('{query}') high risk hai. Confirm karu?"
                return True, conf_msg

            # Execute safe plan
            executor = ActionExecutor()
            success_count = 0
            for action in plan.actions:
                res = executor.execute_action(action)
                if res.status in [ActionStatus.COMPLETED, ActionStatus.VERIFYING]:
                    success_count += 1

            if success_count > 0:
                return True, f"Done Boss. '{query}' execute kar diya hai."
        except Exception as e:
            pass

        return False, "Unrecognized desktop command, Boss."
