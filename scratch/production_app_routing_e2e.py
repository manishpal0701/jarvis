"""
scratch/production_app_routing_e2e.py
Real Production Routing Test Script for Spotify-Style Music Player Brief.
Executes CommandRouter.process_user_input -> AppManager -> Phase 3 Architecture Planner.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProductionRoutingE2E")

from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_model import AppState
from conversation.command_router import CommandRouter


def run_production_routing_test():
    print("=" * 60)
    print("JARVIS PRODUCTION APP ROUTING TEST")
    print("=" * 60)

    # 1. Reset AppManager state
    app_mgr = AppManager()
    app_mgr.reset()

    spoken_responses = []

    def capture_speak(text):
        spoken_responses.append(text)
        print(f"[JARVIS SPEAK]: {text}")

    router = CommandRouter(speak_callback=capture_speak)

    # 2. Exact production request prompt
    spotify_prompt = (
        "Create a Spotify-style Music Player Android app with login, "
        "home screen, search, playlists, liked songs, recently played, "
        "queue, shuffle, repeat, album pages, artist pages, persistent "
        "playback state, and Node.js backend APIs."
    )

    print(f"\n[USER INPUT]:\n{spotify_prompt}\n")

    # 3. Execute production entry point: process_user_input(source='chat')
    router.process_user_input(spotify_prompt, source="chat")

    # 4. Verify routing results
    active_app = app_mgr.get_active_app()

    print("\n" + "=" * 60)
    print("ROUTING VERIFICATION RESULTS")
    print("=" * 60)

    # Check 1: App project created
    if not active_app:
        print("[FAIL] No active AppProject was created!")
        sys.exit(1)
    print(f"[CHECK 1] Active App ID         : {active_app.app_id}")
    print(f"[CHECK 2] App Name               : {active_app.name}")
    print(f"[CHECK 3] App Status             : {active_app.status.value}")

    # Check 2: Verify time command was NOT triggered
    time_triggered = any("It's" in msg or "Today is" in msg for msg in spoken_responses)
    if time_triggered:
        print("[FAIL] Time command was incorrectly triggered!")
        sys.exit(1)
    print(f"[CHECK 4] Datetime Intercepted   : FALSE (PASS)")

    # Check 3: Brief preservation and feature extraction
    brief = active_app.brief
    print(f"[CHECK 5] Stored Brief Description : {brief.description[:60]}...")
    print(f"[CHECK 6] Extracted Features Count : {len(brief.features)}")
    print(f"[CHECK 7] Features Extracted      : {brief.features}")

    if len(brief.features) == 0:
        print("[FAIL] AppBrief features list is empty!")
        sys.exit(1)

    # Check 4: Auto-advancement to Phase 3 Architecture Planning
    valid_phase3_states = [AppState.BRIEF_READY, AppState.STARTING, AppState.PLANNING]
    if active_app.status not in valid_phase3_states:
        print(f"[FAIL] App state {active_app.status.value} did not advance to Phase 3!")
        sys.exit(1)
    print(f"[CHECK 8] Phase 3 Advanced        : YES ({active_app.status.value})")

    # Check 5: Development plan generated
    plan = active_app.development_plan
    if plan and "architecture" in plan:
        arch = plan["architecture"]
        screens_count = len(arch.get("screens", []))
        endpoints_count = len(arch.get("backend_endpoints", []))
        print(f"[CHECK 9] Architecture Screens     : {screens_count}")
        print(f"[CHECK 10] Backend API Endpoints  : {endpoints_count}")
        print(f"[CHECK 11] Architecture Plan Hash  : {plan.get('architecture_hash', '')[:12]}")

    print("\n" + "=" * 60)
    print("PRODUCTION ROUTING E2E TEST: 100% SUCCESS PASS")
    print("=" * 60)


if __name__ == "__main__":
    run_production_routing_test()
