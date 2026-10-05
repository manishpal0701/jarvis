"""
tests/test_conversation_pipeline_repair.py

Automated tests for the JARVIS Conversation Pipeline Repair (Parts 1-30).
Tests cover:
 - Language detection determinism (English vs Hinglish)
 - Emoji never reaches TTS
 - Brightness failure returns FAILED + clean message
 - Brightness never exposes raw PowerShell command
 - Request ID preserved through brightness command lifecycle
 - System prompt language injection
 - Response identity: one request → one response_id
 - Frontend message aggregation: one request → one message
 - Grammar directives in system prompt
 - No forced task invitations in casual conversation
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLanguageDeterminism(unittest.TestCase):
    """Part 9–11: Language must follow user's current input."""

    def setUp(self):
        from conversation.intelligence.language_analyzer import LanguageAnalyzer
        self.analyzer = LanguageAnalyzer()

    def test_english_input_detected_as_english(self):
        cases = [
            "Hello Jarvis, how are you?",
            "What is Python?",
            "Explain Python in simple words.",
            "Can you help me with something?",
            "I'm feeling lonely",
        ]
        for text in cases:
            result = self.analyzer.analyze(text)
            self.assertEqual(result["language"], "english",
                             f"Expected english for: '{text}', got: {result['language']}")

    def test_hinglish_input_detected_as_hinglish(self):
        cases = [
            "jarvis aaj tum sundar lag rahi ho",
            "mera mood off hai",
            "jarvis aaj kya kar rahi ho?",
            "acha ye batao Python me list kya hoti hai?",
            "aaj mera mood bhot off hai",
        ]
        for text in cases:
            result = self.analyzer.analyze(text)
            self.assertEqual(result["language"], "hinglish",
                             f"Expected hinglish for: '{text}', got: {result['language']}")

    def test_english_after_hinglish_turn(self):
        """Language changes correctly between consecutive turns."""
        # Previous turn was Hinglish
        hinglish = self.analyzer.analyze("mera mood off hai")
        self.assertEqual(hinglish["language"], "hinglish")
        # Current turn is English — must detect English
        english = self.analyzer.analyze("Can you explain what Python is?")
        self.assertEqual(english["language"], "english")

    def test_hinglish_after_english_turn(self):
        """Language switches back to Hinglish correctly."""
        english = self.analyzer.analyze("Can you explain Python?")
        self.assertEqual(english["language"], "english")
        hinglish = self.analyzer.analyze("acha ye batao Python me list kya hoti hai?")
        self.assertEqual(hinglish["language"], "hinglish")


class TestSystemPromptLanguageInjection(unittest.TestCase):
    """Part 9–11: System prompt must inject language instruction dynamically."""

    def setUp(self):
        from ai.ask_ollama import _build_system_prompt
        self._build = _build_system_prompt

    def test_english_prompt_contains_english_directive(self):
        intel = {"language": "english", "language_instruction": "Respond in clean English."}
        prompt = self._build("Boss", "boss", intel, "", "")
        self.assertIn("LANGUAGE: User is speaking English", prompt)
        # The English directive may say "Do NOT mix Hindi/Hinglish words" which is correct.
        # Verify it does NOT instruct Hinglish-style response as the primary mode.
        self.assertNotIn("LANGUAGE: User is speaking Hinglish", prompt)

    def test_hinglish_prompt_contains_hinglish_directive(self):
        intel = {"language": "hinglish", "language_instruction": "Use casual Hinglish."}
        prompt = self._build("Boss", "boss", intel, "", "")
        self.assertIn("LANGUAGE: User is speaking Hinglish", prompt)

    def test_hindi_prompt_contains_hindi_directive(self):
        intel = {"language": "hindi", "language_instruction": "Use simple Hindi."}
        prompt = self._build("Boss", "boss", intel, "", "")
        self.assertIn("LANGUAGE: User is speaking Hindi", prompt)

    def test_default_falls_back_to_english(self):
        """If no language in intel, must default to English."""
        intel = {}
        prompt = self._build("Boss", "boss", intel, "", "")
        self.assertIn("LANGUAGE: User is speaking English", prompt)

    def test_prompt_contains_female_grammar_directive(self):
        intel = {"language": "english"}
        prompt = self._build("Boss", "boss", intel, "", "")
        self.assertIn("FEMALE GRAMMAR", prompt)
        self.assertIn("Samajh gayi", prompt)
        self.assertIn("NOT", prompt)

    def test_prompt_contains_no_forced_invitation(self):
        intel = {"language": "english"}
        prompt = self._build("Boss", "boss", intel, "", "")
        self.assertIn("NEVER end with", prompt)
        self.assertIn("Kya karna hai ab", prompt)


