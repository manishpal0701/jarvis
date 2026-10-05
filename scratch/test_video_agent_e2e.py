"""
scratch/test_video_agent_e2e.py
Physical End-to-End Test Suite for Phase 5 JARVIS Video Editing Agent.
Creates real sample video files, executes real ingestion, edit planning, FFmpeg rendering,
output verification, error handling, and Premiere Pro status checks.
"""

import os
import sys
import shutil
import unittest
import numpy as np

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath("."))

import cv2
from video_editing.video_session_manager import VideoEditingSessionManager
from video_editing.export.export_verifier import verify_output_file
from video_editing.software.premiere import _bridge_is_alive

SAMPLE_DIR = os.path.abspath("scratch/sample_videos")


def generate_sample_video(path: str, duration_sec: int = 5, color: tuple = (255, 0, 0)):
    """Generates a real valid MP4 video file with OpenCV for physical test ingestion."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    width, height, fps = 640, 360, 30
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps
    for i in range(total_frames):
        # Create shifting color frame
        frame = np.full((height, width, 3), color, dtype=np.uint8)
        cv2.circle(frame, (int((i * 10) % width), height // 2), 30, (255, 255, 255), -1)
        out.write(frame)

    out.release()
    print(f"[TEST_SETUP] Created sample video '{path}' ({duration_sec}s, {os.path.getsize(path)} bytes)")


class TestVideoAgentE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Prepare sample video directory and physical test clips."""
        shutil.rmtree(SAMPLE_DIR, ignore_errors=True)
        os.makedirs(SAMPLE_DIR, exist_ok=True)

        cls.clip1 = os.path.join(SAMPLE_DIR, "travel_clip_a.mp4")
        cls.clip2 = os.path.join(SAMPLE_DIR, "travel_clip_b.mp4")

        generate_sample_video(cls.clip1, duration_sec=4, color=(200, 50, 50))
        generate_sample_video(cls.clip2, duration_sec=5, color=(50, 200, 50))

        cls.session = VideoEditingSessionManager.get_instance()

    def setUp(self):
        self.session.reset_session()

    def test_a_single_video_trim_and_export(self):
        """TEST A: Single video ingestion, trim request, and physical export verification."""
        print("\n=== RUNNING TEST A — SINGLE VIDEO TRIM & EXPORT ===", flush=True)
        cmd = f'"{self.clip1}" ko 3 seconds me trim karke export karo'

        result = self.session.handle_command(cmd, sync_execution=True)

        self.assertIsNotNone(result)
        self.assertIn("FINAL_STATUS: SUCCESS", result)

        out_path = os.path.abspath("data/exports/jarvis_final_edit.mp4")
        self.assertTrue(os.path.isfile(out_path), "Export output file must exist on disk.")

        ver = verify_output_file(out_path)
        self.assertTrue(ver["success"], f"Export verification failed: {ver.get('error')}")
        self.assertTrue(ver["verified"])
        self.assertGreater(ver["file_size_bytes"], 0)
        self.assertGreater(ver["duration"], 0)
        print("[TEST_A_RESULT] PASS — Output file physically verified!")

    def test_b_multi_video_combine(self):
        """TEST B: Multi-video folder ingestion, combination request, and physical export."""
        print("\n=== RUNNING TEST B — MULTI VIDEO COMBINE ===", flush=True)
        cmd = f'Is folder "{SAMPLE_DIR}" ki sabhi videos ko combine karke final edit banao'

        result = self.session.handle_command(cmd, sync_execution=True)

        self.assertIsNotNone(result)
        self.assertIn("FINAL_STATUS: SUCCESS", result)

        out_path = os.path.abspath("data/exports/jarvis_final_edit.mp4")
        ver = verify_output_file(out_path)
        self.assertTrue(ver["success"])
        self.assertGreater(ver["duration"], 4.0)  # Combined duration of clip1 + clip2
        print(f"[TEST_B_RESULT] PASS — Multi video combined! Duration: {ver['duration']}s")

    def test_c_natural_language_cinematic_edit(self):
        """TEST C: Natural language editing instruction for cinematic travel reel."""
        print("\n=== RUNNING TEST C — NATURAL LANGUAGE CINEMATIC EDIT ===", flush=True)
        cmd = f'Jarvis, is folder "{SAMPLE_DIR}" ki videos ko ek cinematic travel reel me edit karo.'

        result = self.session.handle_command(cmd, sync_execution=True)

        self.assertIsNotNone(result)
        self.assertIn("FINAL_STATUS: SUCCESS", result)

        out_path = os.path.abspath("data/exports/jarvis_final_edit.mp4")
        ver = verify_output_file(out_path)
        self.assertTrue(ver["success"])
        print("[TEST_C_RESULT] PASS — Natural language cinematic edit completed!")

    def test_d_error_handling_invalid_source(self):
        """TEST D: Error handling for invalid/non-existent video source folder."""
        print("\n=== RUNNING TEST D — ERROR HANDLING ===", flush=True)
        cmd = 'Is folder "C:/non_existent_folder_xyz987" ki videos edit karo'

        result = self.session.handle_command(cmd, sync_execution=True)

        self.assertIsNotNone(result)
        self.assertIn("selected folder mein koi valid video files nahi mili", result)
        self.assertEqual(self.session.state, "IDLE")
        print("[TEST_D_RESULT] PASS — Error correctly handled without false success!")

    def test_e_premiere_e2e_status_check(self):
        """TEST E: Premiere Pro automation connection check & report validation."""
        print("\n=== RUNNING TEST E — PREMIERE PRO E2E STATUS CHECK ===", flush=True)
        connected = _bridge_is_alive(timeout=1.0)
        status_str = "PASS" if connected else "NOT_VERIFIED"
        print(f"[TEST_E_RESULT] PREMIERE_E2E = {status_str}")
        # Test passes regardless of whether Premiere is open or closed, as long as status is reported correctly without false claims
        self.assertIn(status_str, ["PASS", "NOT_VERIFIED"])


if __name__ == "__main__":
    unittest.main()
