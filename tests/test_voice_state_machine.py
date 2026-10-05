import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from speech.voice_state_machine import VoiceStateMachine, VoiceState

class TestVoiceStateMachine(unittest.TestCase):

    def setUp(self):
        self.vsm = VoiceStateMachine(VoiceState.IDLE)

    def test_01_initial_state(self):
        self.assertEqual(self.vsm.state, VoiceState.IDLE)

    def test_02_valid_transitions(self):
        # IDLE -> LISTENING -> PROCESSING -> SPEAKING -> COMPLETED -> IDLE
        self.assertTrue(self.vsm.transition_to(VoiceState.LISTENING))
        self.assertEqual(self.vsm.state, VoiceState.LISTENING)

        self.assertTrue(self.vsm.transition_to(VoiceState.PROCESSING))
        self.assertEqual(self.vsm.state, VoiceState.PROCESSING)

        self.assertTrue(self.vsm.transition_to(VoiceState.SPEAKING))
        self.assertEqual(self.vsm.state, VoiceState.SPEAKING)

        self.assertTrue(self.vsm.transition_to(VoiceState.COMPLETED))
        self.assertEqual(self.vsm.state, VoiceState.COMPLETED)

        self.assertTrue(self.vsm.transition_to(VoiceState.IDLE))
        self.assertEqual(self.vsm.state, VoiceState.IDLE)

    def test_03_interruption_transition_flow(self):
        # SPEAKING -> INTERRUPTED -> CANCELLING -> LISTENING
        self.assertTrue(self.vsm.transition_to(VoiceState.SPEAKING))
        self.assertTrue(self.vsm.transition_to(VoiceState.INTERRUPTED))
        self.assertEqual(self.vsm.state, VoiceState.INTERRUPTED)

        self.assertTrue(self.vsm.transition_to(VoiceState.CANCELLING))
        self.assertEqual(self.vsm.state, VoiceState.CANCELLING)

        self.assertTrue(self.vsm.transition_to(VoiceState.LISTENING))
        self.assertEqual(self.vsm.state, VoiceState.LISTENING)

    def test_04_invalid_transitions_rejected(self):
        # IDLE -> COMPLETED is invalid
        self.assertFalse(self.vsm.transition_to(VoiceState.COMPLETED))
        self.assertEqual(self.vsm.state, VoiceState.IDLE)

if __name__ == "__main__":
    unittest.main()
