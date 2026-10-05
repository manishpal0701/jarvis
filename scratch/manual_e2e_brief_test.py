import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from conversation.command_router import CommandRouter
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_model import AppState


def run_manual_e2e_brief_test():
    print("\n============================================================")
    print("STARTING MANUAL E2E APP BRIEF INTEGRITY VERIFICATION")
    print("============================================================\n")

    app_mgr = AppManager()
    app_mgr.reset()

    router = CommandRouter()

    # Step 1: Initial command "Jarvis, ek app bana do."
    print(">>> USER: 'Jarvis, ek app bana do.'")
    router.process_user_input("Jarvis, ek app bana do.", source="chat")

    active_app = app_mgr.get_active_app()
    assert active_app is not None, "Active app project was not created"
    assert active_app.status == AppState.WAITING_FOR_BRIEF, f"Unexpected status: {active_app.status}"
    print(f"[VERIFIED] Active App ID: {active_app.app_id}, Status: {active_app.status.value}\n")

    # Step 2: User sends complete multiline Spotify-style brief
    full_brief_input = (
        "Jarvis, ek complete Spotify-style Music Player Android app banao.\n\n"
        "App ka naam: JARVIS Music\n\n"
        "Purpose:\n"
        "Ek modern music streaming/player app jisme user different types ke music browse, search, play aur manage kar sake.\n\n"
        "Requirements:\n"
        "- Home Screen\n"
        "- Featured songs\n"
        "- Trending songs\n"
        "- Recently played\n"
        "- New releases\n"
        "- Popular artists\n"
        "- Popular albums\n"
        "- Mood-based sections\n"
        "- Playlists\n"
        "- Music categories\n"
        "- Search\n"
        "- Full music player\n"
        "- Mini player\n"
        "- Queue\n"
        "- Likes\n"
        "- Background playback\n"
        "- Demo music catalogue\n"
        "- Node.js + Express backend\n"
        "- Database persistence\n"
        "- Flutter Android frontend\n"
        "- Testing requirements"
    )

    print(">>> USER SENDS COMPLETE MULTILINE BRIEF:")
    print(full_brief_input)
    print("\n--- PROCESSING BRIEF CONTINUATION ---")

    router.process_user_input(full_brief_input, source="chat")
    app_mgr.start_app_development(active_app.app_id, sync_execution=True)

    updated_app = app_mgr.get_app_by_id(active_app.app_id)
    assert updated_app is not None, "Updated app project not found"

    print("\n--- VERIFYING BRIEF INTEGRITY RESULTS ---")
    print(f"App Name            : '{updated_app.name}'")
    print(f"Brief Name          : '{updated_app.brief.name}'")
    print(f"Full Text Length    : {len(updated_app.brief.full_text)}")
    print(f"Features Count      : {len(updated_app.brief.features)}")
    print(f"Development Plan    : {bool(updated_app.development_plan)}")
    
    plan_app_name = updated_app.development_plan.get("app_name") if updated_app.development_plan else None
    plan_domain = updated_app.development_plan.get("requirements", {}).get("domain") if updated_app.development_plan else None

    print(f"Plan App Name       : '{plan_app_name}'")
    print(f"Plan Domain         : '{plan_domain}'")

    # Strict Assertions
    assert updated_app.name == "JARVIS Music", f"FAILED: App name was '{updated_app.name}', expected 'JARVIS Music'"
    assert plan_app_name == "JARVIS Music", f"FAILED: Plan app name was '{plan_app_name}', expected 'JARVIS Music'"
    assert plan_domain == "music", f"FAILED: Plan domain was '{plan_domain}', expected 'music'"
    assert not updated_app.name.startswith("-"), f"FAILED: App name is a bullet point string: {updated_app.name}"
    assert "Artist name" not in updated_app.name, f"FAILED: 'Artist name' found in app name: {updated_app.name}"

    print("\n============================================================")
    print("MANUAL E2E APP BRIEF INTEGRITY TEST PASSED 100%!")
    print("============================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(run_manual_e2e_brief_test())