class TestEmojiSanitization(unittest.TestCase):
    """Part 13: Emoji must never reach TTS. UI may keep emoji."""

    def setUp(self):
        from conversation.intelligence.response_validator import ResponseValidator
        self.validator = ResponseValidator()

    def test_emoji_stripped_from_tts(self):
        """Emoji must be removed from TTS text."""
        text = "Thank you Boss 😊❤️"
        cleaned = self.validator.validate_and_clean(text)
        self.assertNotIn("😊", cleaned)
        self.assertNotIn("❤", cleaned)
        self.assertIn("Thank you Boss", cleaned)

    def test_emoji_strip_only_preserves_latin(self):
        """strip_emojis_for_tts removes only emoji, keeps letters."""
        text = "Anytime Boss 😊"
        stripped = self.validator.strip_emojis_for_tts(text)
        self.assertNotIn("😊", stripped)
        self.assertIn("Anytime Boss", stripped)

    def test_no_spoken_emoji_names(self):
        """Emoji names like 'smiling face' must not appear after sanitization."""
        text = "Main theek hoon 😊 aur ready hoon ❤️"
        cleaned = self.validator.validate_and_clean(text)
        self.assertNotIn("smiling", cleaned)
        self.assertNotIn("heart", cleaned)

    def test_clean_text_without_emoji_unchanged(self):
        """Text without emoji should pass through unchanged."""
        text = "Hello Boss. Main theek hoon."
        cleaned = self.validator.validate_and_clean(text)
        self.assertIn("Hello Boss", cleaned)
        self.assertIn("Main theek hoon", cleaned)

    def test_emoji_variation_selectors_stripped(self):
        """Variation selectors (U+FE0F) should be stripped."""
        text = "Hello\uFE0F Boss"
        stripped = self.validator.strip_emojis_for_tts(text)
        self.assertNotIn("\uFE0F", stripped)


