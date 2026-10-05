import unittest
from unittest.mock import MagicMock, patch
from ai.prompt import REACT_FILE_PROMPT
from speech.wake_manager import WakeManager
from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager
from core.session_manager import SessionManager

class TestWakeAndPromptFixes(unittest.TestCase):
    def test_react_prompt_forbids_fake_terminals_and_metrics(self):
        """Verify REACT_FILE_PROMPT contains strict rules forbidding fake terminals, dashboards, and metrics."""
        self.assertIn("ABSOLUTE CONTENT BAN", REACT_FILE_PROMPT)
        self.assertIn("fake terminal windows", REACT_FILE_PROMPT)
        self.assertIn("fake metrics", REACT_FILE_PROMPT)

    def test_continuous_command_extraction_in_wake_manager(self):
        """Verify check_wake_word extracts commands following 'Jarvis' in the same utterance."""
        sm = StateMachine()
        tm = TimeoutManager()
        sess = SessionManager(sm)
        lm = MagicMock()
        sc = MagicMock()

        wm = WakeManager(sm, tm, sess, lm, sc)

        test_cases = [
            ("Jarvis ek modern portfolio website bana do", "ek modern portfolio website bana do"),
            ("Jarvis mere restaurant ke liye ek modern website bana do", "mere restaurant ke liye ek modern website bana do"),
            ("Jarvis calculator bana do Python mein", "calculator bana do Python mein"),
            ("Jarvis", True)
        ]

        for input_speech, expected in test_cases:
            lm.listen_and_recognize.return_value = input_speech
            res = wm.check_wake_word()
            self.assertEqual(res, expected, f"Failed for input: {input_speech}")

    def test_command_normalization(self):
        """Verify normalize_command removes ONLY the leading wake word 'jarvis'."""
        from speech.listener_manager import normalize_command
        cases = [
            ("Jarvis what is Python", "what is Python"),
            ("Jarvis ek modern portfolio website bana do", "ek modern portfolio website bana do"),
            ("Jarvis mere restaurant ke liye ek modern responsive website bana do", "mere restaurant ke liye ek modern responsive website bana do"),
            ("Jarvis what is Python and where is it used", "what is Python and where is it used"),
            ("ek website bana do", "ek website bana do"),
            ("Jarvis", "Jarvis"),
            ("None", "")
        ]
        for inp, expected in cases:
            res = normalize_command(inp)
            self.assertEqual(res, expected, f"Failed normalize for '{inp}'")

if __name__ == "__main__":
    unittest.main()
