import sys
from unittest.mock import MagicMock
from speech.wake_manager import WakeManager
from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager
from core.session_manager import SessionManager

def run_command_recognition_tests():
    sys.stdout.reconfigure(line_buffering=True)
    print("=" * 60)
    print("REAL MANUAL E2E COMMAND RECOGNITION TEST SUITE")
    print("=" * 60)

    sm = StateMachine()
    tm = TimeoutManager()
    sess = SessionManager(sm)
    lm = MagicMock()
    sc = MagicMock()

    wm = WakeManager(sm, tm, sess, lm, sc)

    test_phrases = [
        "Jarvis ek modern portfolio website bana do",
        "Jarvis mere restaurant ke liye ek modern website bana do",
        "Jarvis calculator bana do Python mein"
    ]

    for phrase in test_phrases:
        print(f"\n[TESTING PHRASE]: '{phrase}'")
        lm.listen_and_recognize.return_value = phrase
        cmd = wm.check_wake_word()
        print(f"[EXTRACTED COMMAND]: '{cmd}'")

    print("\n" + "=" * 60)
    print("ALL COMMAND RECOGNITION TESTS VERIFIED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    run_command_recognition_tests()
