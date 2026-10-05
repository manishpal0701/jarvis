import os
import shutil
import tempfile
import json
import unittest
from unittest.mock import MagicMock, patch

from tools.coding.code_validator import CodeValidator
from tools.coding.website_state import WebsiteStateManager, ActiveWebsiteState
from tools.coding.code_assistant import CodeAssistant

class TestWebsitePipelineFix(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jarvis_test_web_")
        WebsiteStateManager.get_instance().clear()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        WebsiteStateManager.get_instance().clear()

    def test_dependency_closure_detects_unlisted_package(self):
        """Test that validate_dependency_closure flags unlisted @tailwindcss/css import."""
        pkg_json = {
            "name": "test_app",
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1"
            },
            "devDependencies": {
                "tailwindcss": "^4.0.0"
            }
        }
        with open(os.path.join(self.test_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg_json, f)

        src_dir = os.path.join(self.test_dir, "src", "components")
        os.makedirs(src_dir, exist_ok=True)
        about_path = os.path.join(src_dir, "About.tsx")
        with open(about_path, "w", encoding="utf-8") as f:
            f.write("import { Box } from '@tailwindcss/css';\nexport default function About() { return <Box>About</Box>; }")

        is_valid, err_msg = CodeValidator.validate_dependency_closure(self.test_dir)
        self.assertFalse(is_valid)
        self.assertIn("src\\components\\About.tsx", err_msg)
        self.assertIn("@tailwindcss/css", err_msg)

    def test_state_reset_clears_previous_success_state(self):
        """Test that WebsiteStateManager.reset_active_website purges stale success state."""
        mgr = WebsiteStateManager.get_instance()
        old_state = ActiveWebsiteState(
            project_name="old_project",
            output_directory="/old/dir",
            build_passed=True,
            visual_qa_score="20/20",
            local_url="http://127.0.0.1:5173"
        )
        mgr.set_active_website(old_state)

        mgr.reset_active_website("new_project", self.test_dir)
        new_state = mgr.get_active_website()

        self.assertIsNotNone(new_state)
        self.assertEqual(new_state.project_name, "new_project")
        self.assertFalse(new_state.build_passed)
        self.assertFalse(new_state.website_ready)
        self.assertFalse(new_state.dependency_validation_passed)
        self.assertFalse(new_state.preview_running)
        self.assertEqual(new_state.visual_qa_score, "0/20")
        self.assertEqual(new_state.local_url, "")

    @patch("tools.coding.code_assistant.CodeAssistant._speak_status")
    @patch("ai.ai_response_manager.AIResponseManager")
    def test_dependency_auto_repair_3_strikes_failure(self, mock_ai_cls, mock_speak):
        """Test that 3 consecutive dependency repair failures halt the pipeline with WEBSITE BUILD FAILED."""
        mock_ai_instance = MagicMock()
        mock_ai_cls.return_value = mock_ai_instance

        invalid_code = (
            "import { Box } from '@tailwindcss/css';\n"
            "// hero about skills projects experience contact\n"
            "export default function Component() { return <Box>Section</Box>; }"
        )
        mock_ai_instance.generate_response.return_value = invalid_code
        mock_ai_instance.generate_response_token_stream.return_value = [invalid_code]

        assistant = CodeAssistant()
        assistant.ai_manager = mock_ai_instance

        pkg_json = {
            "name": "test_portfolio",
            "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
            "devDependencies": {"tailwindcss": "^4.0.0", "vite": "^5.0.0"}
        }
        with open(os.path.join(self.test_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg_json, f)

        res, entry_path = assistant.build_website("Test portfolio website", project_dir=self.test_dir, open_browser=False)

        state = WebsiteStateManager.get_instance().get_active_website()
        self.assertIn("WEBSITE BUILD FAILED", res)
        self.assertFalse(state.website_ready)
        self.assertFalse(state.dependency_validation_passed)
        self.assertEqual(state.repair_attempts, 3)

    @patch("tools.coding.code_assistant.CodeAssistant._speak_status")
    @patch("tools.coding.website_deployer.LocalPreviewDeployer.execute_production_build")
    @patch("tools.coding.local_website_server.LocalWebsiteServer")
    @patch("ai.ai_response_manager.AIResponseManager")
    def test_dependency_auto_repair_success_loop(self, mock_ai_cls, mock_server_cls, mock_build, mock_speak):
        """Test that invalid dependency is successfully repaired on attempt 1 and pipeline continues."""
        mock_ai_instance = MagicMock()
        mock_ai_cls.return_value = mock_ai_instance

        def side_effect_gen(messages, options=None, **kwargs):
            prompt_str = str(messages)
            if "index.css" in prompt_str.lower():
                return ['@import "tailwindcss";\nbody { background-color: #0f172a; }']

            if "STRICT INSTRUCTIONS" in prompt_str or "Fix dependency closure" in prompt_str or "REPAIR INSTRUCTIONS" in prompt_str:
                return [
                    "import React from 'react';\n"
                    "// hero about skills projects experience contact\n"
                    "export default function About() { return <div className='p-4 text-white'>Building Intelligent Systems</div>; }"
                ]
            else:
                if "target_file: src/components/About.tsx" in prompt_str.lower() or "file:\\nsrc/components/about.tsx" in prompt_str.lower() or "src/components/about.tsx" in prompt_str.lower():
                    return [
                        "import { Box } from '@tailwindcss/css';\n"
                        "// hero about skills projects experience contact\n"
                        "export default function About() { return <Box>Building Intelligent Systems</Box>; }"
                    ]
                return [
                    "import React from 'react';\n"
                    "// hero about skills projects experience contact\n"
                    "export default function Section() { return <div>Building Intelligent Systems</div>; }"
                ]

        mock_ai_instance.generate_response_token_stream.side_effect = side_effect_gen
        mock_ai_instance.generate_response.side_effect = lambda msgs, options=None, **kwargs: side_effect_gen(msgs, options, **kwargs)[0]

        mock_build.return_value = (True, "")

        mock_server_inst = MagicMock()
        mock_server_cls.get_instance.return_value = mock_server_inst
        mock_server_inst.start_preview.return_value = ("http://127.0.0.1:5173", 5173)

        assistant = CodeAssistant()
        assistant.ai_manager = mock_ai_instance

        src_dir = os.path.join(self.test_dir, "src", "components")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump({"dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"}, "devDependencies": {"tailwindcss": "^4.0.0"}}, f)

        with patch("requests.get") as mock_http_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<!DOCTYPE html><html><body><div id='root'></div></body></html>"
            mock_http_get.return_value = mock_resp

            with patch("tools.coding.website_visual_qa.WebsiteVisualQA.evaluate_website", return_value=(True, [])):
                res, entry = assistant.build_website("Test portfolio website", project_dir=self.test_dir, open_browser=False)

        state = WebsiteStateManager.get_instance().get_active_website()
        self.assertTrue(state.website_ready)
        self.assertTrue(state.dependency_validation_passed)
        self.assertTrue(state.build_passed)
        self.assertTrue(state.preview_running)
        self.assertTrue(state.http_status_ok)

    def test_code_gen_model_routing(self):
        """Test that CodeAssistant routes code generation to qwen3:4b-instruct."""
        from config import CODE_GEN_MODEL
        self.assertEqual(CODE_GEN_MODEL, "qwen3:4b-instruct")

    def test_ollama_timeout_protection(self):
        """Test that AIResponseManager raises LLMTimeoutException if streaming exceeds timeout."""
        from ai.ai_response_manager import AIResponseManager, LLMTimeoutException
        mgr = AIResponseManager()
        
        with patch.object(mgr._client, "chat") as mock_chat:
            def slow_generator():
                import time
                time.sleep(0.05)
                yield {"message": {"content": "const"}}
            
            mock_chat.return_value = slow_generator()
            
            with self.assertRaises(LLMTimeoutException):
                list(mgr.generate_response_token_stream([], timeout=0.01, model_name="qwen3:4b-instruct"))

    @patch("tools.coding.code_assistant.CodeAssistant._speak_status")
    @patch("ai.ai_response_manager.AIResponseManager")
    def test_terminal_failure_on_llm_timeout(self, mock_ai_cls, mock_speak):
        """Test that an LLMTimeoutException immediately halts build_website with WEBSITE BUILD FAILED — LLM TIMEOUT."""
        from ai.ai_response_manager import LLMTimeoutException
        mock_ai_instance = MagicMock()
        mock_ai_cls.return_value = mock_ai_instance
        mock_ai_instance.generate_response_token_stream.side_effect = LLMTimeoutException("Ollama generation timed out")
        mock_ai_instance.generate_response.side_effect = LLMTimeoutException("Ollama generation timed out")

        assistant = CodeAssistant()
        assistant.ai_manager = mock_ai_instance

        res, entry = assistant.build_website("Test timeout prompt", project_dir=self.test_dir, open_browser=False)

        state = WebsiteStateManager.get_instance().get_active_website()
        self.assertIn("WEBSITE BUILD FAILED — LLM TIMEOUT", res)
        self.assertFalse(state.website_ready)
        self.assertEqual(state.build_status, "failed")

    def test_mocked_ollama_streaming_and_timeouts(self):
        """Test mocked Ollama stream verifying first token, continuous streaming, code_stream events, file_end, and 60s timeout."""
        from ai.ai_response_manager import AIResponseManager, LLMTimeoutException
        from tools.coding.workspace_manager import WorkspaceManager

        mgr = AIResponseManager()
        ws = WorkspaceManager.get_instance()

        # 1. Verify successful stream tokens
        with patch.object(mgr._client, "chat") as mock_chat:
            def fast_stream():
                yield {"message": {"content": "import React from 'react';\n"}}
                yield {"message": {"content": "export default function App() { return <div>App</div>; }\n"}}

            mock_chat.return_value = fast_stream()
            tokens = list(mgr.generate_response_token_stream([], first_token_timeout=60.0, inter_token_timeout=30.0, file_name="src/App.tsx"))
            self.assertEqual(len(tokens), 2)
            self.assertIn("import React", tokens[0])
            self.assertIn("export default", tokens[1])

        # 2. Verify stalled first token fails at first_token_timeout (60s)
        with patch.object(mgr._client, "chat") as mock_chat:
            def stalled_stream():
                import time
                time.sleep(0.05)
                yield {"message": {"content": "token"}}

            mock_chat.return_value = stalled_stream()
            with self.assertRaises(LLMTimeoutException):
                list(mgr.generate_response_token_stream([], first_token_timeout=0.01, inter_token_timeout=30.0, file_name="src/App.tsx"))

        # 3. Verify workspace stream events emitted and file_end contains complete code
        ws.open_workspace(file_path="src/App.tsx", language="tsx")
        ws.stream_file_start("src/App.tsx")
        ws.stream_code_chunk("import React from 'react';", file_path="src/App.tsx")
        ws.stream_code_chunk(" export default function App() {}", file_path="src/App.tsx")
        ws.stream_file_end("src/App.tsx")

        self.assertIn("import React from 'react'; export default function App() {}", ws.files_content["src/App.tsx"])

    def test_regression_1_malformed_numeric_tsx_output(self):
        """TEST 1: Malformed numeric TSX output fails validation, resets buffer, website_ready = False."""
        from tools.coding.code_validator import CodeValidator
        from tools.coding.workspace_manager import WorkspaceManager
        from tools.coding.website_state import ActiveWebsiteState, WebsiteStateManager

        malformed_tsx = "195-.934.705-.934.705-.546... 2.16 2.04 2.16 1.07 3.14 1.59 2.65"
        is_valid, err = CodeValidator.validate(malformed_tsx, "tsx")
        self.assertFalse(is_valid)
        self.assertIn("Malformed output detected", err)

        ws = WorkspaceManager.get_instance()
        ws.open_workspace(file_path="src/components/Footer.tsx", language="tsx")
        ws.stream_code_chunk(malformed_tsx, file_path="src/components/Footer.tsx")
        ws.reset_file_stream("src/components/Footer.tsx")
        self.assertEqual(ws.files_content["src/components/Footer.tsx"], "")

        state = ActiveWebsiteState(visual_qa_score="20/20", visual_qa_passed=True)
        state.invalidate_downstream("syntax")
        self.assertFalse(state.website_ready)

    def test_regression_2_dependency_validation_failure(self):
        """TEST 2: Dependency validation failure forces website_ready = False."""
        from tools.coding.website_state import ActiveWebsiteState

        state = ActiveWebsiteState(
            dependency_validation_passed=False,
            build_passed=True,
            preview_running=True,
            http_status_ok=True,
            visual_qa_status="passed",
            visual_qa_passed=True,
            responsive_passed=True,
            console_errors=0,
            broken_images=0
        )
        self.assertFalse(state.website_ready)

    def test_regression_3_stale_state_reset_between_builds(self):
        """TEST 3: Previous successful project followed by failed project does not leak old 20/20 score."""
        from tools.coding.website_state import ActiveWebsiteState, WebsiteStateManager

        mgr = WebsiteStateManager.get_instance()
        old_state = ActiveWebsiteState(
            dependency_validation_passed=True,
            build_passed=True,
            preview_running=True,
            http_status_ok=True,
            visual_qa_status="passed",
            visual_qa_passed=True,
            visual_qa_score="20/20",
            responsive_passed=True,
            console_errors=0,
            broken_images=0
        )
        mgr.set_active_website(old_state)
        self.assertTrue(mgr.get_active_website().website_ready)

        # Reset for new build
        mgr.reset_active_website("new_failed_build", "/tmp/new")
        new_state = mgr.get_active_website()
        self.assertFalse(new_state.website_ready)
        self.assertEqual(new_state.visual_qa_score, "0/20")
        self.assertFalse(new_state.visual_qa_passed)
        self.assertFalse(new_state.build_passed)

    def test_regression_4_dependency_failure_invalidates_downstream(self):
        """TEST 4: Dependency validation failure invalidates build/preview/VQA downstream state."""
        from tools.coding.website_state import ActiveWebsiteState

        state = ActiveWebsiteState(
            dependency_validation_passed=True,
            build_passed=True,
            preview_running=True,
            http_status_ok=True,
            visual_qa_status="passed",
            visual_qa_passed=True,
            responsive_passed=True,
            console_errors=0,
            broken_images=0
        )
        self.assertTrue(state.website_ready)

        state.invalidate_downstream("dependency")
        self.assertFalse(state.dependency_validation_passed)
        self.assertFalse(state.build_passed)
        self.assertFalse(state.preview_running)
        self.assertFalse(state.http_status_ok)
        self.assertFalse(state.visual_qa_passed)
        self.assertFalse(state.responsive_passed)
        self.assertFalse(state.website_ready)

    def test_regression_5_any_gate_false_makes_ready_impossible(self):
        """TEST 5: Any single gate false makes WEBSITE READY mathematically impossible."""
        from tools.coding.website_state import ActiveWebsiteState

        base_kwargs = {
            "dependency_validation_passed": True,
            "build_passed": True,
            "preview_running": True,
            "http_status_ok": True,
            "visual_qa_status": "passed",
            "visual_qa_passed": True,
            "responsive_passed": True,
            "console_errors": 0,
            "broken_images": 0
        }

        # 1. Dependency validation false
        k1 = base_kwargs.copy(); k1["dependency_validation_passed"] = False
        self.assertFalse(ActiveWebsiteState(**k1).website_ready)

        # 2. Build passed false
        k2 = base_kwargs.copy(); k2["build_passed"] = False
        self.assertFalse(ActiveWebsiteState(**k2).website_ready)

        # 3. Preview running false
        k3 = base_kwargs.copy(); k3["preview_running"] = False
        self.assertFalse(ActiveWebsiteState(**k3).website_ready)

        # 4. HTTP status false
        k4 = base_kwargs.copy(); k4["http_status_ok"] = False
        self.assertFalse(ActiveWebsiteState(**k4).website_ready)

        # 5. Visual QA status not passed
        k5 = base_kwargs.copy(); k5["visual_qa_status"] = "failed"
        self.assertFalse(ActiveWebsiteState(**k5).website_ready)

        # 6. Visual QA passed false
        k6 = base_kwargs.copy(); k6["visual_qa_passed"] = False
        self.assertFalse(ActiveWebsiteState(**k6).website_ready)

        # 7. Responsive passed false
        k7 = base_kwargs.copy(); k7["responsive_passed"] = False
        self.assertFalse(ActiveWebsiteState(**k7).website_ready)

        # 8. Console errors > 0
        k8 = base_kwargs.copy(); k8["console_errors"] = 2
        self.assertFalse(ActiveWebsiteState(**k8).website_ready)

        # 9. Broken images > 0
        k9 = base_kwargs.copy(); k9["broken_images"] = 1
        self.assertFalse(ActiveWebsiteState(**k9).website_ready)

    def test_regression_6_valid_streamed_tsx_passes(self):
        """TEST 6: Valid streamed TSX code passes validation and complete code is retained."""
        from tools.coding.code_validator import CodeValidator
        from tools.coding.workspace_manager import WorkspaceManager

        valid_tsx = "import React from 'react';\nexport default function Footer() { return <footer>Footer</footer>; }"
        is_valid, err = CodeValidator.validate(valid_tsx, "tsx")
        self.assertTrue(is_valid)
        self.assertEqual(err, "")

        ws = WorkspaceManager.get_instance()
        ws.open_workspace(file_path="src/components/Footer.tsx", language="tsx")
        ws.stream_code_chunk(valid_tsx, file_path="src/components/Footer.tsx")
        ws.stream_file_end("src/components/Footer.tsx")
        self.assertEqual(ws.files_content["src/components/Footer.tsx"], valid_tsx)

    def test_regression_7_sse_chunks_split_inside_token(self):
        """TEST 7: SSE chunks split inside a token reconstruct to exact expected complete code."""
        from tools.coding.workspace_manager import WorkspaceManager

        chunks = ["imp", "ort React", " from 're", "act';\nexp", "ort default function App() { return <div>", "Hello</div>; }"]
        expected = "".join(chunks)

        ws = WorkspaceManager.get_instance()
        ws.open_workspace(file_path="src/App.tsx", language="tsx")
        ws.reset_code("")
        for chunk in chunks:
            ws.stream_code_chunk(chunk, file_path="src/App.tsx")
        ws.stream_file_end("src/App.tsx")

        self.assertEqual(ws.files_content["src/App.tsx"], expected)

    def test_ui_state_rendering_on_build_failure(self):
        """TEST: Verify independent states when npm build fails - preview fails, VQA not run, website_ready False."""
        from tools.coding.website_state import ActiveWebsiteState

        state = ActiveWebsiteState(
            dependency_validation_passed=True,
            build_passed=False,
            preview_running=False,
            http_status_ok=False,
            visual_qa_status="not_started",
            visual_qa_passed=False,
            responsive_passed=False,
            console_errors=0,
            broken_images=0
        )

        self.assertTrue(state.dependency_validation_passed)
        self.assertFalse(state.build_passed)
        self.assertFalse(state.preview_running)
        self.assertFalse(state.http_status_ok)
        self.assertEqual(state.visual_qa_status, "not_started")
        self.assertFalse(state.visual_qa_passed)
        self.assertFalse(state.responsive_passed)
        self.assertFalse(state.website_ready)

if __name__ == "__main__":
    unittest.main()
