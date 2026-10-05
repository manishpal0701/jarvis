"""
video_editing/software/premiere_project_controller.py
Phase 6 Premiere Pro Project & DOM Readiness Controller.
Manages full readiness lifecycle: PROCESS_NOT_RUNNING -> LAUNCHING -> WINDOW_READY ->
HOME_SCREEN -> CREATING_PROJECT -> NEW_PROJECT_DIALOG -> PROJECT_LOADING ->
PROJECT_WORKSPACE -> DOM_READY -> FAILED.
Handles Home Screen auto-creation via ExtendScript, Windows UI Automation fallback (Alt+F->N->P / Ctrl+Alt+N + Enter),
CEP extension panel opening (Alt+W->E), Start Screen overlay dismissal (Esc / Ctrl+Alt+N + Enter), direct project file launch fallback,
and continuous modal dialog dismissal (Enter), executing bounded readiness polling with 120-second timeout.
"""

import os
import sys
import time
import json
import requests
import subprocess
from typing import Dict, Any, Optional

from video_editing.software.premiere_window_controller import PremiereWindowController
from video_editing.software.safe_keyboard import SafeKeyboardAutomation

STATE_PROCESS_NOT_RUNNING = "PROCESS_NOT_RUNNING"
STATE_LAUNCHING = "LAUNCHING"
STATE_WINDOW_READY = "WINDOW_READY"
STATE_HOME_SCREEN = "HOME_SCREEN"
STATE_CREATING_PROJECT = "CREATING_PROJECT"
STATE_NEW_PROJECT_DIALOG = "NEW_PROJECT_DIALOG"
STATE_PROJECT_LOADING = "PROJECT_LOADING"
STATE_PROJECT_WORKSPACE = "PROJECT_WORKSPACE"
STATE_DOM_READY = "DOM_READY"
STATE_FAILED = "FAILED"

BRIDGE_URL = "http://127.0.0.1:7842"
COMMAND_URL = f"{BRIDGE_URL}/command"
EVAL_URL = f"{BRIDGE_URL}/eval"
PING_URL = f"{BRIDGE_URL}/ping"
HEALTHCHECK_URL = f"{BRIDGE_URL}/healthcheck"

PROJECT_READY_TIMEOUT = 120.0
POLL_INTERVAL = 2.0


class PremiereProjectController:
    """
    Manages Premiere Pro process detection, CEP extension auto-panel launch, Home Screen project creation,
    Windows UI automation fallback, direct file open fallback, modal dialog dismissal, and bounded DOM readiness polling.
    """

    def __init__(self):
        self.state = STATE_PROCESS_NOT_RUNNING
        self.current_project_path: Optional[str] = None
        self.last_failure_reason: Optional[str] = None

    def ensure_project_workspace_ready(
        self,
        project_name: str = "Jarvis_Live_Project",
        timeout: float = PROJECT_READY_TIMEOUT,
        poll_interval: float = POLL_INTERVAL
    ) -> Dict[str, Any]:
        """
        Ensures Premiere Pro process is running, opens CEP extension panel if needed,
        handles Home Screen state via ExtendScript, Windows UI Automation fallback (Alt+F->N->P / Ctrl+Alt+N + Enter),
        or direct file launch fallback, and polls until DOM APIs are ready.
        """
        print("[PREMIERE_READINESS]\nstatus=STARTING_CHECK", flush=True)

        if not self.current_project_path:
            proj_dir = os.path.abspath(f"data/video_editing/projects/jarvis_{int(time.time())}").replace("\\", "/")
            os.makedirs(proj_dir, exist_ok=True)
            self.current_project_path = f"{proj_dir}/{project_name}.prproj"

        xml_template_path = self.current_project_path.replace(".prproj", ".xml")
        if not os.path.isfile(xml_template_path):
            xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="5">
  <sequence id="sequence-1">
    <name>{project_name}</name>
    <duration>300</duration>
    <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
    <media><video><format><samplecharacteristics><width>1920</width><height>1080</height></samplecharacteristics></format><track></track></video></media>
  </sequence>
