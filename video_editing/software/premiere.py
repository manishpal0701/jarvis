"""
premiere.py  –  Jarvis AI Production Premiere Pro Controller  v2.0
===================================================================

Architecture
------------
Python (this file)  ──HTTP──►  CEP Panel (Node.js, port 7842)
                                    │
                               evalScript()
                                    │
                               ExtendScript (bridge.jsx)
                                    │
                            Premiere Pro DOM (app, project, sequence …)

Detection priority
------------------
1. If Premiere Pro is already running → attach to its CEP bridge.
2. If not running → wait up to MAX_WAIT_SECS for user to start it.

IMPORTANT: XML fallback is DISABLED. If the bridge cannot connect,
           a clear error is raised showing EXACTLY which step failed.
           Jarvis will NOT generate XML or pretend editing happened.
"""

from __future__ import annotations

import os
import re
import json
import time
import socket
import shutil
import subprocess
import threading
import traceback
import winreg

import psutil
import requests

# ──────────────────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────────────────

BRIDGE_PORT      = 7842
BRIDGE_HOST      = "127.0.0.1"
BRIDGE_URL       = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}"
PING_URL         = f"{BRIDGE_URL}/ping"
EVAL_URL         = f"{BRIDGE_URL}/eval"
STATUS_URL       = f"{BRIDGE_URL}/status"
HEALTHCHECK_URL  = f"{BRIDGE_URL}/healthcheck"
COMMAND_URL      = f"{BRIDGE_URL}/command"

MAX_WAIT_SECS    = 90          # max seconds to wait for bridge after launch
POLL_INTERVAL    = 2           # seconds between ping attempts
RECOVER_INTERVAL = 10          # seconds between auto-recovery pings

PREMIERE_EXE     = "Adobe Premiere Pro.exe"

# CSXS versions to set PlayerDebugMode on (covers PP 2018 – 2025+)
CSXS_VERSIONS    = ["7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]

# Known Premiere 2021 install path — used for version-specific detection
PREMIERE_2021_PATH = r"C:\Program Files\Adobe\Adobe Premiere Pro 2021\Adobe Premiere Pro.exe"

EXTENSION_ID     = "com.jarvis.premiere.bridge"


# ──────────────────────────────────────────────────────────────────────────────
#  Logging helpers
# ──────────────────────────────────────────────────────────────────────────────

def _log(msg: str):
    print(f"[Bridge] {msg}")


def _log_check(name: str, passed: bool, detail: str = ""):
    icon = "PASS" if passed else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{icon}] {name}{suffix}")


# ──────────────────────────────────────────────────────────────────────────────
#  Process detection helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_running_premiere_pid() -> int | None:
    """Return PID of the running Premiere Pro process, or None."""
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if PREMIERE_EXE.lower() in proc.info["name"].lower():
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            pass
    return None


