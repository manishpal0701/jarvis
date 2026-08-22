"""
verify_install.py
Verifies that the Jarvis CEP Bridge is correctly installed for Premiere Pro 2021.
Run: python video_editing/cep_bridge/verify_install.py
"""
import os
import re
import sys

APPDATA = os.environ.get("APPDATA", "")
BASE = os.path.join(APPDATA, "Adobe", "CEP", "extensions", "com.jarvis.premiere.bridge")

REQUIRED_FILES = {
    "CSInterface.js": os.path.join(BASE, "CSInterface.js"),
    "index.html":     os.path.join(BASE, "index.html"),
    "manifest.xml":   os.path.join(BASE, "CSXS", "manifest.xml"),
    "bridge.jsx":     os.path.join(BASE, "jsx", "bridge.jsx"),
}

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

ok_count = 0
fail_count = 0

def check(label, passed, detail=""):
    global ok_count, fail_count
    icon = PASS if passed else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  {icon} {label}{suffix}")
    if passed:
        ok_count += 1
    else:
        fail_count += 1
    return passed

print("=" * 60)
print("  Jarvis CEP Bridge – Installation Verifier")
print("=" * 60)
print(f"\n  Install dir: {BASE}\n")

# ── File existence checks ──────────────────────────────────────
print("[1] Required Files:")
for name, path in REQUIRED_FILES.items():
    exists = os.path.isfile(path)
    size = os.path.getsize(path) if exists else 0
    check(name, exists, f"{size} bytes" if exists else "MISSING")

# ── manifest.xml content checks ───────────────────────────────
print("\n[2] manifest.xml Settings:")
mf_path = REQUIRED_FILES["manifest.xml"]
if os.path.isfile(mf_path):
    with open(mf_path, encoding="utf-8") as f:
        mf = f.read()
    check("Type=Panel (not Custom)", "<Type>Panel</Type>" in mf,
          "CRITICAL: Custom type prevents panel from loading" if "<Type>Custom</Type>" in mf else "")
    check("CSXS Version 9.0", 'Version="9.0"' in mf)
    check("AutoVisible=true", "<AutoVisible>true</AutoVisible>" in mf)
    check("--enable-nodejs", "--enable-nodejs" in mf)
    check("--mixed-context REMOVED", "--mixed-context" not in mf,
          "WARN: mixed-context can break Node.js require()" if "--mixed-context" in mf else "")
    check("ScriptPath present", "./jsx/bridge.jsx" in mf)
else:
    check("manifest.xml readable", False, "File missing")

# ── bridge.jsx content checks ─────────────────────────────────
print("\n[3] bridge.jsx Content:")
jsx_path = REQUIRED_FILES["bridge.jsx"]
if os.path.isfile(jsx_path):
    with open(jsx_path, encoding="utf-8") as f:
        jsx = f.read()
    check("$.global assignment", "$.global.JarvisBridge" in jsx)
    check("Double-load guard", "typeof $.global.JarvisBridge" in jsx)
    check("diagnostic() function", "function diagnostic()" in jsx)
    check("selfTest() function", "function selfTest()" in jsx)
    check("importFiles() function", "function importFiles(" in jsx)
    check("placeClipOnTimeline()", "function placeClipOnTimeline(" in jsx)
else:
    check("bridge.jsx readable", False, "File missing")

# ── index.html content checks ─────────────────────────────────
print("\n[4] index.html Content:")
html_path = REQUIRED_FILES["index.html"]
if os.path.isfile(html_path):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    check("Loads CSInterface.js", 'src="CSInterface.js"' in html)
    check("require(\"http\")", 'require("http")' in html)
    check("BRIDGE_PORT 7842", "7842" in html)
    check("handleHealthCheck", "handleHealthCheck" in html)
    check("handleCommand", "handleCommand" in html)
    check("EvalScript error detection", "EvalScript error" in html)
else:
    check("index.html readable", False, "File missing")

# ── CSInterface.js size check ─────────────────────────────────
print("\n[5] CSInterface.js Validity:")
cs_path = REQUIRED_FILES["CSInterface.js"]
if os.path.isfile(cs_path):
    size = os.path.getsize(cs_path)
    check("CSInterface.js non-empty", size > 1000, f"{size} bytes")
    with open(cs_path, encoding="utf-8", errors="replace") as f:
        cs_content = f.read()
    check("CSInterface class defined", "CSInterface" in cs_content)
else:
    check("CSInterface.js present", False, "MISSING - run install_bridge.py")

# ── Registry check ─────────────────────────────────────────────
print("\n[6] Registry (PlayerDebugMode):")
try:
    import winreg
    for ver in ["9", "10", "11"]:
        key_path = f"Software\\Adobe\\CSXS.{ver}"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "PlayerDebugMode")
            winreg.CloseKey(key)
            check(f"CSXS.{ver} PlayerDebugMode=1", val == "1", f"value={val}")
        except FileNotFoundError:
            check(f"CSXS.{ver} PlayerDebugMode", False, "key not found")
except ImportError:
    print("  [WARN] winreg not available (non-Windows)")

# ── Summary ──────────────────────────────────────────────────
print()
print("=" * 60)
total = ok_count + fail_count
print(f"  Result: {ok_count}/{total} checks passed")
if fail_count == 0:
    print()
    print("  ALL CHECKS PASSED.")
    print()
    print("  NEXT STEP:")
    print("  1. Close Adobe Premiere Pro 2021 completely.")
    print("  2. Reopen Adobe Premiere Pro 2021.")
    print("  3. Go to: Window -> Extensions -> Jarvis Bridge")
    print("  4. The panel should appear (even if tiny).")
    print("  5. Run Jarvis and ask it to edit a video.")
else:
    print()
    print(f"  {fail_count} check(s) FAILED. Run install_bridge.py to fix.")
    print("  python video_editing/cep_bridge/install_bridge.py")
print("=" * 60)

sys.exit(0 if fail_count == 0 else 1)