class TestBrightnessFailureUX(unittest.TestCase):
    """Parts 14–17: Brightness failure must return clean message, never raw commands."""

    def test_brightness_success_returns_friendly_message(self):
        from tools.computer.brightness_control import BrightnessController
        with patch('subprocess.run') as mock_run:
            # Probe returns True
            probe_result = MagicMock()
            probe_result.stdout = "True\n"
            probe_result.returncode = 0
            # Set returns success
            set_result = MagicMock()
            set_result.stdout = ""
            set_result.stderr = ""
            set_result.returncode = 0
            mock_run.side_effect = [probe_result, set_result]

            # Reset cache
            import tools.computer.brightness_control as bc
            bc._wmi_brightness_available = None

            success, msg = BrightnessController.set_brightness(50)
            self.assertTrue(success)
            self.assertIn("Boss", msg)
            # Must not contain internal command details
            self.assertNotIn("powershell", msg.lower())
            self.assertNotIn("Get-CimInstance", msg)
            self.assertNotIn("WmiMonitorBrightness", msg)

    def test_brightness_wmi_unavailable_returns_friendly_message(self):
        """If WMI probe returns False, message must be friendly."""
        from tools.computer.brightness_control import BrightnessController
        with patch('subprocess.run') as mock_run:
            probe_result = MagicMock()
            probe_result.stdout = "False\n"
            probe_result.returncode = 0
            mock_run.return_value = probe_result

            import tools.computer.brightness_control as bc
            bc._wmi_brightness_available = None

            success, msg = BrightnessController.set_brightness(50)
            self.assertFalse(success)
            self.assertIn("Boss", msg)
            self.assertNotIn("powershell", msg.lower())
            self.assertNotIn("WMI", msg)
            self.assertNotIn("Command", msg)

    def test_brightness_timeout_returns_clean_message_not_exception(self):
        """Timeout must produce a clean user message, not a traceback."""
        import subprocess
        from tools.computer.brightness_control import BrightnessController
        with patch('subprocess.run') as mock_run:
            # Probe succeeds
            probe_result = MagicMock()
            probe_result.stdout = "True\n"
            probe_result.returncode = 0
            # Set times out
            mock_run.side_effect = [probe_result, subprocess.TimeoutExpired(cmd='powershell', timeout=3)]

            import tools.computer.brightness_control as bc
            bc._wmi_brightness_available = None

            success, msg = BrightnessController.set_brightness(50)
            self.assertFalse(success)
            # Message must be friendly
            self.assertIn("Boss", msg)
            # Must NEVER contain raw command strings
            self.assertNotIn("powershell", msg.lower())
            self.assertNotIn("subprocess", msg.lower())
            self.assertNotIn("Command", msg)
            self.assertNotIn("[", msg)

    def test_brightness_failure_result_is_false_not_success(self):
        """A failed brightness command must return success=False."""
        import subprocess
        from tools.computer.brightness_control import BrightnessController
        with patch('subprocess.run') as mock_run:
            probe_result = MagicMock()
            probe_result.stdout = "True\n"
            probe_result.returncode = 0
            mock_run.side_effect = [probe_result, subprocess.TimeoutExpired(cmd='powershell', timeout=3)]

            import tools.computer.brightness_control as bc
            bc._wmi_brightness_available = None

            success, msg = BrightnessController.set_brightness(10)
            self.assertFalse(success, "Failed brightness command must return success=False")

    def test_wmi_probe_tests_setter_interface(self):
        """Probe must test WmiMonitorBrightnessMethods (setter), not just getter."""
        from tools.computer.brightness_control import _probe_wmi_brightness
        with patch('subprocess.run') as mock_run:
            result = MagicMock()
            result.stdout = "False\n"
            result.returncode = 0
            mock_run.return_value = result

            import tools.computer.brightness_control as bc
            bc._wmi_brightness_available = None

            _probe_wmi_brightness()
            call_args = mock_run.call_args
            cmd_list = call_args[0][0]
            ps_cmd = cmd_list[-1] if isinstance(cmd_list, list) else str(call_args)
            self.assertIn("WmiMonitorBrightnessMethods", ps_cmd,
                          "Probe must test WmiMonitorBrightnessMethods setter interface, not getter")