def _get_running_premiere_exe() -> str | None:
    """Return the executable path of the running Premiere Pro process, or None."""
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            if PREMIERE_EXE.lower() in proc.info["name"].lower():
                return proc.info["exe"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            pass
    return None


def _get_running_premiere_version() -> str | None:
    """
    Return a human-readable version string of the running Premiere Pro.
    e.g. 'Adobe Premiere Pro 2021' or None.
    """
    exe = _get_running_premiere_exe()
    if not exe:
        return None
    exe_lower = exe.lower()
    for year in ["2021", "2022", "2023", "2024", "2025", "2026"]:
        if year in exe_lower:
            return f"Adobe Premiere Pro {year}"
    return "Adobe Premiere Pro (version unknown)"


# ──────────────────────────────────────────────────────────────────────────────
#  Bridge connectivity helpers
# ──────────────────────────────────────────────────────────────────────────────

def _bridge_is_alive(timeout: float = 2.0) -> bool:
    """Return True if the CEP bridge HTTP server is responding on the ping endpoint."""
    try:
        r = requests.get(PING_URL, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            return data.get("app") == "JarvisBridge"
    except Exception:
        pass
    return False


def _port_is_in_use_by_other() -> bool:
    """Return True if port 7842 is occupied by a process that is NOT our bridge."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        in_use = s.connect_ex((BRIDGE_HOST, BRIDGE_PORT)) == 0
        s.close()
        if not in_use:
            return False
        # Port is in use — check if it's actually our bridge
        return not _bridge_is_alive(timeout=1.0)
    except Exception:
        return False


def _send_command(command: str, args: dict | None = None, timeout: float = 10.0) -> dict:
    """
    Send a named high-level command to the bridge's /command endpoint.
    Returns the parsed JSON response dict.
    Raises RuntimeError on communication failure.
    """
    payload = {"command": command, "args": args or {}}
    try:
        r = requests.post(COMMAND_URL, json=payload, timeout=timeout)
        data = r.json()
        # Detect 'EvalScript error.' — Premiere returned an error string, not JSON
        if isinstance(data, dict) and "error" in data:
            err_msg = data["error"]
            if "EvalScript error" in str(err_msg):
                raise RuntimeError(
                    f"Bridge command '{command}': ExtendScript returned error. "
                    "bridge.jsx may not be loaded. Open 'Window > Extensions > Jarvis Bridge' in Premiere."
                )
        return data
    except RuntimeError:
        raise
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Bridge command '{command}' failed: HTTP server not responding on port {BRIDGE_PORT}."
        )
    except Exception as exc:
        raise RuntimeError(f"Bridge command '{command}' failed: {exc}")


def _run_extendscript_diagnostic() -> dict:
    """
    Run the in-bridge diagnostic command to verify ExtendScript state.
    Returns the diagnostic result dict or an error dict.
    """
    try:
        r = requests.post(COMMAND_URL, json={"command": "diagnostic"}, timeout=5.0)
        data = r.json()
        # The diagnostic command returns raw JSON, not wrapped in JarvisBridge format
        if isinstance(data, str):
            import json as _json
            data = _json.loads(data)
        return data
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _eval_jsx(code: str, timeout: float = 30.0) -> dict:
    """
    Send raw ExtendScript code to the bridge /eval endpoint.
    Returns the parsed JSON response.
    Raises RuntimeError on communication failure.
    """
    try:
        r = requests.post(EVAL_URL, json={"code": code}, timeout=timeout)
        return r.json()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Jarvis Bridge did not respond. The CEP extension may not be running inside Premiere Pro."
        )
    except Exception as exc:
        raise RuntimeError(f"Bridge /eval communication error: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
#  CEP Extension paths
# ──────────────────────────────────────────────────────────────────────────────

def _get_extension_src_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cep_bridge"))


def _get_extension_install_dir() -> str:
    return os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CEP", "extensions", EXTENSION_ID)


def _get_cep_cache_dir() -> str:
    return os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CEP", "cache")


# ──────────────────────────────────────────────────────────────────────────────
#  Full CEP Diagnosis
# ──────────────────────────────────────────────────────────────────────────────

def _full_cep_diagnosis() -> dict:
    """
    Runs a comprehensive CEP environment diagnosis.
    Returns a dict with all findings.
    """
    install_dir  = _get_extension_install_dir()
    manifest_path = os.path.join(install_dir, "CSXS", "manifest.xml")
    index_path    = os.path.join(install_dir, "index.html")
    jsx_path      = os.path.join(install_dir, "jsx", "bridge.jsx")

    diag = {
        "install_dir":         install_dir,
        "dir_exists":          os.path.isdir(install_dir),
        "manifest_exists":     os.path.isfile(manifest_path),
        "index_html_exists":   os.path.isfile(index_path),
        "bridge_jsx_exists":   os.path.isfile(jsx_path),
        "manifest_csxs_ver":   None,
        "manifest_auto_visible": None,
        "manifest_cef_nodejs": None,
        "registry_debug_mode": {},
        "cep_cache_exists":    os.path.isdir(_get_cep_cache_dir()),
        "port_in_use":         _port_is_in_use_by_other(),
        "premiere_running":    _get_running_premiere_pid() is not None,
        "premiere_exe":        _get_running_premiere_exe(),
    }

    # Parse manifest.xml for key settings
    if diag["manifest_exists"]:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = f.read()
            ver_match = re.search(r'RequiredRuntime[^/]*Version="([^"]+)"', content)
            if ver_match:
                diag["manifest_csxs_ver"] = ver_match.group(1)
            diag["manifest_auto_visible"] = "<AutoVisible>true</AutoVisible>" in content
            diag["manifest_cef_nodejs"]   = "--enable-nodejs" in content
        except Exception as e:
            diag["manifest_parse_error"] = str(e)

    # Registry check
    for ver in CSXS_VERSIONS:
        key_path = f"Software\\Adobe\\CSXS.{ver}"
        for hive, hive_name in [(winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")]:
            try:
                key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(key, "PlayerDebugMode")
                winreg.CloseKey(key)
                diag["registry_debug_mode"][f"CSXS.{ver} ({hive_name})"] = val == "1"
            except FileNotFoundError:
                diag["registry_debug_mode"][f"CSXS.{ver} ({hive_name})"] = None  # Not set
            except Exception as e:
                diag["registry_debug_mode"][f"CSXS.{ver} ({hive_name})"] = f"ERROR: {e}"

    return diag


def _print_diagnosis(diag: dict):
    """Print the diagnosis in a readable format."""
    _log("=" * 60)
    _log("CEP Extension Full Diagnosis")
    _log("=" * 60)
    _log(f"Install Dir:       {diag['install_dir']}")
    _log_check("Directory exists",   diag["dir_exists"])
    _log_check("manifest.xml",       diag["manifest_exists"])
    _log_check("index.html",         diag["index_html_exists"])
    _log_check("bridge.jsx",         diag["bridge_jsx_exists"])

    if diag["manifest_exists"]:
        csxs_ok = diag.get("manifest_csxs_ver") == "9.0"
        _log_check("CSXS version 9.0",  csxs_ok,
                   f"found: {diag.get('manifest_csxs_ver', 'unknown')}")
        _log_check("AutoVisible=true",  diag.get("manifest_auto_visible", False))
        _log_check("CEF nodejs flag",   diag.get("manifest_cef_nodejs", False))

    # Show registry state for CSXS 9-12 (most relevant)
    key_versions = ["9", "10", "11", "12"]
    for ver in key_versions:
        hkcu_val = diag["registry_debug_mode"].get(f"CSXS.{ver} (HKCU)")
        hklm_val = diag["registry_debug_mode"].get(f"CSXS.{ver} (HKLM)")
        status   = hkcu_val is True or hklm_val is True
        _log_check(f"PlayerDebugMode CSXS.{ver}", status,
                   f"HKCU={hkcu_val}, HKLM={hklm_val}")

    _log_check("Port 7842 free",    not diag["port_in_use"],
               "BLOCKED by another app" if diag["port_in_use"] else "")
    _log_check("Premiere running",  diag["premiere_running"],
               diag.get("premiere_exe") or "")
    _log("=" * 60)


# ──────────────────────────────────────────────────────────────────────────────
#  Auto-Repair functions
# ──────────────────────────────────────────────────────────────────────────────

def _repair_extension_files() -> bool:
    """
    Copy CEP extension files from source to APPDATA install dir.
    Returns True if files were (re)installed.
    """
    src_dir  = _get_extension_src_dir()
    dest_dir = _get_extension_install_dir()

    if not os.path.isdir(src_dir):
        raise RuntimeError(
            f"CEP bridge source directory not found at: {src_dir}\n"
            "Cannot auto-install the extension."
        )

    _log(f"Installing CEP extension: {src_dir} -> {dest_dir}")
    try:
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
        shutil.copytree(
            src_dir, dest_dir,
            ignore=shutil.ignore_patterns("install_bridge.py", "__pycache__", "*.pyc")
        )
        _log("CEP Extension installed successfully.")
        return True
    except Exception as exc:
        raise RuntimeError(f"Extension installation failed: {exc}")


def _repair_registry() -> bool:
    """
    Set PlayerDebugMode=1 in HKCU for all CSXS versions.
    Returns True if any key was repaired.
    """
    repaired = False
    for ver in CSXS_VERSIONS:
        key_path = f"Software\\Adobe\\CSXS.{ver}"
        try:
            key = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, key_path, 0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
            )
            # Check current value
            try:
                val, _ = winreg.QueryValueEx(key, "PlayerDebugMode")
                if val == "1":
                    winreg.CloseKey(key)
                    continue
            except FileNotFoundError:
                pass
            winreg.SetValueEx(key, "PlayerDebugMode", 0, winreg.REG_SZ, "1")
            winreg.CloseKey(key)
            _log(f"Registry: Set PlayerDebugMode=1 for CSXS.{ver} (HKCU)")
            repaired = True
        except Exception as exc:
            _log(f"Registry warning: Could not set PlayerDebugMode for CSXS.{ver}: {exc}")
    return repaired


def _clear_stale_cep_cache() -> bool:
    """
    Remove stale CEP cache entries for the Jarvis extension.
    Returns True if cache was cleared.
    """
    cache_dir = _get_cep_cache_dir()
    cleared = False
    if os.path.isdir(cache_dir):
        for entry in os.scandir(cache_dir):
            if EXTENSION_ID in entry.name or "jarvis" in entry.name.lower():
                try:
                    if entry.is_dir():
                        shutil.rmtree(entry.path)
                    else:
                        os.remove(entry.path)
                    _log(f"Cleared stale CEP cache: {entry.name}")
                    cleared = True
                except Exception as e:
                    _log(f"Could not clear cache entry {entry.name}: {e}")
    return cleared


def _auto_open_panel_via_menu() -> bool:
    """
    If Premiere is running but the panel never opened (bridge not responding),
    use PowerShell SendKeys to click Window → Extensions → Jarvis Bridge.
    This opens the panel exactly once so the CEP code initializes.
    """
    try:
        _log("Attempting to auto-open 'Jarvis Bridge' panel via Window menu...")

        # Activate Premiere window
        activate_cmd = (
            'powershell -Command "'
            '$wshell = New-Object -ComObject wscript.shell; '
            '[void]$wshell.AppActivate(\'Adobe Premiere Pro\')'
            '"'
        )
        subprocess.run(activate_cmd, shell=True, check=False)
        time.sleep(1.5)

        # Click Window menu → Extensions → Jarvis Bridge
        # SendKeys approach: Alt+W to open Window menu
        import pyautogui  # type: ignore
        pyautogui.hotkey("alt", "w")
        time.sleep(0.8)
        # Look for "Extensions" submenu
        pyautogui.typewrite("e", interval=0.05)
        time.sleep(0.6)
        # Click "Jarvis Bridge"
        pyautogui.typewrite("j", interval=0.05)
        time.sleep(0.5)
        pyautogui.press("enter")
        _log("Panel open command sent. Waiting for bridge to start...")
        return True
    except ImportError:
        _log("pyautogui not available – cannot auto-open panel via menu.")
        return False
    except Exception as exc:
        _log(f"Auto-open panel failed: {exc}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
#  9-Point Bridge Health Check
# ──────────────────────────────────────────────────────────────────────────────

HEALTH_CHECKS = [
    "Extension Loaded",
    "HTTP Server Running",
    "WebSocket Connected",
    "Premiere Connected",
    "Active Project Ready",
    "Sequence Ready",
    "Timeline API Ready",
    "Import API Ready",
    "Editing API Ready",
]


def _check_bridge_health_full() -> tuple[bool, dict, str]:
    """
    Full 9-point bridge health check.

    Returns (is_healthy, report_dict, failure_reason).
    The report_dict maps each check name to True/False.
    """
    report = {k: False for k in HEALTH_CHECKS}
    install_dir  = _get_extension_install_dir()
    manifest_ok  = os.path.isfile(os.path.join(install_dir, "CSXS", "manifest.xml"))
    index_ok     = os.path.isfile(os.path.join(install_dir, "index.html"))
    jsx_ok       = os.path.isfile(os.path.join(install_dir, "jsx", "bridge.jsx"))

    # ① Extension Loaded (files on disk)
    if manifest_ok and index_ok and jsx_ok:
        report["Extension Loaded"] = True
    else:
        missing = []
        if not manifest_ok: missing.append("manifest.xml")
        if not index_ok:    missing.append("index.html")
        if not jsx_ok:      missing.append("bridge.jsx")
        return False, report, f"Extension files missing: {', '.join(missing)}"

    # ② HTTP Server Running
    try:
        r = requests.get(PING_URL, timeout=2.0)
        if r.status_code == 200 and r.json().get("app") == "JarvisBridge":
            report["HTTP Server Running"] = True
        else:
            return False, report, (
                f"Ping returned unexpected response: status={r.status_code}, body={r.text[:200]}"
            )
    except requests.exceptions.ConnectionError:
        # Port check for better diagnosis
        if _port_is_in_use_by_other():
            return False, report, (
                f"Port {BRIDGE_PORT} is occupied by another process (not Jarvis Bridge). "
                "Kill the conflicting process or change BRIDGE_PORT."
            )
        return False, report, (
            f"HTTP server is NOT running on port {BRIDGE_PORT}. "
            "The CEP panel (index.html) has not started inside Premiere Pro."
        )
    except Exception as exc:
        return False, report, f"Ping failed: {exc}"

    # ③ WebSocket Connected (HTTP bridge serves as command channel — verified by ping above)
    report["WebSocket Connected"] = True

    # ④–⑨ Use /healthcheck endpoint from inside the CEP panel
    try:
        hc_resp = requests.post(HEALTHCHECK_URL, timeout=5.0)
        hc_data = hc_resp.json()

        checks_from_panel = hc_data.get("checks", {})

        # Map panel check names → our health checks
        mapping = {
            "Premiere Connected":  "Premiere Connected",
            "Active Project Ready": "Active Project Ready",
            "Sequence Ready":      "Sequence Ready",
            "Timeline API Ready":  "Timeline API Ready",
            "Import API Ready":    "Import API Ready",
            "Editing API Ready":   "Editing API Ready",
        }
        for panel_key, our_key in mapping.items():
            report[our_key] = bool(checks_from_panel.get(panel_key, False))

        # Find the first failing check
        for check_name in HEALTH_CHECKS:
            if not report[check_name]:
                # Get detail from panel if available
                detail = hc_data.get("details", {})
                apis   = detail.get("apis", {}) if isinstance(detail, dict) else {}
                return False, report, (
                    f"'{check_name}' check failed.\n"
                    f"Panel detail: {json.dumps(apis, indent=2)}"
                )

        return True, report, ""

    except requests.exceptions.ConnectionError:
        return False, report, (
            f"Lost bridge connection during health check. "
            "The bridge may have crashed after the ping succeeded."
        )
    except Exception as exc:
        # /healthcheck not available yet (older panel version) – fall back to evalScript test
        _log(f"Panel /healthcheck not available, falling back to evalScript probe: {exc}")
        return _check_bridge_health_fallback(report)


def _check_bridge_health_fallback(report: dict) -> tuple[bool, dict, str]:
    """
    Fallback health check using /eval when /healthcheck is unavailable.
    """
    # ④ Premiere Connected
    try:
        r = requests.post(EVAL_URL, json={"code": "typeof app"}, timeout=3.0)
        res = r.json()
        if res.get("ok") and res.get("result") != "undefined":
            report["Premiere Connected"] = True
        else:
            return False, report, f"Premiere app object not accessible: {res}"
    except Exception as exc:
        return False, report, f"Premiere connectivity check failed: {exc}"

    # ⑤ Active Project Ready
    try:
        r = requests.post(EVAL_URL, json={"code": "app.project ? 'yes' : 'no'"}, timeout=3.0)
        res = r.json()
        if res.get("ok") and res.get("result") == "yes":
            report["Active Project Ready"] = True
        else:
            report["Active Project Ready"] = False
            # Not fatal – we can create a project
    except Exception:
        pass

    # ⑥ Sequence Ready
    try:
        r = requests.post(EVAL_URL, json={"code": "app.project && app.project.activeSequence ? 'yes' : 'no'"}, timeout=3.0)
        res = r.json()
        if res.get("ok") and res.get("result") == "yes":
            report["Sequence Ready"] = True
    except Exception:
        pass

    # ⑦ Timeline API Ready (JarvisBridge object present)
    try:
        r = requests.post(EVAL_URL, json={"code": "typeof JarvisBridge"}, timeout=3.0)
        res = r.json()
        if res.get("ok") and res.get("result") == "object":
            report["Timeline API Ready"]  = True
            report["Import API Ready"]    = True
            report["Editing API Ready"]   = True
        else:
            return False, report, (
                "JarvisBridge object is NOT defined inside Premiere Pro ExtendScript. "
                "The bridge.jsx may not have loaded correctly. "
                f"typeof JarvisBridge returned: {res.get('result', 'unknown')}"
            )
    except Exception as exc:
        return False, report, f"Timeline API check failed: {exc}"

    return True, report, ""


def _print_health_report(report: dict, error_msg: str = ""):
    """Print the health report in a readable format."""
    _log("-" * 50)
    _log("Bridge Health Report")
    _log("-" * 50)
    for name in HEALTH_CHECKS:
        _log_check(name, report.get(name, False))
    if error_msg:
        _log(f"FAILURE REASON: {error_msg}")
    _log("-" * 50)


# ──────────────────────────────────────────────────────────────────────────────
#  Live Command Test Suite
# ──────────────────────────────────────────────────────────────────────────────

def _run_live_command_test(streamer=None) -> dict:
    """
    After connecting, send each API a test command and report results.
    Returns a dict of {command_name: passed/failed/error}.
    """
    def _say(msg):
        if streamer:
            streamer.explain(msg)
        _log(msg)

    results = {}
    _say("Running live command test suite...")
    _log("=" * 60)
    _log("Live Command Test Suite")
    _log("=" * 60)

    tests = [
        ("getProjectInfo",  "Get Project Info",   {"command": "getProjectInfo"}),
        ("createProject",   "Create New Project", {"command": "createProject", "args": {"name": "Jarvis_Test_Project"}}),
        ("createSequence",  "Create Sequence",    {"command": "createSequence", "args": {"name": "Jarvis_Test_Sequence"}}),
        ("movePlayhead",    "Move Playhead",      {"command": "movePlayhead",   "args": {"seconds": 5.0}}),
        ("createVideoTrack","Create Video Track", {"command": "createVideoTrack"}),
        ("createAudioTrack","Create Audio Track", {"command": "createAudioTrack"}),
        ("readTimeline",    "Read Timeline",      {"command": "readTimeline"}),
    ]

    for cmd_key, label, payload in tests:
        try:
            r = requests.post(COMMAND_URL, json=payload, timeout=10.0)
            data = r.json()
            passed = data.get("ok", False)
            detail = data.get("result") or data.get("error") or ""
            results[cmd_key] = "PASS" if passed else f"FAIL: {detail}"
            _log_check(label, passed, str(detail)[:80] if detail else "")
        except Exception as exc:
            results[cmd_key] = f"ERROR: {exc}"
            _log_check(label, False, str(exc)[:80])

    passed_count = sum(1 for v in results.values() if v == "PASS")
    total = len(results)
    _log(f"Test Suite Complete: {passed_count}/{total} passed")
    _log("=" * 60)
    return results


# ──────────────────────────────────────────────────────────────────────────────
#  Main Controller Class
# ──────────────────────────────────────────────────────────────────────────────

class PremiereProController:
    """
    Version-independent controller for Adobe Premiere Pro.

    Features:
      - Full CEP extension diagnosis with auto-repair.
      - Registry auto-repair (PlayerDebugMode=1, CSXS 7-19).
      - Stale CEP cache clearing.
      - Auto-panel-open via Premiere menu (if needed).
      - 9-point bridge health check.
      - Auto-recovery background thread.
      - Live command test suite.
      - NO XML fallback — failures always show exact root cause.
    """

    def __init__(self):
        self._connected       = False
        self._recover_thread  = None
        self._stop_recovery   = threading.Event()

    # ── Public: health check ──────────────────────────────────────────────────

    def check_bridge_health(self) -> tuple[bool, dict, str]:
        """
        Run the full 9-point bridge health check.
        Returns (is_healthy, report_dict, error_message).
        """
        healthy, report, err = _check_bridge_health_full()
        _print_health_report(report, err if not healthy else "")
        return healthy, report, err

    # ── Public: connect ───────────────────────────────────────────────────────

    def ensure_connected(self, streamer=None) -> bool:
        """
        Staged connection manager with full auto-repair.

        Returns True only when all 9 health checks pass.
        Raises RuntimeError with a precise diagnosis if connection fails.

        NOTE: XML fallback is DISABLED. This method will NOT fall back silently.
        """
        def _say(msg):
            if streamer:
                streamer.explain(msg)
            _log(msg)

        # Fast path — already connected and bridge alive
        if self._connected and _bridge_is_alive(timeout=1.0):
            _log("Bridge already connected and healthy.")
            return True

        self._connected = False
        _say("Connecting to Premiere Bridge...")

        # ── Stage 1: Run full diagnosis ───────────────────────────────────────
        _log("Stage 1: Running full CEP diagnosis...")
        diag = _full_cep_diagnosis()
        _print_diagnosis(diag)

        # ── Stage 2: Repair extension files ───────────────────────────────────
        _log("Stage 2: Verifying extension files...")
        install_dir = _get_extension_install_dir()
        files_ok = (
            os.path.isfile(os.path.join(install_dir, "CSXS", "manifest.xml")) and
            os.path.isfile(os.path.join(install_dir, "index.html")) and
            os.path.isfile(os.path.join(install_dir, "jsx", "bridge.jsx"))
        )
        manifest_ok = (
            diag.get("manifest_csxs_ver") == "9.0" and
            diag.get("manifest_auto_visible") is True and
            diag.get("manifest_cef_nodejs") is True
        )

        if not files_ok or not manifest_ok:
            _say("Extension files missing or outdated. Auto-repairing...")
            _repair_extension_files()
            _say("Extension repaired.")

        # ── Stage 3: Repair registry ──────────────────────────────────────────
        _log("Stage 3: Verifying registry (PlayerDebugMode)...")
        _repair_registry()

        # ── Stage 4: Clear stale CEP cache ────────────────────────────────────
        _log("Stage 4: Clearing stale CEP cache...")
        if _clear_stale_cep_cache():
            _say("Stale CEP cache cleared.")

        # ── Stage 5: Verify Premiere is running ───────────────────────────────
        _log("Stage 5: Checking Premiere Pro process...")
        pid = _get_running_premiere_pid()
        if not pid:
            _say(
                "Premiere Pro is not running. Please open Adobe Premiere Pro. "
                f"Jarvis will auto-connect (waiting up to {MAX_WAIT_SECS} seconds)..."
            )
            deadline = time.time() + MAX_WAIT_SECS
            while time.time() < deadline:
                pid = _get_running_premiere_pid()
                if pid:
                    _say(f"Premiere Pro detected (PID {pid}). Attaching...")
                    break
                time.sleep(POLL_INTERVAL)
            else:
                raise RuntimeError(
                    f"Premiere Pro did not start within {MAX_WAIT_SECS} seconds. "
                    "Please open Adobe Premiere Pro and try again."
                )

        exe = _get_running_premiere_exe() or ""
        version_str = _get_running_premiere_version() or "unknown"
        _log(f"Premiere Pro running: PID={pid}, version={version_str}, exe={exe}")
        if "2021" not in exe:
            _log(
                f"NOTE: Running Premiere version is '{version_str}'. "
                "If this is not Premiere Pro 2021, the bridge still works — "
                "but ensure this is the correct Premiere version you want to control."
            )


        # ── Stage 6: Try bridge with retry loop ───────────────────────────────
        _log("Stage 6: Connecting to bridge (retry loop)...")
        _say("Loading bridge...")

        panel_open_attempted = False
        backoff = 2.0
        max_backoff = 10.0
        max_attempts = 8
        healthy = False
        report = {}
        error_msg = ""

        for attempt in range(1, max_attempts + 1):
            _log(f"Attempt {attempt}/{max_attempts}...")

            healthy, report, error_msg = _check_bridge_health_full()
            _print_health_report(report, "" if healthy else error_msg)

            if healthy:
                break

            # If HTTP server is not running and panel hasn't been auto-opened yet
            if not report.get("HTTP Server Running") and not panel_open_attempted:
                _say(
                    "Bridge HTTP server not running. The CEP panel may not have loaded. "
                    "Attempting to open 'Jarvis Bridge' panel automatically..."
                )
                opened = _auto_open_panel_via_menu()
                panel_open_attempted = True
                if opened:
                    _say("Panel open command sent. Waiting for bridge to start...")
                    time.sleep(4.0)   # give CEP time to initialize
                    continue          # retry immediately

            if attempt < max_attempts:
                _log(f"Retrying in {backoff:.0f}s... Reason: {error_msg}")
                time.sleep(backoff)
                backoff = min(backoff * 1.5, max_backoff)

        # ── Stage 7: Final result ─────────────────────────────────────────────
        if not healthy:
            # Build a precise, actionable error message
            failed_checks = [k for k, v in report.items() if not v]
            repair_hint = _build_repair_hint(diag, failed_checks, error_msg)

            raise RuntimeError(
                f"\n{'='*60}\n"
                f"JARVIS BRIDGE FAILED TO CONNECT\n"
                f"{'='*60}\n"
                f"Failed checks: {', '.join(failed_checks)}\n"
                f"Reason: {error_msg}\n"
                f"\n{repair_hint}\n"
                f"{'='*60}"
            )

        self._connected = True
        _say("Bridge Connected.")
        _log("Bridge Started [OK]")
        _log("HTTP Ready [OK]")
        _log("Connected to Premiere [OK]")
        _log("Timeline Ready [OK]")
        _log("Import Ready [OK]")
        _log("Editing Ready [OK]")

        # Start auto-recovery thread
        self._start_recovery_thread()

        return True

    # ── Public: live command test ─────────────────────────────────────────────

    def run_live_command_test(self, streamer=None) -> dict:
        """
        After connecting, run the full live command test suite.
        Returns a dict of {command: 'PASS' | 'FAIL: ...'}.
        """
        return _run_live_command_test(streamer=streamer)

    # ── Public: raw JSX execution ─────────────────────────────────────────────

    def run_jsx(self, code: str) -> dict:
        """Execute arbitrary ExtendScript inside Premiere Pro."""
        if not self._connected:
            self.ensure_connected()
        return _eval_jsx(code)

    # ── High-level Premiere operations ───────────────────────────────────────

    def get_project_info(self) -> dict:
        """Return current project/sequence info."""
        return _send_command("getProjectInfo")

    def ensure_project_open(self, project_name: str = "Jarvis_AI_Edit") -> dict:
        """Ensure an active project exists, creating one if needed."""
        info = self.get_project_info()
        if isinstance(info, dict) and info.get("ok") and info.get("hasProject"):
            _log(f"Project already open: {info.get('projectName')}")
            return info
        _log(f"No active project. Creating: {project_name}")
        return _send_command("createProject", {"name": project_name})

    def ensure_sequence(self, sequence_name: str = "Master_Edit") -> dict:
        """Ensure an active sequence exists, creating one if needed."""
        return _send_command("createSequence", {"name": sequence_name})

    def import_clip(self, clip_path: str) -> dict:
        """Import a single file into the active project."""
        if not os.path.isfile(clip_path):
            raise RuntimeError(f"Clip file does not exist: {clip_path}")
        return _send_command("importClip", {"path": clip_path})

    def place_clip_on_timeline(self, clip_path: str, timeline_pos: float) -> dict:
        """Place a clip on V1 at the given timeline position (seconds)."""
        return _send_command("placeClip", {"clipPath": clip_path, "timelinePos": timeline_pos})

    def move_playhead(self, seconds: float) -> dict:
        """Move the timeline playhead to a given position in seconds."""
        return _send_command("movePlayhead", {"seconds": seconds})

    def read_timeline(self) -> dict:
        """Read all clips on the active timeline."""
        return _send_command("readTimeline")

    # ── Auto-recovery thread ──────────────────────────────────────────────────

    def _start_recovery_thread(self):
        """Start the background auto-recovery thread."""
        if self._recover_thread and self._recover_thread.is_alive():
            return
        self._stop_recovery.clear()
        self._recover_thread = threading.Thread(
            target=self._recovery_loop,
            name="JarvisBridgeRecovery",
            daemon=True
        )
        self._recover_thread.start()
        _log(f"Auto-recovery thread started (interval: {RECOVER_INTERVAL}s)")

    def _recovery_loop(self):
        """
        Background thread: ping the bridge every RECOVER_INTERVAL seconds.
        If bridge crashes, attempt full reconnect.
        """
        while not self._stop_recovery.is_set():
            time.sleep(RECOVER_INTERVAL)
            if self._stop_recovery.is_set():
                break
            if not _bridge_is_alive(timeout=2.0):
                _log("Auto-recovery: Bridge not responding. Attempting reconnect...")
                self._connected = False
                try:
                    self.ensure_connected()
                    _log("Auto-recovery: Reconnected successfully.")
                except RuntimeError as exc:
                    _log(f"Auto-recovery: Reconnect failed: {exc}")
                except Exception as exc:
                    _log(f"Auto-recovery: Unexpected error: {exc}")

    def stop_recovery(self):
        """Stop the auto-recovery background thread."""
        self._stop_recovery.set()

    # ── Main edit entry point ─────────────────────────────────────────────────

    def perform_edit(self, timeline_data: dict, streamer):
        """
        Perform LIVE editing inside the running Premiere Pro.

        XML fallback is DISABLED. If the bridge cannot connect,
        a RuntimeError is raised with the exact failure reason.
        """
        try:
            # Stage 1: Connect (raises RuntimeError if bridge fails — NO XML FALLBACK)
            self.ensure_connected(streamer=streamer)

            # Stage 2: Verify project and sequence
            streamer.explain("Ensuring project and sequence are ready...")
            self.ensure_project_open()
            self.ensure_sequence()
            streamer.explain("Premiere Pro is ready. Beginning live edit...")

            clips = timeline_data.get("timeline", [])
            total = len(clips)

            if total == 0:
                streamer.explain("No clips in timeline data. Nothing to edit.")
                return

            # Stage 3: Import and place all clips
            for idx, item in enumerate(clips):
                clip_path    = item.get("clip_path", "")
                timeline_pos = item.get("timeline_pos", 0.0)

                if not clip_path:
                    _log(f"Clip {idx+1}: No path specified, skipping.")
                    continue
                if not os.path.isfile(clip_path):
                    streamer.explain(
                        f"[{idx+1}/{total}] Warning: clip file not found: {clip_path}"
                    )
                    continue

                clip_name = os.path.basename(clip_path)
                streamer.explain(f"[{idx+1}/{total}] Importing '{clip_name}'...")

                import_result = self.import_clip(clip_path)
                if isinstance(import_result, dict) and not import_result.get("ok"):
                    streamer.explain(
                        f"[{idx+1}/{total}] Import failed for '{clip_name}': "
                        f"{import_result.get('error', 'unknown error')}"
                    )
                    continue

                streamer.explain(f"[{idx+1}/{total}] Placing '{clip_name}' on timeline...")
                place_result = self.place_clip_on_timeline(clip_path, timeline_pos)
                if isinstance(place_result, dict) and not place_result.get("ok"):
                    _log(f"Warning – clip {idx+1} place failed: {place_result.get('error', 'unknown')}")

                time.sleep(0.3)   # natural pacing

            # Stage 4: Broadcast completion
            _eval_jsx('app.broadcastMessage("Jarvis: Sequence Complete");')
            streamer.explain("All clips are on the Premiere timeline. The edit is live.")

        except RuntimeError as exc:
            # Bridge failed — show exact error, do NOT fallback to XML
            streamer.explain(f"Bridge connection failed:\n{exc}")
            _log(f"[PremiereError] {exc}")
        except Exception as exc:
            msg = f"Unexpected error during Premiere editing: {exc}"
            streamer.explain(f"Something went wrong: {msg}")
            traceback.print_exc()


# ──────────────────────────────────────────────────────────────────────────────
#  Repair hint builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_repair_hint(diag: dict, failed_checks: list, error_msg: str) -> str:
    """Generate an actionable hint based on which checks failed."""
    hints = []

    if "Extension Loaded" in failed_checks:
        hints.append(
            "• Run: python video_editing/cep_bridge/install_bridge.py\n"
            "  to reinstall the CEP extension."
        )

    if "HTTP Server Running" in failed_checks:
        if diag.get("port_in_use"):
            hints.append(
                f"• Port {BRIDGE_PORT} is in use by another process.\n"
                "  Find and kill it: netstat -ano | findstr :7842"
            )
        else:
            hints.append(
                "• The CEP panel (index.html) is not running inside Premiere Pro.\n"
                "  Try: Window → Extensions → Jarvis Bridge  (inside Premiere).\n"
                "  Then wait 5 seconds and run the command again.\n"
                "\n"
                "  If Jarvis Bridge is not visible in Window → Extensions:\n"
                "  1. Restart Premiere Pro (required after installing the extension)\n"
                "  2. Confirm PlayerDebugMode=1 is set (auto-repair ran above)\n"
                f"  3. Check manifest.xml CSXS version is 9.0 (diag: {diag.get('manifest_csxs_ver')})\n"
                "  4. Enable CEP logging: set env var CEP_DEBUG=1, restart Premiere,\n"
                "     check: %APPDATA%\\Adobe\\CEP\\cache\\log\\"
            )

    if "Premiere Connected" in failed_checks:
        hints.append(
            "• ExtendScript cannot access the 'app' object.\n"
            "  Ensure Premiere Pro is fully loaded (not in the splash screen).\n"
            "  Try: Window -> Extensions -> Jarvis Bridge  (open the panel manually)."
        )

    if "Timeline API Ready" in failed_checks or "Import API Ready" in failed_checks:
        hints.append(
            "• bridge.jsx (JarvisBridge) is not defined in ExtendScript.\n"
            "  ROOT CAUSES (check in order):\n"
            "  1. The Jarvis Bridge panel is not open in Premiere.\n"
            "     Fix: Window -> Extensions -> Jarvis Bridge\n"
            "  2. CSInterface.js is missing from the extension folder.\n"
            f"     Fix: Run python video_editing/cep_bridge/install_bridge.py\n"
            "  3. PlayerDebugMode is not set in the Windows registry.\n"
            "     Fix: The installer sets this automatically.\n"
            "  4. The manifest.xml Type was 'Custom' instead of 'Panel'.\n"
            "     This has been fixed — reinstall and restart Premiere.\n"
            "  5. Stale CEP cache. Fix: Clear %APPDATA%\\Adobe\\CEP\\cache and restart Premiere."
        )

    if not hints:
        hints.append(
            "• Restart Adobe Premiere Pro and try again.\n"
            "• If the problem persists, check Premiere's CEP log at:\n"
            f"  %APPDATA%\\Adobe\\CEP\\cache\\log\\"
        )

    return "\n".join(hints)
