"""
scratch/test_phase4_acceptance.py
Comprehensive real-world visual acceptance test script for JARVIS Phase 4: Vision + Computer Awareness.
Tests Scenarios A through J.
"""

import os
import sys
import time
import unittest

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vision.screen_frame import ScreenFrame
from vision.screen_capture import ScreenCapture
from vision.window_tracker import WindowTracker
from vision.ocr_engine import OCREngine
from vision.screen_context import ScreenContextAnalyzer, ScreenContext
from vision.privacy_filter import PrivacyFilter, TEMP_SCREENSHOT_DIR
from vision.vision_provider import LocalVisionProvider, OllamaVisionProvider
from vision.visual_reasoning_engine import VisualReasoningEngine
from agent.task_model import TaskModel, TaskType
from agent.agent_registry import AgentRegistry
from conversation.command_router import CommandRouter


class TestPhase4Acceptance(unittest.TestCase):

    def test_scenario_a_full_screen_capture(self):
        print("\n=== SCENARIO A: Full Screen Capture & ScreenFrame Dataclass ===")
        cap = ScreenCapture(max_dimension=1920)
        frame = cap.capture_full_screen()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.capture_source, "full_screen")
        self.assertTrue(frame.frame_id.startswith("frame_"))
        print(f"[PASS] Captured frame_id={frame.frame_id} size={frame.width}x{frame.height} path={frame.image_path}")
        if frame.image_path:
            PrivacyFilter.cleanup_file(frame.image_path)

    def test_scenario_b_region_capture_and_scaling(self):
        print("\n=== SCENARIO B: Region Capture & Auto-Scaling ===")
        cap = ScreenCapture(max_dimension=600)
        frame = cap.capture_region(bbox=(100, 100, 800, 600))
        self.assertIsNotNone(frame)
        self.assertEqual(frame.capture_source, "region")
        self.assertEqual(frame.region, (100, 100, 700, 500))
        # Max dimension scaling check
        self.assertLessEqual(max(frame.width, frame.height), 600)
        print(f"[PASS] Captured ROI scaled down to {frame.width}x{frame.height}")
        if frame.image_path:
            PrivacyFilter.cleanup_file(frame.image_path)

    def test_scenario_c_window_tracking(self):
        print("\n=== SCENARIO C: Active Foreground Window Tracking ===")
        tracker = WindowTracker()
        win_info = tracker.get_active_window_info()
        self.assertIn("window_title", win_info)
        self.assertIn("process_name", win_info)
        self.assertIn("app_category", win_info)
        print(f"[PASS] Active window: '{win_info['window_title']}' ({win_info['process_name']}, Category: {win_info['app_category']})")

    def test_scenario_d_spatial_ocr(self):
        print("\n=== SCENARIO D: Spatial OCR & Bounding Box Extraction ===")
        cap = ScreenCapture(max_dimension=1000)
        ocr = OCREngine()
        frame = cap.capture_full_screen()
        if frame.image_path:
            res = ocr.extract_text(frame.image_path)
            self.assertIsNotNone(res)
            print(f"[PASS] OCR Extracted {len(res.blocks)} text block(s). Full text snippet: '{res.full_text[:80]}...'")
            PrivacyFilter.cleanup_file(frame.image_path)

    def test_scenario_e_privacy_filtering_and_lifecycle(self):
        print("\n=== SCENARIO E: Privacy Filtering & Screenshot Lifecycle Cleanup ===")
        pf = PrivacyFilter.get_instance()

        raw_secret_text = "Database connection string: mongodb+srv://admin:sk-1234567890abcdef12345678@cluster.mongodb.net/db password=MySuperSecretPassword123"
        filtered = pf.filter_text(raw_secret_text)
        self.assertNotIn("sk-1234567890abcdef12345678", filtered)
        self.assertIn("[REDACTED_SECRET]", filtered)
        print(f"[PASS] Redacted text: {filtered}")

        # Check cleanup lifecycle
        cap = ScreenCapture()
        frame = cap.capture_full_screen()
        path = frame.image_path
        self.assertTrue(os.path.exists(path))
        pf.cleanup_file(path)
        self.assertFalse(os.path.exists(path))
        print(f"[PASS] Screenshot safely removed after processing.")

    def test_scenario_f_screen_context_and_change_detection(self):
        print("\n=== SCENARIO F: ScreenContext & Change Detection ===")
        cap = ScreenCapture()
        analyzer = ScreenContextAnalyzer()

        frame1 = cap.capture_full_screen()
        ctx1 = analyzer.analyze_frame(frame1)
        self.assertTrue(ctx1.has_changed)

        frame2 = cap.capture_full_screen()
        ctx2 = analyzer.analyze_frame(frame2, prev_context=ctx1)
        print(f"[PASS] Frame change magnitude: {ctx2.change_magnitude:.4f}, has_changed={ctx2.has_changed}")

        if frame1.image_path:
            PrivacyFilter.cleanup_file(frame1.image_path)
        if frame2.image_path:
            PrivacyFilter.cleanup_file(frame2.image_path)

    def test_scenario_g_visual_reasoning_and_grounding_tags(self):
        print("\n=== SCENARIO G: Visual Reasoning & Grounding Tags ===")
        engine = VisualReasoningEngine()
        res = engine.process_visual_query("screen dekho aur batao kya chal raha hai")
        self.assertTrue(res.get("success"))
        resp = res.get("response", "")
        self.assertTrue(any(tag in resp for tag in ["[OBSERVED]", "[INFERRED]", "[UNKNOWN]"]))
        print(f"[PASS] Grounded Visual QA Response:\n{resp}")

    def test_scenario_h_developer_error_diagnosis(self):
        print("\n=== SCENARIO H: Developer Error Diagnosis ===")
        engine = VisualReasoningEngine()
        err_sol = engine._infer_error_solution("Traceback (most recent call last):\nFile 'app.py', line 42\nTypeError: 'NoneType' object is not subscriptable")
        self.assertIn("TypeError", err_sol)
        print(f"[PASS] Inferred solution: {err_sol}")

    def test_scenario_i_agent_orchestrator_vision_task(self):
        print("\n=== SCENARIO I: Agent Orchestrator TaskType.VISION ===")
        registry = AgentRegistry.get_instance()
        agent = registry.match_agent_for_task(TaskType.VISION)
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_id, "vision_agent")

        task = TaskModel(
            task_id="task_vision_01",
            request_id="req_v1",
            user_request="screen dekho",
            normalized_goal="screen understanding",
            task_type=TaskType.VISION
        )
        step = task.steps[0] if task.steps else None
        res = agent.handler(task, step)
        self.assertTrue(res.success)
        print(f"[PASS] Vision Agent Result: {res.result[:100]}...")

    def test_scenario_j_command_router_vision_integration(self):
        print("\n=== SCENARIO J: CommandRouter Vision Integration ===")
        router = CommandRouter()
        self.assertTrue(router.is_vision_query("screen dekho"))
        self.assertTrue(router.is_vision_query("ye error kya hai"))

        # Test process input without error
        spoken_output = []
        router.speak_callback = lambda txt: spoken_output.append(txt)
        router.route_command("screen dekho", source="test")
        self.assertTrue(len(spoken_output) > 0)
        print(f"[PASS] CommandRouter Spoken Output: {spoken_output[0][:100]}...")


if __name__ == "__main__":
    unittest.main()
