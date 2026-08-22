"""
install_bridge.py

Installs the Jarvis CEP Bridge extension into Adobe Premiere Pro's
per-user CEP extensions folder and enables PlayerDebugMode in the
Windows registry so unsigned panels load without errors.

Run once:  python video_editing/cep_bridge/install_bridge.py
"""

import os
import sys
import shutil
import winreg
import subprocess

BRIDGE_SRC = os.path.dirname(os.path.abspath(__file__))
EXTENSION_ID = "com.jarvis.premiere.bridge"
CEP_EXTENSIONS_DIR = os.path.join(
    os.environ.get("APPDATA", ""), "Adobe", "CEP", "extensions"
)
INSTALL_DIR = os.path.join(CEP_EXTENSIONS_DIR, EXTENSION_ID)

# CSX versions that recent Premiere Pro releases use (most-to-least recent)
CSXS_VERSIONS = ["12", "11", "10", "9", "8", "7"]


def enable_player_debug_mode():
    """
    Write PlayerDebugMode=1 to all known CSXS registry keys so Premiere Pro
    loads unsigned (developer) CEP extensions.
    """
    for ver in CSXS_VERSIONS:
        key_path = f"Software\\Adobe\\CSXS.{ver}"
        try:
            key = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
            )
            winreg.SetValueEx(key, "PlayerDebugMode", 0, winreg.REG_SZ, "1")
            winreg.CloseKey(key)
            print(f"  [registry] Set PlayerDebugMode=1 for CSXS.{ver}")
        except Exception as exc:
            print(f"  [registry] Could not write CSXS.{ver}: {exc}")


def install_extension():
    """Copy the CEP bridge extension to the user's extensions folder."""
    os.makedirs(CEP_EXTENSIONS_DIR, exist_ok=True)

    if os.path.exists(INSTALL_DIR):
        print(f"  [install] Removing existing installation at:\n  {INSTALL_DIR}")
        shutil.rmtree(INSTALL_DIR)

    print(f"  [install] Copying bridge from:\n  {BRIDGE_SRC}\n  -> {INSTALL_DIR}")
    shutil.copytree(BRIDGE_SRC, INSTALL_DIR,
                    ignore=shutil.ignore_patterns("install_bridge.py", "__pycache__", "*.pyc"))
    print("  [install] Extension installed successfully.")


def main():
    print("=" * 60)
    print("  Jarvis CEP Bridge – Installer")
    print("=" * 60)

    # 1. Enable debug mode so Premiere loads the unsigned extension
    print("\n[Step 1] Enabling PlayerDebugMode in Windows registry …")
    enable_player_debug_mode()

    # 2. Copy the extension files
    print("\n[Step 2] Installing CEP extension …")
    install_extension()

    print("\n[Done] Restart Adobe Premiere Pro to load the Jarvis Bridge extension.")
    print("       After restarting, Jarvis can connect automatically.\n")


if __name__ == "__main__":
    main()
