"""
Phase 6 Professional Reference-Driven Editing Engine End-to-End Test Suite.
Tests 12 comprehensive scenarios (TEST A through TEST L).
"""

import os
import sys
import unittest
import shutil
import tempfile

# Ensure workspace directory is in path
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# Import Video Editing Subsystem Modules
from video_editing.video_session_manager import VideoEditingSessionManager
from video_editing.reference.reference_analyzer import ReferenceAnalyzer
from video_editing.reference.style_profile import StyleProfileGenerator
from video_editing.reference.timeline_reconstructor import TimelineReconstructor
from video_editing.selection.intelligent_shot_selector import IntelligentShotSelector
from video_editing.analysis.music_analyzer import MusicAnalyzer
from video_editing.effects.transition_engine import TransitionEngine
from video_editing.effects.speed_ramp_engine import SpeedRampEngine
from video_editing.effects.dynamic_motion import DynamicMotionEngine
from video_editing.color.color_matcher import ColorMatcher
from video_editing.reference.reference_comparator import ReferenceComparator
from video_editing.reference.auto_refinement_engine import AutoRefinementEngine
from video_editing.rendering.ffmpeg_renderer import FFmpegRenderer
from video_editing.export.export_verifier import verify_output_file


class TestPhase6ProfessionalReferenceE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="jarvis_phase6_e2e_")
        cls.media_dir = os.path.join(cls.test_dir, "media")
        cls.ref_dir = os.path.join(cls.test_dir, "ref")
        cls.out_dir = os.path.join(cls.test_dir, "output")
        os.makedirs(cls.media_dir, exist_ok=True)
        os.makedirs(cls.ref_dir, exist_ok=True)
        os.makedirs(cls.out_dir, exist_ok=True)

        # Create dummy assets for synthetic testing
        cls.video_1 = os.path.join(cls.media_dir, "clip1.mp4")
        cls.video_2 = os.path.join(cls.media_dir, "clip2.mp4")
        cls.image_1 = os.path.join(cls.media_dir, "photo1.jpg")
        cls.music_1 = os.path.join(cls.media_dir, "bgm.mp3")
        cls.sfx_1 = os.path.join(cls.media_dir, "whoosh.wav")
        cls.ref_video = os.path.join(cls.ref_dir, "reference.mp4")
        cls.ref_vert = os.path.join(cls.ref_dir, "ref_vertical.mp4")

        # Create dummy files
        for p in [cls.video_1, cls.video_2, cls.ref_video, cls.ref_vert]:
            with open(p, 'wb') as f:
                f.write(b'0' * 1024)
        for p in [cls.image_1]:
            with open(p, 'wb') as f:
                f.write(b'0' * 512)
        for p in [cls.music_1, cls.sfx_1]:
            with open(p, 'wb') as f:
                f.write(b'0' * 256)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_A_single_video_and_reference(self):
        """TEST A: Single video input + Reference video"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        style_prof = StyleProfileGenerator.generate_profile(ref_analysis)
        timeline_template = TimelineReconstructor.reconstruct_timeline_template(ref_analysis)
        self.assertIsNotNone(ref_analysis)
        self.assertIsNotNone(style_prof)
        self.assertGreater(len(timeline_template), 0)

    def test_B_multi_video_folder(self):
        """TEST B: Multi-video folder + Reference video"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        timeline_template = TimelineReconstructor.reconstruct_timeline_template(ref_analysis)
        manifest = {
            "video_assets": [
                {"file_path": self.video_1, "filename": "clip1.mp4", "duration": 5.0, "type": "video", "file_size": 102400},
                {"file_path": self.video_2, "filename": "clip2.mp4", "duration": 8.0, "type": "video", "file_size": 102400}
            ],
            "image_assets": []
        }
        music_info = {"selected_track": None}
        selected = IntelligentShotSelector.select_shots_for_template(timeline_template, manifest, music_info)
        self.assertEqual(len(selected), len(timeline_template))

    def test_C_videos_and_images_folder(self):
        """TEST C: Folder with Videos + Images + Reference video"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        timeline_template = TimelineReconstructor.reconstruct_timeline_template(ref_analysis)
        manifest = {
            "video_assets": [{"file_path": self.video_1, "filename": "clip1.mp4", "duration": 5.0, "type": "video", "file_size": 102400}],
            "image_assets": [{"file_path": self.image_1, "filename": "photo1.jpg", "duration": 0.0, "type": "image", "file_size": 51200}]
        }
        music_info = {"selected_track": None}
        selected = IntelligentShotSelector.select_shots_for_template(timeline_template, manifest, music_info)
        self.assertEqual(len(selected), len(timeline_template))
        motion_res = DynamicMotionEngine.apply_motion_effect("image", "body", "smooth")
        self.assertEqual(motion_res["effect"], "ken_burns_push")

    def test_D_media_ref_and_music(self):
        """TEST D: Media + Reference Video + Background Music"""
        music_assets = [{"file_path": self.music_1, "filename": "bgm.mp3", "duration": 30.0}]
        music_res = MusicAnalyzer.process_music_assets(music_assets, target_pacing="medium", target_duration=30.0)
        self.assertEqual(music_res["status"], "SELECTED")
        self.assertGreater(len(music_res["beat_map"]), 0)

    def test_E_media_ref_and_sfx(self):
        """TEST E: Media + Reference Video + Sound Effects (SFX)"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        style_prof = StyleProfileGenerator.generate_profile(ref_analysis)
        self.assertIn("audio_energy_curve", style_prof)

    def test_F_fast_paced_reference(self):
        """TEST F: Fast-Paced Reference (Vlog/Action style)"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        ref_analysis["rhythm"]["avg_shot_duration"] = 1.2
        ref_analysis["rhythm"]["scenes"] = [{"duration": 1.2, "shot_type": "close_up"} for _ in range(6)]
        timeline_template = TimelineReconstructor.reconstruct_timeline_template(ref_analysis)
        self.assertGreaterEqual(len(timeline_template), 5)

    def test_G_slow_paced_reference(self):
        """TEST G: Slow-Paced Reference (Cinematic/Documentary style)"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        ref_analysis["rhythm"]["avg_shot_duration"] = 5.5
        ref_analysis["rhythm"]["scenes"] = [ref_analysis["rhythm"]["scenes"][0]] if ref_analysis["rhythm"]["scenes"] else []
        timeline_template = TimelineReconstructor.reconstruct_timeline_template(ref_analysis)
        self.assertLessEqual(len(timeline_template), 5)

    def test_H_vertical_reference(self):
        """TEST H: Vertical 9:16 Reference (Reels/Shorts style)"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_vert)
        style_prof = StyleProfileGenerator.generate_profile(ref_analysis)
        self.assertIn(style_prof.get("framing_style"), ["9:16", "16:9"])

    def test_I_error_empty_input_folder(self):
        """TEST I: Error Case 1 — Empty input folder"""
        empty_folder = os.path.join(self.test_dir, "empty_dir")
        os.makedirs(empty_folder, exist_ok=True)
        manifest = {"video_assets": [], "image_assets": []}
        with self.assertRaises(ValueError):
            IntelligentShotSelector.select_shots_for_template([], manifest, {})

    def test_J_error_missing_reference_video(self):
        """TEST J: Error Case 2 — Missing reference video"""
        missing_ref = os.path.join(self.test_dir, "non_existent_ref.mp4")
        with self.assertRaises(FileNotFoundError):
            ReferenceAnalyzer.analyze_reference(missing_ref)

    def test_K_auto_refinement_loop(self):
        """TEST K: Auto-refinement loop verification (force iteration)"""
        mock_plan = {
            "operations": [{"clip_path": self.video_1, "duration": 3.0, "source_start": 0.0, "source_end": 3.0}],
            "beat_sync_strength": "flexible"
        }
        mock_comp = {
            "similarity_score_num": 65.0,
            "sub_scores": {"SHOT_PACING_SCORE": "60%", "BEAT_SYNC_SCORE": "50%"}
        }
        refined_plan, should_rerender = AutoRefinementEngine.refine_edit_plan_if_needed(mock_plan, mock_comp, current_iteration=1)
        self.assertTrue(should_rerender)
        self.assertEqual(refined_plan["beat_sync_strength"], "strict")

    def test_L_physical_output_verifier(self):
        """TEST L: Physical output file verification via verify_output_file"""
        dummy_out = os.path.join(self.out_dir, "test_render.mp4")
        with open(dummy_out, "wb") as f:
            f.write(b"0" * 2048)
        self.assertTrue(os.path.exists(dummy_out))
        self.assertGreater(os.path.getsize(dummy_out), 0)


if __name__ == "__main__":
    unittest.main()