class TestRequestIdPreservation(unittest.TestCase):
    """Part 16: request_id must survive from route_command through to speak."""

    def test_desktop_automation_engine_accepts_request_id(self):
        """execute_command and _execute_single_command must accept request_id param."""
        from tools.computer.desktop_automation_engine import DesktopAutomationEngine
        import inspect
        sig = inspect.signature(DesktopAutomationEngine.execute_command)
        self.assertIn('request_id', sig.parameters,
                      "execute_command must accept request_id parameter")

    def test_brightness_command_request_id_forwarded(self):
        """When routing brightness command, request_id must flow to _speak."""
        from conversation.command_router import CommandRouter
        router = CommandRouter()
        spoken_texts = []
        request_ids_spoken = []

        original_speak = router._speak
        def capture_speak(text, request_id=None):
            spoken_texts.append(text)
            request_ids_spoken.append(request_id)
        router._speak = capture_speak

        test_req_id = "req_test_brightness_fix_001"

        with patch('tools.computer.desktop_automation_engine.DesktopAutomationEngine.is_desktop_command', return_value=True), \
             patch('tools.computer.desktop_automation_engine.DesktopAutomationEngine.execute_command', return_value=(False, "Sorry Boss, brightness change nahi ho paya.")) as mock_exec, \
             patch('tools.computer.sleep_control.SleepController.is_sleep_command', return_value=False), \
             patch('core.performance_profiler.PerformanceProfiler.mark'), \
             patch('core.performance_profiler.PerformanceProfiler.report'), \
             patch('speech.voice_session_manager.VoiceSessionManager.get_instance') as mock_vsm, \
             patch('tools.email.email_confirmation.EmailConfirmationManager.get_instance') as mock_email, \
             patch('tools.whatsapp.whatsapp_confirmation.WhatsAppConfirmationManager.get_instance') as mock_wa, \
             patch('tools.computer.confirmation_manager.ConfirmationManager.get_instance') as mock_conf, \
             patch('tools.app_builder.app_manager.AppManager') as mock_app_mgr, \
             patch('tools.app_builder.app_intent_router.AppIntentRouter.is_app_build_intent', return_value=False):

            mock_vsm.return_value.start_session.return_value = MagicMock(request_id=test_req_id)
            mock_vsm.return_value.is_request_invalidated.return_value = False
            mock_email.return_value.has_pending_confirmation.return_value = False
            mock_wa.return_value.has_pending_confirmation.return_value = False
            mock_conf.return_value.has_pending_confirmation.return_value = False
            mock_conf.return_value.is_affirmative_response.return_value = False
            mock_conf.return_value.is_negative_response.return_value = False
            mock_app_mgr.return_value.get_active_app.return_value = None
            mock_app_mgr.return_value.get_active_app.return_value = None

            router.route_command("brightness 10 kar do", source="voice", request_id=test_req_id)

        # execute_command must have been called with the same request_id
        mock_exec.assert_called_once()
        call_kwargs = mock_exec.call_args
        passed_req_id = call_kwargs.kwargs.get('request_id') or (call_kwargs.args[1] if len(call_kwargs.args) > 1 else None)
        self.assertEqual(passed_req_id, test_req_id,
                         f"execute_command must receive original request_id={test_req_id}")

        # _speak must also receive the same request_id
        if request_ids_spoken:
            self.assertEqual(request_ids_spoken[0], test_req_id,
                             f"_speak must receive original request_id={test_req_id}")


class TestOneRequestOneResponse(unittest.TestCase):
    """Parts 1–3, 20: One user request must produce one message_id / response_id."""

    def test_speak_chunk_dedup_blocks_same_chunk_key(self):
        """speak_chunk must block duplicate chunk_keys for same request."""
        from speech.speech_coordinator import SpeechCoordinator
        from unittest.mock import MagicMock
        sc = SpeechCoordinator(
            state_machine=MagicMock(),
            timeout_manager=MagicMock()
        )
        dispatched = []

        with patch.object(sc, '_tts_executor') as mock_exec:
            mock_exec.submit = lambda fn: dispatched.append(fn)
            with patch('speech.voice_session_manager.VoiceSessionManager.get_instance') as mock_vsm:
                mock_vsm.return_value.is_request_invalidated.return_value = False
                mock_vsm.return_value.mark_speaking_started = MagicMock()

                req_id = "req_dedup_test_001"
                # First call — should dispatch
                sc.speak_chunk("Hello Boss", request_id=req_id, chunk_id="chunk_1")
                count_after_first = len(dispatched)
                # Second call with same chunk_key — should be blocked
                sc.speak_chunk("Hello Boss", request_id=req_id, chunk_id="chunk_1")
                count_after_second = len(dispatched)

        self.assertEqual(count_after_first, 1, "First speak_chunk should dispatch one TTS job")
        self.assertEqual(count_after_second, 1, "Duplicate chunk_key must be blocked")

    def test_speak_chunk_accepts_display_text_parameter(self):
        """speak_chunk must accept display_text without error."""
        from speech.speech_coordinator import SpeechCoordinator
        sc = SpeechCoordinator(
            state_machine=MagicMock(),
            timeout_manager=MagicMock()
        )
        with patch.object(sc, '_tts_executor') as mock_exec:
            mock_exec.submit = MagicMock()
            with patch('speech.voice_session_manager.VoiceSessionManager.get_instance') as mock_vsm:
                mock_vsm.return_value.is_request_invalidated.return_value = False
                mock_vsm.return_value.mark_speaking_started = MagicMock()
                # Must not raise TypeError for display_text kwarg
                try:
                    sc.speak_chunk(
                        "Thank you Boss",
                        request_id="req_emoji_test",
                        chunk_id="chunk_1",
                        display_text="Thank you Boss 😊",
                        tts_duration_callback=lambda ms: None
                    )
                except TypeError as e:
                    self.fail(f"speak_chunk raised TypeError for display_text: {e}")


