import unittest
from tools.computer.sleep_control import SleepController
from tools.computer.desktop_automation_engine import DesktopAutomationEngine

class TestLaptopSleepMode(unittest.TestCase):
    def test_sleep_intent_positive_phrases(self):
        positive_commands = [
            "Jarvis, main so raha hoon",
            "Jarvis, main sone ja raha hoon",
            "Jarvis, main bahar ja raha hoon",
            "Jarvis, main bahar ja raha hoon, der se aaunga",
            "Jarvis, laptop sleep pe daal do",
            "Jarvis, laptop ko sleep kar do",
            "Jarvis, put the laptop to sleep",
            "laptop sleep pe daal do",
            "mai sone ja raha hu",
            "main bahar ja rha hu",
            "put system to sleep",
            "go to sleep mode"
        ]
        for cmd in positive_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(
                    SleepController.is_sleep_command(cmd),
                    f"Expected positive sleep intent for: '{cmd}'"
                )
                self.assertTrue(
                    DesktopAutomationEngine.is_desktop_command(cmd),
                    f"Expected desktop automation engine match for: '{cmd}'"
                )

    def test_sleep_intent_negative_phrases(self):
        negative_commands = [
            "what is sleep mode in windows",
            "how to fix sleep quality",
            "explain sleep cycle",
            "python time.sleep function",
            "why do humans sleep",
            "how many hours of sleep do I need",
            "open calculator",
            "volume 50 percent",
            "play Believer on youtube"
        ]
        for cmd in negative_commands:
            with self.subTest(cmd=cmd):
                self.assertFalse(
                    SleepController.is_sleep_command(cmd),
                    f"Expected negative sleep intent for: '{cmd}'"
                )

    def test_desktop_automation_sleep_action_response(self):
        cmd = "Jarvis, main so raha hoon"
        success, response_msg = DesktopAutomationEngine.execute_command(cmd)
        self.assertTrue(success)
        self.assertIn("sleep pe daal deti hoon", response_msg.lower())

if __name__ == "__main__":
    unittest.main()
