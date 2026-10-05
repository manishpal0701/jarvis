"""
tests/test_visual_reasoning.py
Unit tests for JARVIS Phase 4 VisualReasoningEngine, Grounding Tags, and CommandRouter Vision Integration.
"""

import unittest
from vision.visual_reasoning_engine import VisualReasoningEngine
from vision.vision_provider import LocalVisionProvider
from conversation.command_router import CommandRouter


class TestVisualReasoning(unittest.TestCase):
    def setUp(self):
        self.engine = VisualReasoningEngine()
        self.router = CommandRouter()

    def test_visual_query_processing(self):
        res = self.engine.process_visual_query("screen dekho aur batao kya hai")
        self.assertTrue(res.get("success"))
        resp = res.get("response", "")
        self.assertTrue(any(tag in resp for tag in ["[OBSERVED]", "[INFERRED]", "[UNKNOWN]"]))

    def test_error_inferencing(self):
        err_sol = self.engine._infer_error_solution("Traceback (most recent call last):\n  File 'test.py'\nSyntaxError: invalid syntax")
        self.assertIn("Syntax Error", err_sol)

    def test_local_vision_provider(self):
        provider = LocalVisionProvider()
        res = provider.analyze_screen(None, "explain error", context_dict={
            "active_window": {"window_title": "VS Code", "process_name": "code.exe", "app_category": "IDE"},
            "ocr_summary": {"detected_errors": ["TypeError: Cannot read property 'map' of undefined"], "code_snippets": [], "full_text": ""}
        })
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("provider"), "LocalVisionFallback")

    def test_command_router_is_vision_query(self):
        self.assertTrue(self.router.is_vision_query("screen dekho"))
        self.assertTrue(self.router.is_vision_query("what is on my screen"))
        self.assertTrue(self.router.is_vision_query("ye error kya hai"))
        self.assertTrue(self.router.is_vision_query("is code ko explain karo"))
        self.assertFalse(self.router.is_vision_query("python me calculator bana do"))


if __name__ == "__main__":
    unittest.main()