</xmeml>
"""
            try:
                with open(xml_template_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
            except Exception:
                pass

        if not os.path.isfile(self.current_project_path):
            import gzip
            prproj_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="3">
  <Project ObjectRef="1">
    <Name>{project_name}</Name>
  </Project>
</PremiereData>
"""
            try:
                with gzip.open(self.current_project_path, "wb") as gf:
                    gf.write(prproj_xml.encode("utf-8"))
            except Exception:
                pass

        # 1. Process Check & Launch
        pid = PremiereWindowController.get_running_pid()
        if not pid:
            self.state = STATE_LAUNCHING
            print("[PREMIERE_READINESS]\nstate=LAUNCHING", flush=True)
            PremiereWindowController.ensure_premiere_running_and_focused(xml_template_path)
            pid = PremiereWindowController.get_running_pid()

        self.state = STATE_WINDOW_READY
        print(f"[PREMIERE_READINESS]\nstate=WINDOW_READY\npid={pid}", flush=True)
        PremiereWindowController.bring_to_foreground()

        # 2. Wait for HTTP server to respond with CEP panel auto-opening & process restart fallback
        deadline = time.time() + timeout
        server_alive = False
        panel_triggered = False
        restarted_stale_process = False

        while time.time() < deadline:
            try:
                r = requests.get(PING_URL, timeout=2.0)
                if r.status_code == 200 and r.json().get("app") == "JarvisBridge":
                    server_alive = True
                    break
            except Exception:
                if not panel_triggered:
                    panel_triggered = True
                    self.trigger_open_cep_extension_panel()

                if not restarted_stale_process and (deadline - time.time()) < (timeout - 10.0):
                    restarted_stale_process = True
                    print("[PREMIERE_READINESS]\nstatus=RESTARTING_PREMIERE_STALE_CEP_PROCESS", flush=True)
                    subprocess.run("taskkill /F /IM \"Adobe Premiere Pro.exe\"", shell=True, check=False)
                    time.sleep(2.0)
                    PremiereWindowController.ensure_premiere_running_and_focused()
                    time.sleep(4.0)

            time.sleep(poll_interval)

        if not server_alive:
            self.state = STATE_FAILED
            self.last_failure_reason = f"CEP bridge HTTP server not responding on port 7842 within {timeout}s."
            raise RuntimeError(f"PREMIERE_READINESS_FAILED: {self.last_failure_reason}")

        # 3. Poll DOM diagnostics & handle Home Screen with bounded recovery
        extendscript_attempts = 0
        ui_fallback_attempts = 0
        file_launch_attempts = 0
        post_recovery_polls = 0

        while time.time() < deadline:
            diag = self.check_dom_diagnostics()

            # Case A: Project workspace loaded & verified
            if diag.get("project_exists"):
                if self.state != STATE_PROJECT_WORKSPACE and self.state != STATE_DOM_READY:
                    self.state = STATE_PROJECT_WORKSPACE
                    print("[PREMIERE_READINESS]\nstate=PROJECT_WORKSPACE", flush=True)

                if diag.get("dom_ready"):
                    self.state = STATE_DOM_READY
                    print(f"[PREMIERE_READINESS]\nstate=DOM_READY\nproject={diag.get('project_path') or project_name}", flush=True)
                    return diag

            # Case B: Home Screen or Loading (no active project yet)
            elif diag.get("process_running") and not diag.get("project_exists"):
                if self.state != STATE_HOME_SCREEN and self.state != STATE_PROJECT_LOADING:
                    self.state = STATE_HOME_SCREEN
                    print("[PREMIERE_READINESS]\nstate=HOME_SCREEN", flush=True)

                # Attempt 1: Open project template via executable & ExtendScript creation
                if extendscript_attempts < 1:
                    if "unittest" not in sys.modules:
                        exe_path = PremiereWindowController.find_premiere_install_path()
                        if exe_path and os.path.isfile(xml_template_path):
                            print(f"[PREMIERE_READINESS]\nopening_project_template_directly={xml_template_path}", flush=True)
                            subprocess.Popen([exe_path, xml_template_path], shell=False)
                            time.sleep(2.0)

                    self.state = STATE_CREATING_PROJECT
                    print(f"[PREMIERE_READINESS]\nstate=CREATING_PROJECT\nname={project_name}", flush=True)

                    # Send Ctrl+N + Enter safely to close Home Screen overlay and create project in Premiere Pro 2021
                    PremiereWindowController.bring_to_foreground()
                    def _send_ctrl_n():
                        ps_script = """
$wshell = New-Object -ComObject wscript.shell
Start-Sleep -Milliseconds 300
$wshell.SendKeys('^n')
Start-Sleep -Milliseconds 600
$wshell.SendKeys('{ENTER}')
Start-Sleep -Milliseconds 400
$wshell.SendKeys('{ENTER}')
"""
                        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False)

                    SafeKeyboardAutomation.send_key_safely("create_project_ctrl_n", _send_ctrl_n)
                    if "unittest" not in sys.modules:
                        time.sleep(1.5)

                    create_res = self.create_project_extendscript(project_name, target_path=self.current_project_path)
                    extendscript_attempts += 1

                    if create_res.get("ok"):
                        self.state = STATE_PROJECT_LOADING
                        print("[PREMIERE_READINESS]\nstate=PROJECT_LOADING", flush=True)
                        if "unittest" not in sys.modules:
                            time.sleep(1.0)
                        continue
                    else:
                        err_msg = create_res.get("error", {})
                        if isinstance(err_msg, dict):
                            err_msg = err_msg.get("message", str(err_msg))
                        self.last_failure_reason = f"ExtendScript createProject returned error: {err_msg}"
                        print(f"[PREMIERE_READINESS_NOTICE] ExtendScript project creation failed: {self.last_failure_reason}", flush=True)

                # Attempt 2: Windows UI Automation Fallback (Alt+F->N->P / Ctrl+Alt+N + Enter)
                if ui_fallback_attempts < 1:
                    print(f"[PREMIERE_READINESS]\ntriggering_ui_automation_fallback=True (attempt {ui_fallback_attempts + 1})", flush=True)
                    self.trigger_ui_automation_new_project()
                    ui_fallback_attempts += 1
                    self.state = STATE_PROJECT_LOADING
                    print("[PREMIERE_READINESS]\nstate=PROJECT_LOADING", flush=True)
                    if "unittest" not in sys.modules:
                        time.sleep(1.0)
                    continue

                # Attempt 3: Direct Project File Open Fallback
                if file_launch_attempts < 1:
                    print(f"[PREMIERE_READINESS]\ntriggering_file_launch_fallback=True (attempt {file_launch_attempts + 1})", flush=True)
                    self.trigger_direct_project_file_open(project_name)
                    file_launch_attempts += 1
                    self.state = STATE_PROJECT_LOADING
                    print("[PREMIERE_READINESS]\nstate=PROJECT_LOADING", flush=True)
                    if "unittest" not in sys.modules:
                        time.sleep(3.0)
                    continue

                # Bounded recovery check: allow up to 10 polls (20s) for Premiere to load project workspace after recovery actions
                if extendscript_attempts >= 1 and ui_fallback_attempts >= 1 and file_launch_attempts >= 1:
                    post_recovery_polls += 1
                    print(f"[PREMIERE_READINESS]\nwaiting_for_project_load_post_recovery={post_recovery_polls}/10", flush=True)

                    # State-aware check: ONLY press Enter if an actual modal dialog window is detected
                    if PremiereWindowController.is_modal_dialog_present():
                        PremiereWindowController.bring_to_foreground()
                        def _send_enter_modal():
                            ps_script = """
$wshell = New-Object -ComObject wscript.shell
Start-Sleep -Milliseconds 100
$wshell.SendKeys('{ENTER}')
"""
                            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False)

                        SafeKeyboardAutomation.send_key_safely("state_aware_modal_dismiss_enter", _send_enter_modal)

                    if post_recovery_polls >= 10:
                        self.state = STATE_FAILED
                        failure_summary = (
                            f"PREMIERE_READINESS_FAILED: Exceeded maximum project creation recovery attempts ({extendscript_attempts} ExtendScript, {ui_fallback_attempts} UI Automation, {file_launch_attempts} File Launch). "
                            f"Premiere remains on HOME_SCREEN. Reason: {self.last_failure_reason or 'app.project remained null'}"
                        )
                        print(f"[PREMIERE_READINESS]\nstate=FAILED\nreason={failure_summary}", flush=True)
                        raise RuntimeError(failure_summary)

            time.sleep(poll_interval)

        self.state = STATE_FAILED
        failure_summary = (
            f"PREMIERE_READINESS_TIMEOUT: Premiere project workspace did not reach DOM_READY within {timeout}s. "
            f"Original reason: {self.last_failure_reason or 'app.project was null'}"
        )
        raise RuntimeError(failure_summary)

    def check_dom_diagnostics(self) -> Dict[str, Any]:
        """
        Queries bridge for ExtendScript app and project DOM diagnostic flags.
        Returns structured diagnostic payload matching required schema.
        """
        diag = {
            "process_running": True,
            "window_found": True,
            "home_screen": True,
            "new_project_dialog": (self.state == STATE_NEW_PROJECT_DIALOG),
            "project_exists": False,
            "project_path": None,
            "root_item_ready": False,
            "sequence_count": 0,
            "dom_ready": False,
            "failure_reason": self.last_failure_reason
        }

        try:
            r = requests.post(HEALTHCHECK_URL, timeout=3.0)
            if r.status_code == 200:
                data = r.json()
                checks = data.get("checks", {})
                details = data.get("details", {}).get("apis", {}) if isinstance(data.get("details"), dict) else {}

                diag["project_exists"] = bool(checks.get("Active Project Ready") or details.get("projectAPI"))
                diag["root_item_ready"] = bool(details.get("rootItemAccessible"))
                diag["home_screen"] = not diag["project_exists"]
                diag["dom_ready"] = bool(diag["project_exists"] and checks.get("Timeline API Ready") and checks.get("Import API Ready"))
                diag["project_path"] = details.get("projectName")
        except Exception as exc:
            diag["failure_reason"] = str(exc)

        return diag

    def create_project_extendscript(self, project_name: str, target_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends ExtendScript createProject command to HTTP CEP server.
        """
        if target_path:
            self.current_project_path = target_path
        elif not self.current_project_path:
            proj_dir = os.path.abspath(f"data/video_editing/projects/jarvis_{int(time.time())}").replace("\\", "/")
            os.makedirs(proj_dir, exist_ok=True)
            self.current_project_path = f"{proj_dir}/{project_name}.prproj"

        safe_path = self.current_project_path.replace("\\", "/")
        payload = {
            "command": "createProject",
            "args": {
                "name": project_name,
                "targetPath": safe_path
            }
        }

        try:
            r = requests.post(COMMAND_URL, json=payload, timeout=10.0)
            return r.json()
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def trigger_open_cep_extension_panel(self):
        """
        Sends Alt+W -> E -> Enter to Premiere Pro to open Window -> Extensions -> Jarvis Bridge panel.
        """
        print("[UI_AUTOMATION]\nstatus=OPENING_CEP_EXTENSION_PANEL_MENU", flush=True)
        PremiereWindowController.bring_to_foreground()
        time.sleep(0.5)

        def _send_cep_menu():
            ps_cmd = (
                'powershell -Command "'
                '$wshell = New-Object -ComObject wscript.shell; '
                '[void]$wshell.AppActivate(\'Adobe Premiere Pro\'); '
                'Start-Sleep -Milliseconds 300; '
                '$wshell.SendKeys(\'%we\'); '
                'Start-Sleep -Milliseconds 500; '
                '$wshell.SendKeys(\'{ENTER}\')'
                '"'
            )
            subprocess.run(ps_cmd, shell=True, check=False)

        SafeKeyboardAutomation.send_key_safely("open_cep_extension_panel_menu", _send_cep_menu)

    def trigger_ui_automation_new_project(self):
        """
        Windows UI Automation Fallback: Brings Premiere to front, sends Alt+F -> N -> P & Ctrl+Alt+N,
        opens New Project dialog, and presses Enter to confirm creation.
        """
        print("[UI_AUTOMATION]\nstatus=STARTING_NEW_PROJECT_FALLBACK", flush=True)

        PremiereWindowController.bring_to_foreground()
        time.sleep(0.5)

        # 1. Send Ctrl+Alt+N / Alt+F+N+P (New Project shortcut in Premiere Pro)
        def _send_new_project_shortcut():
            try:
                import pyautogui  # type: ignore
                pyautogui.hotkey("ctrl", "alt", "n")
                time.sleep(0.3)
                pyautogui.hotkey("ctrl", "n")
                print("[UI_AUTOMATION]\nsent_hotkey=ctrl+alt+n", flush=True)
            except Exception:
                pass

            ps_script = """
$wshell = New-Object -ComObject wscript.shell
Start-Sleep -Milliseconds 300
$wshell.SendKeys('%f')
Start-Sleep -Milliseconds 300
$wshell.SendKeys('n')
Start-Sleep -Milliseconds 300
$wshell.SendKeys('p')
Start-Sleep -Milliseconds 400
$wshell.SendKeys('{ENTER}')
"""
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False)
            print("[UI_AUTOMATION]\nsent_ps_sendkeys=alt_f_n_p", flush=True)

        SafeKeyboardAutomation.send_key_safely("ui_automation_new_project_hotkeys", _send_new_project_shortcut)

        self.state = STATE_NEW_PROJECT_DIALOG
        print("[PREMIERE_READINESS]\nstate=NEW_PROJECT_DIALOG", flush=True)
        time.sleep(0.8)

        # 2. Press Enter to submit & confirm default project settings
        def _send_confirm_enter():
            try:
                import pyautogui  # type: ignore
                pyautogui.press("enter")
                print("[UI_AUTOMATION]\nsent_key=enter", flush=True)
            except Exception:
                ps_script = """
$wshell = New-Object -ComObject wscript.shell
Start-Sleep -Milliseconds 200
$wshell.SendKeys('{ENTER}')
"""
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False)

        SafeKeyboardAutomation.send_key_safely("ui_automation_confirm_new_project", _send_confirm_enter)
        time.sleep(1.0)

    def trigger_direct_project_file_open(self, project_name: str):
        """
        Direct Project File Fallback: Creates empty project XML or launches Premiere with project path,
        and sends Enter to confirm the Import XML / Save Project modal dialog.
        """
        print("[PROJECT_FILE_FALLBACK]\nstatus=LAUNCHING_PROJECT_FILE", flush=True)
        if not self.current_project_path:
            proj_dir = os.path.abspath(f"data/video_editing/projects/jarvis_{int(time.time())}").replace("\\", "/")
            os.makedirs(proj_dir, exist_ok=True)
            self.current_project_path = f"{proj_dir}/{project_name}.prproj"

        xml_path = self.current_project_path.replace(".prproj", ".xml")
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="5">
  <sequence id="sequence-1">
    <name>{project_name}</name>
    <duration>300</duration>
    <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>
    <media><video><format><samplecharacteristics><width>1920</width><height>1080</height></samplecharacteristics></format><track></track></video></media>
  </sequence>
</xmeml>
"""
        try:
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

            if not os.path.isfile(self.current_project_path):
                import gzip
                prproj_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<PremiereData Version="3">
  <Project ObjectRef="1">
    <Name>{project_name}</Name>
  </Project>
</PremiereData>
"""
                try:
                    with gzip.open(self.current_project_path, "wb") as gf:
                        gf.write(prproj_xml.encode("utf-8"))
                except Exception:
                    pass

            exe_path = PremiereWindowController.find_premiere_install_path()
            if exe_path and os.path.isfile(exe_path):
                subprocess.Popen([exe_path, self.current_project_path], shell=False)
                print(f"[PROJECT_FILE_FALLBACK]\nopened_prproj_with_premiere={self.current_project_path}", flush=True)
            else:
                os.startfile(self.current_project_path)
                print(f"[PROJECT_FILE_FALLBACK]\nos_startfile={self.current_project_path}", flush=True)

            time.sleep(2.5)

            # State-aware check: Bring Premiere window to front and press Enter ONLY if modal dialog present
            if PremiereWindowController.is_modal_dialog_present():
                PremiereWindowController.bring_to_foreground()
                time.sleep(0.5)

                def _send_modal_enter():
                    try:
                        import pyautogui  # type: ignore
                        pyautogui.press("enter")
                        print("[PROJECT_FILE_FALLBACK]\nsent_key=enter_to_confirm_modal", flush=True)
                    except Exception:
                        ps_script = """
$wshell = New-Object -ComObject wscript.shell
Start-Sleep -Milliseconds 300
$wshell.SendKeys('{ENTER}')
"""
                        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False)
                        print("[PROJECT_FILE_FALLBACK]\nsent_ps_sendkeys=enter_to_confirm_modal", flush=True)

                SafeKeyboardAutomation.send_key_safely("direct_project_file_modal_enter", _send_modal_enter)

        except Exception as exc:
            print(f"[PROJECT_FILE_FALLBACK_ERROR] {exc}", flush=True)
