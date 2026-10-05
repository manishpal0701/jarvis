import sys
from unittest.mock import MagicMock
from speech.wake_manager import WakeManager
from speech.listener_manager import ListenerManager, normalize_command
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager
from core.session_manager import SessionManager

def run_controlled_voice_tests():
    sys.stdout.reconfigure(line_buffering=True)
    print("=" * 65)
    print("JARVIS VOICE CONVERSATION PIPELINE CONTROLLED VERIFICATION")
    print("=" * 65)

    sm = StateMachine()
    tm = TimeoutManager()
    sess = SessionManager(sm)
    sc = MagicMock()
    sc.is_speaking.return_value = False

    lm = ListenerManager(sm, tm, sc)
    wm = WakeManager(sm, tm, sess, lm, sc)

    test_cases = [
        ("Test 1: Single-shot query", "Jarvis what is Python", "what is Python", True),
        ("Test 2: Website build prompt", "Jarvis ek modern portfolio website bana do", "ek modern portfolio website bana do", True),
        ("Test 3: Complex restaurant prompt", "Jarvis mere restaurant ke liye ek modern responsive website bana do", "mere restaurant ke liye ek modern responsive website bana do", True),
        ("Test 4: Long multi-clause query", "Jarvis what is Python and where is it used", "what is Python and where is it used", True),
        ("Test 5: Active session command without wake word", "ek website bana do", "ek website bana do", False),
        ("Test 6: Wake word only", "Jarvis", True, True)
    ]

    for label, input_text, expected, is_wake_test in test_cases:
        print(f"\n--- {label} ---")
        lm.listen_and_recognize = MagicMock(return_value=input_text)
        
        if is_wake_test:
            actual = wm.check_wake_word()
        else:
            actual = normalize_command(input_text)

        print(f"INPUT:    '{input_text}'")
        print(f"EXPECTED: '{expected}'")
        print(f"ACTUAL:   '{actual}'")
        assert actual == expected, f"Mismatch for '{label}': expected {expected}, got {actual}"
        print("STATUS:   PASS")

    print("\n" + "=" * 65)
    print("ALL 6 CONTROLLED VOICE PIPELINE TESTS PASSED 100%")
    print("=" * 65)

if __name__ == "__main__":
    run_controlled_voice_tests()