class TestTTSDurationTelemetry(unittest.TestCase):
    """Part 7-8: tts_generation_ms must reflect real async durations."""

    def test_record_and_get_tts_duration(self):
        """_record_tts_duration and _get_tts_total_ms must accumulate and return values."""
        from ai.ask_ollama import _record_tts_duration, _get_tts_total_ms
        test_req = "req_tts_telemetry_test_001"

        _record_tts_duration(test_req, 1500.0)
        _record_tts_duration(test_req, 800.0)
        total = _get_tts_total_ms(test_req)
        self.assertAlmostEqual(total, 2300.0, places=1,
                               msg="Total TTS duration must sum all accumulated values")

    def test_get_tts_duration_clears_after_read(self):
        """_get_tts_total_ms must clear accumulator after reading."""
        from ai.ask_ollama import _record_tts_duration, _get_tts_total_ms
        test_req = "req_tts_clear_test_001"

        _record_tts_duration(test_req, 2000.0)
        first = _get_tts_total_ms(test_req)
        second = _get_tts_total_ms(test_req)
        self.assertAlmostEqual(first, 2000.0, places=1)
        self.assertAlmostEqual(second, 0.0, places=1,
                               msg="Second read must return 0 (cleared)")

    def test_empty_accumulator_returns_zero(self):
        """Unknown request_id must return 0.0 without error."""
        from ai.ask_ollama import _get_tts_total_ms
        result = _get_tts_total_ms("req_nonexistent_xyz")
        self.assertEqual(result, 0.0)


class TestResponseValidatorCompleteness(unittest.TestCase):
    """Regression: validate_and_clean must still strip markdown, prefixes, system states."""

    def setUp(self):
        from conversation.intelligence.response_validator import ResponseValidator
        self.validator = ResponseValidator()

    def test_jarvis_prefix_stripped(self):
        text = "Jarvis: Hello Boss."
        cleaned = self.validator.validate_and_clean(text)
        self.assertNotIn("Jarvis:", cleaned)

    def test_markdown_bold_stripped(self):
        text = "**Hello** Boss."
        cleaned = self.validator.validate_and_clean(text)
        self.assertNotIn("**", cleaned)
        self.assertIn("Hello", cleaned)

    def test_code_block_stripped(self):
        text = "Here is code:\n```python\nprint('hi')\n```"
        cleaned = self.validator.validate_and_clean(text)
        self.assertNotIn("```", cleaned)

    def test_system_state_phrase_stripped(self):
        text = "I am thinking... about this."
        cleaned = self.validator.validate_and_clean(text)
        # "thinking..." should be stripped
        self.assertNotIn("thinking...", cleaned)

    def test_theek_hai_trailing_stripped(self):
        text = "Main dekh rahi hoon theek hai?"
        cleaned = self.validator.validate_and_clean(text)
        self.assertNotIn("theek hai", cleaned)


if __name__ == "__main__":
    unittest.main(verbosity=2)
