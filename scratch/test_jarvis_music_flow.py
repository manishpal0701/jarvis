"""
scratch/test_jarvis_music_flow.py
Validates the complete workflow for "Jarvis, ek Spotify-style Music Player Android app banao".
"""
import os
import shutil
import tempfile
import json

from tools.app_builder.app_model import AppProject, AppBrief, AppBuildSpec, AppState
from tools.app_builder.app_requirements_analyzer import AppRequirementsAnalyzer
from tools.app_builder.architecture_planner import ArchitecturePlanner
from tools.app_builder.app_workspace_manager import AppWorkspaceManager
from tools.app_builder.node_generator import NodeProjectGenerator
from tools.app_builder.flutter_generator import FlutterProjectGenerator
from tools.app_builder.app_coding_agent import AppCodingAgent
from tools.app_builder.ide_interfaces import ConcreteFlutterAndroidStudioRunner, ConcreteNodeVSCodeRunner

def test_music_player_e2e():
    print("\n============================================================")
    print("TESTING E2E WORKFLOW: JARVIS MUSIC (FLUTTER + NODE.JS)")
    print("============================================================")

    # 1. Brief & Requirements Analysis
    brief_text = "Jarvis, ek Spotify-style Music Player Android app banao with login, home screen, search, playlists, liked songs, recently played, queue, shuffle, repeat, categories, album pages, artist pages, persistent playback state and a Node.js backend."
    brief = AppBrief(description=brief_text)
    brief.name = "JARVIS Music"
    brief.technology = {"frontend": "Flutter", "backend": "Node.js"}

    analyzed = AppRequirementsAnalyzer.analyze(brief)

    assert analyzed["app_name"] == "JARVIS Music", f"Expected JARVIS Music, got {analyzed['app_name']}"
    assert analyzed["domain"] == "music", f"Expected domain music, got {analyzed['domain']}"
    assert analyzed["needs_backend"] is True, "Expected needs_backend=True"
    print("[OK] Step 1: Requirements Analysis & Domain Detection PASSED (domain=music)")

    # 2. Immutable AppBuildSpec
    spec = AppBuildSpec.from_dict(analyzed["build_spec"])
    assert spec.app_name == "JARVIS Music"
    assert spec.domain == "music"
    assert spec.frontend_stack == "Flutter"
    assert spec.backend_stack == "Node.js + Express"
    assert spec.is_locked is True
    print("[OK] Step 2: Locked AppBuildSpec Validation PASSED")

    # 3. Architecture Plan Generation
    app_id = "test_music_12345"
    arch_plan = ArchitecturePlanner.create_architecture_plan(app_id, analyzed)
    assert arch_plan["app_metadata"]["domain"] == "music"
    assert len(arch_plan["screens"]) >= 6
    print(f"[OK] Step 3: Architecture Plan Created ({len(arch_plan['screens'])} screens planned)")

    # 4. Workspace Creation
    test_root = tempfile.mkdtemp(prefix="jarvis_music_test_")
    try:
        ws_mgr = AppWorkspaceManager(workspace_root=test_root)
        app_project = AppProject(project_id=app_id, name="JARVIS Music", brief=brief, build_spec=spec)
        ws_info = ws_mgr.create_workspace(app_project, arch_plan)

        ws_dir = ws_info["workspace_path"]
        fe_dir = ws_info["frontend_path"]
        be_dir = ws_info["backend_path"]

        assert os.path.exists(os.path.join(ws_dir, "app_build_spec.json"))
        assert os.path.exists(os.path.join(ws_dir, "architecture_plan.json"))
        assert os.path.exists(os.path.join(ws_dir, "brief.json"))
        print("[OK] Step 4: Workspace Created & Metadata Persisted in Internal Workspace")

        # 5. Project Identity Validation
        agent = AppCodingAgent()
        valid_id = agent.validate_project_identity(ws_dir, app_id, arch_plan)
        assert valid_id is True, "Expected project identity validation to PASS"
        print("[OK] Step 5: Project Identity Validation PASSED")

        # 6. Real Node.js Backend Generation
        be_files = NodeProjectGenerator.generate_backend(be_dir, arch_plan)
        assert len(be_files) > 0
        assert os.path.exists(os.path.join(be_dir, "package.json"))
        assert os.path.exists(os.path.join(be_dir, "src", "server.js"))
        assert os.path.exists(os.path.join(be_dir, "src", "routes", "songRoutes.js"))
        assert os.path.exists(os.path.join(be_dir, "src", "services", "storeService.js"))
        print(f"[OK] Step 6: Real Node.js Backend Generated ({len(be_files)} files in backend/)")

        # 7. Real Flutter Frontend Generation
        fe_files = FlutterProjectGenerator.generate_frontend(fe_dir, arch_plan)
        assert len(fe_files) > 0
        assert os.path.exists(os.path.join(fe_dir, "pubspec.yaml"))
        assert os.path.exists(os.path.join(fe_dir, "android", "app", "src", "main", "AndroidManifest.xml"))
        assert os.path.exists(os.path.join(fe_dir, "lib", "main.dart"))
        assert os.path.exists(os.path.join(fe_dir, "lib", "services", "api_service.dart"))
        assert os.path.exists(os.path.join(fe_dir, "lib", "screens", "dashboard_screen.dart"))
        print(f"[OK] Step 7: Real Flutter Frontend Generated ({len(fe_files)} files in frontend/)")

        # 8. IDE Launch Target Path Verification
        flutter_runner = ConcreteFlutterAndroidStudioRunner()
        node_runner = ConcreteNodeVSCodeRunner()

        # Test IDE path targets (frontend/ for Android Studio, backend/ for VS Code)
        # Note: If studio64.exe or code.cmd isn't in PATH, runners gracefully fail with clear error
        as_target = fe_dir
        if not os.path.exists(os.path.join(as_target, "pubspec.yaml")) and os.path.exists(os.path.join(ws_dir, "frontend", "pubspec.yaml")):
            as_target = os.path.join(ws_dir, "frontend")

        vsc_target = be_dir
        if not os.path.exists(os.path.join(vsc_target, "package.json")) and os.path.exists(os.path.join(ws_dir, "backend", "package.json")):
            vsc_target = os.path.join(ws_dir, "backend")

        assert os.path.exists(os.path.join(as_target, "pubspec.yaml")), "Android Studio target must be physical Flutter project frontend/"
        assert os.path.exists(os.path.join(vsc_target, "package.json")), "VS Code target must be physical Node backend/"
        print("[OK] Step 8: IDE Target Path Verification PASSED (frontend/ for Android Studio, backend/ for VS Code)")

        print("\n============================================================")
        print("ALL E2E WORKFLOW CHECKS PASSED CLEANLY FOR JARVIS MUSIC!")
        print("============================================================\n")

    finally:
        shutil.rmtree(test_root, ignore_errors=True)

if __name__ == "__main__":
    test_music_player_e2e()
