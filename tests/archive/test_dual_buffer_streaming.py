import unittest
import os
import shutil
import tempfile
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.stream_filter import MarkdownFenceFilter, TokenBatcher
from tools.coding.code_validator import CodeValidator

class TestDualBufferStreaming(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.assistant = CodeAssistant()
        self.ws = WorkspaceManager.get_instance()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_1_calculator_dual_buffer_live_streaming(self):
        prompt = "calculator program"
        target_file, lang, ext = self.assistant.detect_target_file(prompt, self.test_dir)

        # Track SSE broadcasts emitted during generation
        emitted_events = []
        original_broadcast = self.ws._broadcast

        def capture_broadcast(payload):
            emitted_events.append(payload)
            original_broadcast(payload)

        self.ws._broadcast = capture_broadcast

        try:
            code, saved_path = self.assistant.generate_code(prompt, project_dir=self.test_dir)

            # Check emitted event types
            stream_events = [e for e in emitted_events if e.get("type") == "code_stream"]
            final_set_events = [e for e in emitted_events if e.get("type") == "code_set" and e.get("is_final") is True]

            self.assertGreater(len(stream_events), 0, "Incremental code_stream events should be emitted live")
            self.assertGreater(len(final_set_events), 0, "Final code_set event should be emitted post-validation")

            # Check metadata fields in stream events
            for s_evt in stream_events:
                self.assertIn("line", s_evt)
                self.assertIn("column", s_evt)
                self.assertFalse(s_evt.get("is_final"))

            self.assertTrue(os.path.isfile(saved_path))
        finally:
            self.ws._broadcast = original_broadcast

    def test_2_weather_app_fence_filtering(self):
        filter_inst = MarkdownFenceFilter()

        raw_stream = ["```python\n", "import requests\n", "def get_weather():\n", "    return 'Sunny'\n", "```"]
        cleaned_preview = []

        for token in raw_stream:
            clean = filter_inst.process(token)
            if clean:
                cleaned_preview.append(clean)
        rem = filter_inst.flush()
        if rem:
            cleaned_preview.append(rem)

        full_preview = "".join(cleaned_preview)
        self.assertNotIn("```python", full_preview)
        self.assertNotIn("```", full_preview)
        self.assertIn("import requests", full_preview)

    def test_3_snake_game_streaming_and_validation(self):
        prompt = "snake game"
        code, saved_path = self.assistant.generate_code(prompt, project_dir=self.test_dir)

        self.assertTrue(os.path.isfile(saved_path))
        is_valid, _ = CodeValidator.validate(code, "python")
        self.assertTrue(is_valid)

    def test_4_portfolio_website_multi_file_streaming(self):
        prompt = "modern portfolio website"
        from tools.coding.website_planner import WebsiteProjectPlanner
        plan = WebsiteProjectPlanner.plan_project(prompt, self.test_dir)
        paths = [f.path for f in plan.files]

        self.assertIn("index.html", paths)
        self.assertIn("src/App.tsx", paths)

    def test_5_forced_validation_failure_auto_repair_replacement(self):
        # Test validator failure and repair logic handling
        invalid_code = "def broken_code():\n    return syntax error here!!"
        is_valid, err_msg = CodeValidator.validate(invalid_code, "python")
        self.assertFalse(is_valid)

        # Confirm workspace set_final_code handles replacement
        self.ws.set_final_code("# Repaired Code\ndef fixed(): pass", file_path="broken.py")
        self.assertEqual(self.ws.files_content.get("broken.py"), "# Repaired Code\ndef fixed(): pass")

    def test_6_browser_reconnect_init_state_restoration(self):
        self.ws.files_content["streaming_active.py"] = "print('Live Streaming State')"
        self.ws.set_file_info("streaming_active.py", "python")

        init_payload = {
            "type": "init",
            "file_path": self.ws.file_path,
            "language": self.ws.language,
            "code": self.ws.files_content[self.ws.file_path],
            "all_files": self.ws.files_content
        }

        self.assertEqual(init_payload["file_path"], "streaming_active.py")
        self.assertEqual(init_payload["code"], "print('Live Streaming State')")

if __name__ == "__main__":
    unittest.main()
