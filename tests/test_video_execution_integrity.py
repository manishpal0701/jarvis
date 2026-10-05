"""
tests/test_video_execution_integrity.py
Regression & Integrity Test Suite for Phase 5 Jarvis Video Editing Pipeline.
Tests:
1. Scene analysis performance & caching verification in media_analyzer
2. Zero media files imported failure gate (MEDIA_IMPORT_FAILED)
3. Zero clips on V1 timeline failure gate (TIMELINE_BUILD_FAILED)
4. Project save (.prproj) verification & 13-point verification gate check 12 failure
5. Full E2E success path through handle_command(sync_execution=True) with 13/13 PASS
"""

import os
import shutil
import tempfile
import unittest
import numpy as np
from unittest.mock import MagicMock, patch

from video_editing.video_session_manager import VideoEditingSessionManager
from video_editing.analysis.media_analyzer import clear_media_cache, analyze_media
from video_editing.scene_understanding import analyze_scenes_and_content


class TestVideoExecutionIntegrity(unittest.TestCase):

    def setUp(self):
        self.session = VideoEditingSessionManager.get_instance()
        self.session.reset_session()
        clear_media_cache()

        self.temp_dir = tempfile.mkdtemp()
        self.source_folder = os.path.join(self.temp_dir, "test_videos")
        os.makedirs(self.source_folder, exist_ok=True)

        self.clip1 = os.path.join(self.source_folder, "test_clip1.mp4")
        self.clip2 = os.path.join(self.source_folder, "test_clip2.mp4")

        with open(self.clip1, "wb") as f:
            f.write(b"fake video clip data 1")
        with open(self.clip2, "wb") as f:
            f.write(b"fake video clip data 2")

        self.manifest = [
            {
                "file_path": self.clip1,
                "filename": "test_clip1.mp4",
                "extension": ".mp4",
                "duration": 5.0,
                "resolution": "1920x1080",
                "fps": 30.0,
                "codec": "h264",
                "file_size": 1024
            },
            {
                "file_path": self.clip2,
                "filename": "test_clip2.mp4",
                "extension": ".mp4",
                "duration": 5.0,
                "resolution": "1920x1080",
                "fps": 30.0,
                "codec": "h264",
                "file_size": 1024
            }
        ]

    def tearDown(self):
        self.session.reset_session()
        clear_media_cache()
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    # 1. Caching & Performance Test
    @patch("video_editing.analysis.media_analyzer.cv2.VideoCapture")
    def test_01_scene_analysis_caching(self, mock_cap_cls):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 300 if prop == 7 else (30.0 if prop == 5 else 0)
        mock_cap.grab.return_value = True
        mock_cap.retrieve.return_value = (True, None)
        mock_cap.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
        mock_cap_cls.return_value = mock_cap

        # First call to analyze_media
        res1 = analyze_media(self.clip1)
        calls_after_first = mock_cap_cls.call_count

        # Second call to analyze_media (must hit cache, 0 extra VideoCapture calls)
        res2 = analyze_media(self.clip1)
        self.assertEqual(res1, res2)
        self.assertEqual(mock_cap_cls.call_count, calls_after_first)

    # 2. Zero media files imported -> MEDIA_IMPORT_FAILED
    @patch("video_editing.video_session_manager.analyze_media")
    @patch("video_editing.video_session_manager.verify_output_file")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController")
    @patch("video_editing.software.premiere.PremiereProController")
    @patch("video_editing.scene_understanding.detect_scenes")
    @patch("video_editing.scene_understanding.analyze_media")
    def test_02_zero_media_imported_gate_failure(
        self, mock_su_analyze, mock_detect, mock_ctrl_cls, mock_win_ctrl, mock_verify, mock_sm_analyze
    ):
        meta = {"duration": 5.0, "fps": 30.0, "resolution": "1920x1080"}
        mock_su_analyze.return_value = meta
        mock_sm_analyze.return_value = meta
        mock_detect.return_value = [{"scene_id": "s1", "start": 0.0, "end": 5.0, "duration": 5.0}]

        ctrl_mock = MagicMock()
        ctrl_mock._connected = True
        ctrl_mock.get_project_info.return_value = {"ok": True, "hasProject": True, "hasActiveSequence": True}
        ctrl_mock.import_clip.return_value = {"ok": False, "error": "Import failed"}
        ctrl_mock.get_project_items.return_value = {"ok": True, "items": []}
        mock_ctrl_cls.return_value = ctrl_mock

        result = self.session.handle_command(f"cinematic edit '{self.source_folder}'", sync_execution=True)

        self.assertIn("FINAL_STATUS: FAILED", result)
        self.assertIn("MEDIA_IMPORT_FAILED", result)

    # 3. Zero clips on V1 timeline -> TIMELINE_BUILD_FAILED
    @patch("video_editing.video_session_manager.analyze_media")
    @patch("video_editing.video_session_manager.verify_output_file")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController")
    @patch("video_editing.software.premiere.PremiereProController")
    @patch("video_editing.scene_understanding.detect_scenes")
    @patch("video_editing.scene_understanding.analyze_media")
    def test_03_zero_timeline_clips_gate_failure(
        self, mock_su_analyze, mock_detect, mock_ctrl_cls, mock_win_ctrl, mock_verify, mock_sm_analyze
    ):
        meta = {"duration": 5.0, "fps": 30.0, "resolution": "1920x1080"}
        mock_su_analyze.return_value = meta
        mock_sm_analyze.return_value = meta
        mock_detect.return_value = [{"scene_id": "s1", "start": 0.0, "end": 5.0, "duration": 5.0}]

        ctrl_mock = MagicMock()
        ctrl_mock._connected = True
        ctrl_mock.get_project_info.return_value = {"ok": True, "hasProject": True, "hasActiveSequence": True}
        ctrl_mock.import_clip.return_value = {"ok": True}
        ctrl_mock.place_clip_on_timeline.return_value = {"ok": True}
        ctrl_mock.read_timeline_detailed.return_value = {"ok": True, "videoClipCount": 0}
        mock_ctrl_cls.return_value = ctrl_mock

        result = self.session.handle_command(f"cinematic edit '{self.source_folder}'", sync_execution=True)

        self.assertIn("FINAL_STATUS: FAILED", result)
        self.assertIn("TIMELINE_BUILD_FAILED", result)

    # 4. Project save failure -> Gate Check 14 FAILED -> FINAL_STATUS FAILED
    @patch("video_editing.video_session_manager.analyze_media")
    @patch("video_editing.video_session_manager.verify_output_file")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController")
    @patch("video_editing.software.premiere.PremiereProController")
    @patch("video_editing.scene_understanding.detect_scenes")
    @patch("video_editing.scene_understanding.analyze_media")
    def test_04_project_save_gate_failure(
        self, mock_su_analyze, mock_detect, mock_ctrl_cls, mock_win_ctrl, mock_verify, mock_sm_analyze
    ):
        meta = {"duration": 5.0, "fps": 30.0, "resolution": "1920x1080"}
        mock_su_analyze.return_value = meta
        mock_sm_analyze.return_value = meta
        mock_detect.return_value = [{"scene_id": "s1", "start": 0.0, "end": 5.0, "duration": 5.0}]

        ctrl_mock = MagicMock()
        ctrl_mock._connected = True
        ctrl_mock.get_project_info.return_value = {"ok": True, "hasProject": True, "hasActiveSequence": True}
        ctrl_mock.import_clip.return_value = {"ok": True}
        ctrl_mock.place_clip_on_timeline.return_value = {"ok": True}
        ctrl_mock.read_timeline_detailed.return_value = {"ok": True, "videoClipCount": 2}
        ctrl_mock.save_project.return_value = {"ok": False, "error": "Save failed"}
        mock_ctrl_cls.return_value = ctrl_mock

        mock_verify.return_value = {
            "success": True,
            "verified": True,
            "duration": 10.0,
            "file_size_bytes": 2048576,
            "video": {"resolution": "1080x1920"}
        }

        result = self.session.handle_command(f"cinematic edit '{self.source_folder}'", sync_execution=True)

        self.assertIn("FINAL_STATUS: FAILED", result)
        self.assertIn("[FAIL] 14. Project file saved (.prproj size > 0)", result)

    # 5. Full E2E Success Path -> All 13 Gate Checks PASS
    @patch("video_editing.video_session_manager.analyze_media")
    @patch("video_editing.video_session_manager.verify_output_file")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController")
    @patch("video_editing.software.premiere.PremiereProController")
    @patch("video_editing.scene_understanding.detect_scenes")
    @patch("video_editing.scene_understanding.analyze_media")
    def test_05_full_e2e_success_path(
        self, mock_su_analyze, mock_detect, mock_ctrl_cls, mock_win_ctrl, mock_verify, mock_sm_analyze
    ):
        meta = {"duration": 5.0, "fps": 30.0, "resolution": "1920x1080"}
        mock_su_analyze.return_value = meta
        mock_sm_analyze.return_value = meta
        mock_detect.return_value = [{"scene_id": "s1", "start": 0.0, "end": 5.0, "duration": 5.0}]

        prproj_dummy = os.path.join(self.temp_dir, "test_proj.prproj")
        with open(prproj_dummy, "wb") as f:
            f.write(b"dummy prproj binary data")

        ctrl_mock = MagicMock()
        ctrl_mock._connected = True
        ctrl_mock.get_project_info.return_value = {
            "ok": True,
            "hasProject": True,
            "hasActiveSequence": True,
            "activeSequenceName": "Jarvis_Live_Sequence",
            "projectPath": prproj_dummy
        }
        ctrl_mock.import_clip.return_value = {"ok": True}
        ctrl_mock.place_clip_on_timeline.return_value = {"ok": True}
        ctrl_mock.read_timeline_detailed.return_value = {"ok": True, "videoClipCount": 2}
        ctrl_mock.save_project.return_value = {"ok": True, "path": prproj_dummy}
        mock_ctrl_cls.return_value = ctrl_mock

        mock_verify.return_value = {
            "success": True,
            "verified": True,
            "duration": 10.0,
            "file_size_bytes": 2048576,
            "video": {"resolution": "1080x1920"}
        }

        result = self.session.handle_command(f"cinematic edit '{self.source_folder}'", sync_execution=True)

        self.assertIn("FINAL_STATUS: SUCCESS", result)
        self.assertIn("[PASS] 1. Valid source folder", result)
        self.assertIn("[PASS] 11. Media files imported to project panel", result)
        self.assertIn("[PASS] 13. Clips placed on V1 timeline", result)
        self.assertIn("[PASS] 14. Project file saved (.prproj size > 0)", result)
        self.assertIn("[PASS] 15. Pipeline status = SUCCESS", result)


if __name__ == "__main__":
    unittest.main()
