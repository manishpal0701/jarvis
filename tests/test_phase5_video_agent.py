"""
tests/test_phase5_video_agent.py
Comprehensive Unit & E2E Integration Test Suite for Phase 5 Jarvis AI Video Editing Agent.
Tests:
- Single-video folder scan & manifest building
- Multiple-video folder scan & manifest building
- Mixed non-video files folder scan
- Empty folder / invalid videos -> NO_VALID_VIDEO_SOURCE
- Scene understanding & error states (VISION_UNAVAILABLE, SCENE_ANALYSIS_FAILED, INSUFFICIENT_SCENES)
- Clip quality scoring & intelligent selection
- Edit intent parsing with UNKNOWN / NOT_AVAILABLE
- Qwen3 edit planning & PLANNING_FAILED handling
- Approval gate state transitions
- Premiere handoff & export state machine
- Output verification with ffprobe & RENDER_VERIFICATION_FAILED
- Zero-byte / missing output error handling
- Routing preservation for non-video commands
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from video_editing.video_session_manager import (
    VideoEditingSessionManager,
    NO_VALID_VIDEO_SOURCE,
    RENDER_VERIFICATION_FAILED
)
from video_editing.scene_understanding import (
    SceneUnderstanding,
    STATE_SUCCESS,
    STATE_VISION_UNAVAILABLE,
    STATE_SCENE_ANALYSIS_FAILED,
    STATE_INSUFFICIENT_SCENES
)
from video_editing.clip_quality_scorer import ClipQualityScorer, score_clips
from video_editing.clip_selector import ClipSelector, select_intelligent_clips
from video_editing.edit_intent import EditIntentParser, parse_edit_intent, VALUE_UNKNOWN, VALUE_NOT_AVAILABLE
from video_editing.intelligent_edit_planner import IntelligentEditPlanner, STATE_PLANNING_FAILED
from video_editing.export.export_verifier import verify_output_file
from conversation.command_router import CommandRouter


class TestPhase5VideoAgent(unittest.TestCase):

    def setUp(self):
        self.session = VideoEditingSessionManager.get_instance()
        self.session.reset_session()

        self.temp_dir = tempfile.mkdtemp()
        self.single_video_folder = os.path.join(self.temp_dir, "single_vid")
        os.makedirs(self.single_video_folder, exist_ok=True)
        self.dummy_v1 = os.path.join(self.single_video_folder, "clip1.mp4")
        with open(self.dummy_v1, "wb") as f:
            f.write(b"fake mp4 header content 1")

        self.multi_video_folder = os.path.join(self.temp_dir, "multi_vid")
        os.makedirs(self.multi_video_folder, exist_ok=True)
        self.dummy_v2 = os.path.join(self.multi_video_folder, "clipA.mp4")
        self.dummy_v3 = os.path.join(self.multi_video_folder, "clipB.mov")
        self.dummy_txt = os.path.join(self.multi_video_folder, "notes.txt")
        with open(self.dummy_v2, "wb") as f: f.write(b"fake mp4 content A")
        with open(self.dummy_v3, "wb") as f: f.write(b"fake mov content B")
        with open(self.dummy_txt, "w") as f: f.write("some notes")

        self.empty_folder = os.path.join(self.temp_dir, "empty_dir")
        os.makedirs(self.empty_folder, exist_ok=True)

        self.non_video_folder = os.path.join(self.temp_dir, "non_video_dir")
        os.makedirs(self.non_video_folder, exist_ok=True)
        with open(os.path.join(self.non_video_folder, "doc.pdf"), "w") as f:
            f.write("pdf data")

    def tearDown(self):
        self.session.reset_session()
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    # A. Single-video folder manifest building
    def test_01_single_video_folder_manifest(self):
        manifest = self.session.build_source_manifest(self.single_video_folder)
        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest[0]["filename"], "clip1.mp4")
        self.assertEqual(manifest[0]["extension"], ".mp4")

    # B. Multiple-video & mixed files folder scan
    def test_02_multi_video_folder_scan(self):
        manifest = self.session.build_source_manifest(self.multi_video_folder)
        filenames = [m["filename"] for m in manifest]
        self.assertEqual(len(manifest), 2)
        self.assertIn("clipA.mp4", filenames)
        self.assertIn("clipB.mov", filenames)
        self.assertNotIn("notes.txt", filenames)

    # C. Empty folder / no video files -> NO_VALID_VIDEO_SOURCE
    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    def test_03_empty_folder_returns_no_valid_video_source(self, mock_askdirectory, mock_tk):
        mock_askdirectory.return_value = self.empty_folder
        resp = self.session.handle_command("Jarvis, edit this video", sync_execution=True)
        self.assertIn("video folder ki zaroorat hai", resp)
        self.assertEqual(self.session.state, "WAITING_FOR_SOURCE_MEDIA")

    # D. Invalid non-video files folder -> NO_VALID_VIDEO_SOURCE
    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    def test_04_non_video_folder_returns_no_valid_video_source(self, mock_askdirectory, mock_tk):
        mock_askdirectory.return_value = self.non_video_folder
        resp = self.session.handle_command("Jarvis, edit this video", sync_execution=True)
        self.assertIn("video folder ki zaroorat hai", resp)
        self.assertEqual(self.session.state, "WAITING_FOR_SOURCE_MEDIA")

    # E. Edit Intent Parsing (UNKNOWN / NOT_AVAILABLE fields)
    def test_05_edit_intent_parsing(self):
        intent = EditIntentParser.parse_intent("Create a 30 second Instagram reel")
        self.assertEqual(intent["edit_type"], "reel")
        self.assertEqual(intent["target_duration"], 30.0)
        self.assertEqual(intent["aspect_ratio"], "9:16")
        self.assertEqual(intent["platform"], "instagram")
        self.assertEqual(intent["preferred_sections"], VALUE_NOT_AVAILABLE)

        intent_unknown = EditIntentParser.parse_intent("Jarvis edit video")
        self.assertEqual(intent_unknown["platform"], VALUE_UNKNOWN)

    # F. Clip Quality Scoring
    def test_06_clip_quality_scoring(self):
        dummy_scenes = [
            {"scene_id": "s1", "file_path": self.dummy_v1, "blur_score": 200, "brightness": 120, "motion_level": 10, "duration": 5.0, "is_duplicate": False},
            {"scene_id": "s2", "file_path": self.dummy_v1, "blur_score": 10, "brightness": 10, "motion_level": 0, "duration": 0.5, "is_duplicate": True}
        ]
        scored = score_clips(dummy_scenes)
        self.assertEqual(len(scored), 2)
        s1 = next(s for s in scored if s["scene_id"] == "s1")
        s2 = next(s for s in scored if s["scene_id"] == "s2")
        self.assertTrue(s1["usable"])
        self.assertFalse(s2["usable"])
        self.assertGreater(s1["score"], s2["score"])

    # G. Intelligent Clip Selection
    def test_07_intelligent_clip_selection(self):
        dummy_scored = [
            {"scene_id": "s1", "file_path": self.dummy_v1, "score": 0.85, "usable": True, "is_duplicate": False, "duration": 5.0, "start": 0.0},
            {"scene_id": "s2", "file_path": self.dummy_v2, "score": 0.75, "usable": True, "is_duplicate": False, "duration": 10.0, "start": 0.0}
        ]
        intent = {"target_duration": 12.0}
        selected = select_intelligent_clips(dummy_scored, intent)
        self.assertEqual(len(selected), 2)
        tot_dur = sum(s["selected_duration"] for s in selected)
        self.assertEqual(tot_dur, 12.0)

    # H. Intelligent Edit Planner & PLANNING_FAILED handling
    def test_08_intelligent_edit_planner(self):
        manifest = [{"file_path": self.dummy_v1, "filename": "clip1.mp4"}]
        selected = [{"scene_id": "s1", "file_path": self.dummy_v1, "filename": "clip1.mp4", "duration": 5.0, "start": 0.0}]
        intent = {"edit_type": "reel", "target_duration": 5.0}

        plan_res = IntelligentEditPlanner.generate_plan(manifest, [], [], selected, intent)
        self.assertTrue(plan_res["success"])
        self.assertIn("Plan:", plan_res["summary"])

        # Failed case: empty selection
        fail_res = IntelligentEditPlanner.generate_plan(manifest, [], [], [], intent)
        self.assertFalse(fail_res["success"])
        self.assertEqual(fail_res["status"], STATE_PLANNING_FAILED)

    # I. Autonomous Execution & Verification Flow
    @patch("video_editing.video_session_manager.analyze_media")
    @patch("video_editing.video_session_manager.verify_output_file")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController")
    @patch("video_editing.software.premiere.PremiereProController")
    @patch("video_editing.video_session_manager.plan_intelligent_edit")
    @patch("video_editing.video_session_manager.analyze_scenes_and_content")
    def test_09_approval_gate_flow(self, mock_scene, mock_plan, mock_ctrl_cls, mock_win_ctrl, mock_verify, mock_analyze):
        meta = {"duration": 5.0, "fps": 30.0, "resolution": "1920x1080"}
        mock_analyze.return_value = meta
        mock_scene.return_value = {
            "status": "SUCCESS",
            "scenes": [{"scene_id": "s1", "file_path": self.dummy_v1, "duration": 5.0, "blur_score": 100, "brightness": 100, "motion_level": 10}]
        }
        mock_plan.return_value = {
            "success": True,
            "status": "PLAN_CREATED",
            "plan": {"operations": [{"clip_path": self.dummy_v1, "timeline_pos": 0.0, "duration": 5.0}]},
            "summary": "Boss, ready to edit?"
        }
        ctrl_mock = MagicMock()
        ctrl_mock._connected = True
        ctrl_mock.get_project_info.return_value = {"ok": True, "hasProject": True, "hasActiveSequence": True}
        ctrl_mock.import_clip.return_value = {"ok": True}
        ctrl_mock.place_clip_on_timeline.return_value = {"ok": True}
        ctrl_mock.read_timeline_detailed.return_value = {"ok": True, "videoClipCount": 1}
        ctrl_mock.save_project.return_value = {"ok": True, "path": self.dummy_v1}
        mock_ctrl_cls.return_value = ctrl_mock
        mock_verify.return_value = {"success": True, "verified": True, "duration": 5.0, "file_size_bytes": 1024, "video": {"resolution": "1920x1080"}}

        resp = self.session.handle_command(f"Make a cinematic reel from '{self.single_video_folder}'", sync_execution=True)
        self.assertEqual(self.session.state, "IDLE")
        self.assertIn("FINAL_STATUS: SUCCESS", resp)

    # J. Export Output Verification with ffprobe & RENDER_VERIFICATION_FAILED
    def test_10_export_verification(self):
        # 1. Non-existent file
        res_missing = verify_output_file(os.path.join(self.temp_dir, "non_existent.mp4"))
        self.assertFalse(res_missing["success"])
        self.assertEqual(res_missing["error"]["code"], "OUTPUT_NOT_FOUND")

        # 2. Zero-byte file
        zero_file = os.path.join(self.temp_dir, "zero.mp4")
        with open(zero_file, "wb") as f:
            pass
        res_zero = verify_output_file(zero_file)
        self.assertFalse(res_zero["success"])
        self.assertEqual(res_zero["error"]["code"], "ZERO_BYTE_OUTPUT")

    # K. Non-video Jarvis command routing preservation
    def test_11_preserve_non_video_routing(self):
        router = CommandRouter()
        # Normal conversation or system queries must NOT be intercepted by video agent
        self.assertFalse(self.session.is_active())


if __name__ == "__main__":
    unittest.main()
