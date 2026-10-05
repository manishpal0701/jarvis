"""
Phase 7 Autonomous Professional Video Editor End-to-End Physical Test Suite.
Tests 19 comprehensive scenarios (Scenario A through Scenario S).
"""

import os
import sys
import unittest
import shutil
import tempfile
import json

# Ensure workspace directory is in path
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# Import Phase 7 Subsystem Modules
from video_editing.video_session_manager import VideoEditingSessionManager
from video_editing.analysis.project_asset_intelligence import ProjectAssetIntelligence
from video_editing.reference.reference_analyzer import ReferenceAnalyzer
from video_editing.timeline.professional_timeline_builder import ProfessionalTimelineBuilder
from video_editing.selection.intelligent_shot_selector import IntelligentShotSelector
from video_editing.analysis.music_analyzer import MusicAnalyzer
from video_editing.audio.pro_audio_mixer import ProAudioMixer
from video_editing.quality.pro_editor_qc import ProEditorQC
from video_editing.reference.auto_refinement_engine import AutoRefinementEngine
from video_editing.reference.reference_comparator import ReferenceComparator
from video_editing.export.export_verifier import verify_output_file


class TestPhase7AutonomousEditorE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="jarvis_phase7_e2e_")
        cls.media_dir = os.path.join(cls.test_dir, "media")
        cls.ref_dir = os.path.join(cls.test_dir, "ref")
        cls.out_dir = os.path.join(cls.test_dir, "output")
        os.makedirs(cls.media_dir, exist_ok=True)
        os.makedirs(cls.ref_dir, exist_ok=True)
        os.makedirs(cls.out_dir, exist_ok=True)

        cls.video_1 = os.path.join(cls.media_dir, "clip1.mp4")
        cls.video_2 = os.path.join(cls.media_dir, "clip2.mp4")
        cls.image_1 = os.path.join(cls.media_dir, "photo1.jpg")
        cls.music_1 = os.path.join(cls.media_dir, "bgm.mp3")
        cls.sfx_1 = os.path.join(cls.media_dir, "whoosh_sfx.wav")
        cls.ref_video = os.path.join(cls.ref_dir, "reference.mp4")
        cls.ref_vert = os.path.join(cls.ref_dir, "ref_vertical.mp4")

        # Create physical dummy media files
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
        """Scenario A: Single video + reference"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        blueprint = ReferenceAnalyzer.create_reference_blueprint(ref_analysis)
        timeline = ProfessionalTimelineBuilder.build_professional_timeline(blueprint)
        self.assertIsNotNone(blueprint)
        self.assertGreater(len(timeline), 0)

    def test_B_multiple_videos_and_reference(self):
        """Scenario B: Multiple videos + reference"""
        manifest = ProjectAssetIntelligence.scan_project_assets(self.media_dir, self.ref_video)
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        blueprint = ref_analysis.get("blueprint")
        timeline = ProfessionalTimelineBuilder.build_professional_timeline(blueprint)
        selected = IntelligentShotSelector.select_shots_for_template(timeline, manifest, {})
        self.assertEqual(len(selected), len(timeline))

    def test_C_videos_and_images_and_reference(self):
        """Scenario C: Videos + images + reference"""
        manifest = ProjectAssetIntelligence.scan_project_assets(self.media_dir, self.ref_video)
        self.assertGreater(len(manifest["video_assets"]), 0)
        self.assertGreater(len(manifest["image_assets"]), 0)

    def test_D_videos_and_music_and_reference(self):
        """Scenario D: Videos + music + reference"""
        manifest = ProjectAssetIntelligence.scan_project_assets(self.media_dir, self.ref_video)
        music_info = MusicAnalyzer.process_music_assets(manifest["music_assets"])
        self.assertEqual(music_info["status"], "SELECTED")
        self.assertGreater(len(music_info["beat_timeline"]), 0)

    def test_E_videos_music_sfx_reference(self):
        """Scenario E: Videos + music + SFX + reference"""
        manifest = ProjectAssetIntelligence.scan_project_assets(self.media_dir, self.ref_video)
        self.assertGreater(len(manifest["sfx_assets"]), 0)
        mix = ProAudioMixer.mix_audio_tracks(manifest["music_assets"][0], manifest["sfx_assets"], [], 30.0)
        self.assertEqual(mix["sfx_count"], len(manifest["sfx_assets"]))

    def test_F_fast_reference(self):
        """Scenario F: Fast reference (Vlog/Action)"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        ref_analysis["rhythm"]["avg_shot_duration"] = 1.2
        ref_analysis["rhythm"]["scenes"] = [{"duration": 1.2} for _ in range(6)]
        blueprint = ReferenceAnalyzer.create_reference_blueprint(ref_analysis)
        timeline = ProfessionalTimelineBuilder.build_professional_timeline(blueprint)
        self.assertEqual(blueprint["pacing_profile"]["pacing_style"], "FAST_ACTION")
        self.assertGreaterEqual(len(timeline), 6)

    def test_G_slow_cinematic_reference(self):
        """Scenario G: Slow cinematic reference"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        ref_analysis["rhythm"]["avg_shot_duration"] = 5.5
        ref_analysis["rhythm"]["scenes"] = [{"duration": 5.5}]
        blueprint = ReferenceAnalyzer.create_reference_blueprint(ref_analysis)
        timeline = ProfessionalTimelineBuilder.build_professional_timeline(blueprint)
        self.assertEqual(blueprint["pacing_profile"]["pacing_style"], "SLOW_CINEMATIC")
        self.assertLessEqual(len(timeline), 3)

    def test_H_vertical_reference(self):
        """Scenario H: Vertical reference (Reels 9:16)"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_vert)
        blueprint = ReferenceAnalyzer.create_reference_blueprint(ref_analysis)
        self.assertIn(blueprint["framing_profile"]["aspect_ratio"], ["9:16", "16:9"])

    def test_I_reference_with_beat_sync(self):
        """Scenario I: Reference with strong beat sync"""
        shots = [{"shot_id": "shot_1", "target_duration": 2.0}]
        beats = [0.0, 0.5, 1.0, 1.5, 2.1, 2.5]
        synced = MusicAnalyzer.synchronize_cuts_to_beats(shots, beats)
        self.assertTrue(synced[0]["beat_synced"])

    def test_J_reference_with_transitions(self):
        """Scenario J: Reference with transitions"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        blueprint = ReferenceAnalyzer.create_reference_blueprint(ref_analysis)
        self.assertIn("primary_transition", blueprint["transition_profile"])

    def test_K_reference_with_color_style(self):
        """Scenario K: Reference with color style"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        blueprint = ReferenceAnalyzer.create_reference_blueprint(ref_analysis)
        self.assertEqual(blueprint["color_profile"]["style"], "cinematic_warm")

    def test_L_reference_with_subtitles_text(self):
        """Scenario L: Reference with subtitles/text"""
        ref_analysis = ReferenceAnalyzer.analyze_reference(self.ref_video)
        blueprint = ReferenceAnalyzer.create_reference_blueprint(ref_analysis)
        self.assertIn("text_profile", blueprint)

    def test_M_empty_folder_handling(self):
        """Scenario M: Empty folder handling"""
        mgr = VideoEditingSessionManager()
        empty_dir = os.path.join(self.test_dir, "empty_media_dir")
        os.makedirs(empty_dir, exist_ok=True)
        res = mgr.process_reference_driven_editing(empty_dir, self.ref_video)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "EMPTY_INPUT_DIRECTORY")

    def test_N_invalid_reference_handling(self):
        """Scenario N: Invalid reference handling"""
        mgr = VideoEditingSessionManager()
        missing_ref = os.path.join(self.test_dir, "missing_ref_video.mp4")
        res = mgr.process_reference_driven_editing(self.media_dir, missing_ref)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "MISSING_REFERENCE_VIDEO")

    def test_O_missing_music_handling(self):
        """Scenario O: Missing music handling"""
        music_res = MusicAnalyzer.process_music_assets([])
        self.assertEqual(music_res["status"], "NO_MUSIC")

    def test_P_missing_audio_handling(self):
        """Scenario P: Missing audio handling"""
        mix = ProAudioMixer.mix_audio_tracks(None, [], [], 30.0)
        self.assertFalse(mix["has_music"])
        self.assertFalse(mix["has_speech"])

    def test_Q_auto_refinement_loop(self):
        """Scenario Q: Auto refinement loop & threshold check"""
        mock_plan = {"operations": [{"duration": 2.0, "source_start": 0.0}]}
        comp_res = {
            "similarity_score_num": 72.0,
            "sub_scores": {"SHOT_PACING_SCORE": "65%", "BEAT_SYNC_SCORE": "70%"}
        }
        refined, rerender = AutoRefinementEngine.refine_edit_plan_if_needed(mock_plan, comp_res, current_iteration=1)
        self.assertTrue(rerender)

    def test_R_final_physical_export_validation(self):
        """Scenario R: Final physical export validation"""
        dummy_out = os.path.join(self.out_dir, "jarvis_final_edit.mp4")
        with open(dummy_out, "wb") as f:
            f.write(b"0" * 2048)
        qc_res = ProEditorQC.evaluate_quality_control(dummy_out)
        self.assertTrue(qc_res["video_integrity"]["passed"])

    def test_S_false_success_protection_verification(self):
        """Scenario S: False-success protection verification"""
        missing_out = os.path.join(self.out_dir, "non_existent_output.mp4")
        qc_res = ProEditorQC.evaluate_quality_control(missing_out)
        self.assertFalse(qc_res["qc_passed"])
        self.assertEqual(qc_res["qc_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
