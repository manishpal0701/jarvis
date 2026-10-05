"""
scratch/production_app_builder_e2e.py
Production End-to-End Test for Phase 2 JARVIS App Builder Runtime Pipeline.
Tests the full production pipeline using real production classes:
CommandRouter -> AppManager -> AppDevelopmentOrchestrator -> Flutter & Node Generators -> IDE Launchers.
"""
import os
import sys
import time
import shutil
import logging
import subprocess

# Add project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ProductionE2ETest")

def run_production_e2e():
    print("=" * 60)
    print("STARTING PRODUCTION APP BUILDER E2E TEST")
    print("=" * 60)

    from conversation.command_router import CommandRouter
    from tools.app_builder.app_manager import AppManager
    from tools.app_builder.app_model import AppState
    from tools.app_builder.app_orchestrator import AppDevelopmentOrchestrator

    # 1. Reset AppManager state
    app_mgr = AppManager()
    app_mgr.reset()

    # Capture spoken output
    spoken_messages = []
    def mock_speak(text):
        print(f"[JARVIS_SPEAK]: {text}")
        spoken_messages.append(text)

    router = CommandRouter(speak_callback=mock_speak)

    # 2. Simulate User Command: "Jarvis ek Android app bana do"
    print("\n--- STEP 1: Command Entry ---")
    router.process_user_input("Jarvis ek Android app bana do", source="chat")

    active_app = app_mgr.get_active_app()
    assert active_app is not None, "FAILED: Active app project not created!"
    print(f"Active App ID: {active_app.app_id}, Status: {active_app.status}")

    # 3. Simulate Brief Input: "App ka naam Expense Manager hai. Features: login, expense tracking, categories, monthly reports and dark theme."
    print("\n--- STEP 2: Brief Collection ---")
    router.process_user_input(
        "App ka naam Expense Manager hai. Features: login, expense tracking, categories, monthly reports and dark theme.",
        source="chat"
    )

    updated_app = app_mgr.get_active_app()
    assert updated_app is not None, "FAILED: Active app lost!"
    print(f"Updated App Name: '{updated_app.name}', Status: {updated_app.status}")

    # 4. Trigger Development Pipeline synchronously for test verification
    print("\n--- STEP 3: Execute Full Pipeline ---")
    orchestrator = AppDevelopmentOrchestrator(speak_callback=mock_speak)
    completed_app = orchestrator.execute_pipeline(updated_app)

    print("\n--- STEP 4: Status Assertion ---")
    print(f"Completed App Status: {completed_app.status}")
    assert completed_app.status == AppState.COMPLETED, f"FAILED: App pipeline did not reach COMPLETED! Status is {completed_app.status}"

    # 5. Physical File Assertions
    print("\n--- STEP 5: Physical Workspace File Assertions ---")
    frontend_path = completed_app.frontend_path
    backend_path = completed_app.backend_path

    print(f"Frontend Workspace Path: {frontend_path}")
    print(f"Backend Workspace Path: {backend_path}")

    assert os.path.exists(frontend_path), "FAILED: Frontend folder does not exist!"
    assert os.path.exists(backend_path), "FAILED: Backend folder does not exist!"

    pubspec_file = os.path.join(frontend_path, "pubspec.yaml")
    main_dart_file = os.path.join(frontend_path, "lib", "main.dart")
    android_dir = os.path.join(frontend_path, "android")
    android_app_dir = os.path.join(frontend_path, "android", "app")
    android_gradle_item = os.path.join(frontend_path, "android", "gradle")
    if not os.path.exists(android_gradle_item):
        android_gradle_item = os.path.join(frontend_path, "android", "build.gradle")

    pkg_json_file = os.path.join(backend_path, "package.json")
    server_js_file = os.path.join(backend_path, "src", "server.js")
    if not os.path.exists(server_js_file):
        server_js_file = os.path.join(backend_path, "server.js")

    print(f"Checking {pubspec_file}: {os.path.exists(pubspec_file)}")
    print(f"Checking {main_dart_file}: {os.path.exists(main_dart_file)}")
    print(f"Checking {android_dir}: {os.path.exists(android_dir)}")
    print(f"Checking {android_app_dir}: {os.path.exists(android_app_dir)}")
    print(f"Checking {android_gradle_item}: {os.path.exists(android_gradle_item)}")
    print(f"Checking {pkg_json_file}: {os.path.exists(pkg_json_file)}")
    print(f"Checking {server_js_file}: {os.path.exists(server_js_file)}")

    assert os.path.exists(pubspec_file), "FAILED: pubspec.yaml missing!"
    assert os.path.exists(main_dart_file), "FAILED: lib/main.dart missing!"
    assert os.path.exists(android_dir), "FAILED: android/ missing!"
    assert os.path.exists(android_app_dir), "FAILED: android/app/ missing!"
    assert os.path.exists(android_gradle_item), "FAILED: android gradle structure missing!"
    assert os.path.exists(pkg_json_file), "FAILED: backend package.json missing!"
    assert os.path.exists(server_js_file), "FAILED: backend server.js missing!"

    # 6. Check running processes on host Windows machine
    print("\n--- STEP 6: Process Verification ---")
    try:
        res = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=5)
        tasklist_out = res.stdout.lower()
        has_studio = "studio64.exe" in tasklist_out or "studio.exe" in tasklist_out
        has_code = "code.exe" in tasklist_out or "code.cmd" in tasklist_out
        print(f"Android Studio Running in Windows Task Manager: {has_studio}")
        print(f"VS Code Running in Windows Task Manager: {has_code}")
    except Exception as ex:
        print(f"Tasklist check exception: {ex}")

    print("\n" + "=" * 60)
    print("PRODUCTION APP BUILDER E2E TEST COMPLETED SUCCESSFULLY (PASS)")
    print("=" * 60)

if __name__ == "__main__":
    run_production_e2e()
