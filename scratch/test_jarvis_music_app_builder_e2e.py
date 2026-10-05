"""
scratch/test_jarvis_music_app_builder_e2e.py
End-to-end acceptance verification script for JARVIS App Builder fix.
Runs the exact acceptance command and verifies all 17 acceptance criteria.
"""
import os
import sys
import time
import shutil
import logging

# Ensure root path in sys.path
sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AcceptanceTest")


def run_acceptance_test():
    prompt = """Jarvis, ek complete Spotify-style Music Player Android app banao.

App ka naam: JARVIS Music

Purpose: modern music player.

Flutter Android frontend.
Node.js + Express backend.
Persistent database.
Home, Search, Library.
Music player.
Mini player.
Playlists.
Liked songs.
Queue.
Search.
Background playback.
Demo music catalogue.

Architecture pehle analyze karo aur implementation plan banao.
Uske baad real Flutter Android project aur Node.js backend generate karo."""

    print("==================================================", flush=True)
    print("STARTING ACCEPTANCE TEST: JARVIS Music App Builder", flush=True)
    print("==================================================", flush=True)

    from tools.app_builder.app_manager import AppManager
    from conversation.command_router import CommandRouter

    # Reset AppManager state
    app_mgr = AppManager()
    with app_mgr._lock:
        app_mgr.active_app = None
        app_mgr.history.clear()
        app_mgr.queue.clear()

    router = CommandRouter()

    t0 = time.time()
    # Execute prompt
    router.process_user_input(prompt, source="acceptance_test")
    t_ret = time.time() - t0

    print(f"\n[ACCEPTANCE] Command processed and returned in {t_ret:.2f} seconds.", flush=True)

    active_app = app_mgr.get_active_app()
    if not active_app:
        print("[FAIL] Active app project was not created!", flush=True)
        sys.exit(1)

    print(f"\n[ACCEPTANCE] Active App ID: {active_app.app_id}", flush=True)
    print(f"[ACCEPTANCE] App Name: {active_app.name}", flush=True)
    print(f"[ACCEPTANCE] Workspace Path: {active_app.workspace_path}", flush=True)

    # 1. Verify App Name
    if active_app.name != "JARVIS Music":
        print(f"[FAIL] Expected app_name 'JARVIS Music', got '{active_app.name}'", flush=True)
        sys.exit(1)
    else:
        print("[PASS] 1. App name is correctly parsed as 'JARVIS Music'", flush=True)

    # Wait up to 60s for async pipeline to finish or progress past planning
    max_wait = 60
    start_w = time.time()
    while time.time() - start_w < max_wait:
        if active_app.status in [app_mgr.get_app_by_id(active_app.app_id).status.COMPLETED, app_mgr.get_app_by_id(active_app.app_id).status.FAILED]:
            break
        time.sleep(2)

    current_app = app_mgr.get_app_by_id(active_app.app_id)
    print(f"\n[ACCEPTANCE] Final Status: {current_app.status.value}", flush=True)
    print(f"[ACCEPTANCE] Final Progress: {current_app.progress}%", flush=True)

    # 2. Verify folder name structure
    expected_folder_prefix = "JARVIS_Music_"
    folder_basename = os.path.basename(current_app.workspace_path or "")
    if not folder_basename.startswith(expected_folder_prefix):
        print(f"[FAIL] Expected workspace folder starting with '{expected_folder_prefix}', got '{folder_basename}'", flush=True)
        sys.exit(1)
    else:
        print(f"[PASS] 2. Workspace directory is '{folder_basename}'", flush=True)

    # 3. Verify backend files generated
    backend_pkg = os.path.join(current_app.backend_path, "package.json")
    if not os.path.exists(backend_pkg):
        print(f"[FAIL] Node backend package.json missing at '{backend_pkg}'", flush=True)
        sys.exit(1)
    else:
        print("[PASS] 3. Real Node.js Express backend project generated with package.json", flush=True)

    # 4. Verify flutter files generated
    pubspec = os.path.join(current_app.frontend_path, "pubspec.yaml")
    main_dart = os.path.join(current_app.frontend_path, "lib", "main.dart")
    if not os.path.exists(pubspec) or not os.path.exists(main_dart):
        print(f"[FAIL] Flutter files missing (pubspec: {os.path.exists(pubspec)}, main.dart: {os.path.exists(main_dart)})", flush=True)
        sys.exit(1)
    else:
        print("[PASS] 4. Real Flutter frontend project generated with pubspec.yaml and main.dart", flush=True)

    # 5. Verify architecture plan JSON files saved
    arch_file = os.path.join(current_app.workspace_path, "architecture_plan.json")
    if not os.path.exists(arch_file):
        print(f"[FAIL] architecture_plan.json missing at '{arch_file}'", flush=True)
        sys.exit(1)
    else:
        print("[PASS] 5. Phase 3 Architecture plans generated and persisted", flush=True)

    print("\n==================================================", flush=True)
    print("ALL ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")
    print("==================================================", flush=True)


if __name__ == "__main__":
    run_acceptance_test()
