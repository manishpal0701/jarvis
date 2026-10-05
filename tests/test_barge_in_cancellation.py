import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from speech.speech_coordinator import SpeechCoordinator
from speech.queue_manager import QueueManager
from speech.voice_session_manager import VoiceSessionManager
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager
from conversation.command_router import CommandRouter

class TestBargeInAndCancellation(unittest.TestCase):

    def setUp(self):
        self.state_machine = StateMachine()
        self.timeout_manager = TimeoutManager(timeout_seconds=10.0)
        self.coordinator = SpeechCoordinator(self.state_machine, self.timeout_manager)
        self.queue_mgr = QueueManager()
        self.vsm = VoiceSessionManager.get_instance()

    def test_01_queue_manager_cancel_request(self):
        self.queue_mgr.enqueue("dummy_audio.mp3", "dummy text", speech_id="speech_test_1")
        self.assertFalse(self.queue_mgr.queue.empty())

        self.queue_mgr.cancel_request("req_test_1")
        self.assertTrue(self.queue_mgr.queue.empty())

    def test_02_speech_coordinator_interrupt_speech(self):
        session = self.vsm.start_session("Test prompt", request_id="req_barge_1")
        req_id = session.request_id

        # Interrupt active speech
        self.coordinator.interrupt_speech(reason="user_barge_in", request_id=req_id)
        
        # Verify request identity is invalidated
        self.assertTrue(self.vsm.is_request_invalidated(req_id))

    def test_03_stale_response_protection(self):
        session_a = self.vsm.start_session("First request", request_id="req_stale_a")
        self.coordinator.interrupt_speech(reason="user_barge_in", request_id="req_stale_a")

        # Attempt to speak on stale request_id
        # Should be blocked and not raise exception
        self.coordinator.speak("Stale text output", wait=False, request_id="req_stale_a")
        self.assertTrue(self.vsm.is_request_invalidated("req_stale_a"))

    def test_04_speech_vs_task_cancellation_routing(self):
        router = CommandRouter(self.coordinator)
        
        # 1. Stop Speech Only ("Stop talking")
        router.route_command("Stop talking", source="voice", request_id="req_stop_speech")
        # Should trigger speech interruption cleanly
        self.assertTrue(self.vsm.is_request_invalidated("req_stop_speech"))

        # 2. Cancel Task ("Stop this task")
        router.route_command("Stop this task", source="voice", request_id="req_cancel_task")
        self.assertTrue(self.vsm.is_request_invalidated("req_cancel_task"))

if __name__ == "__main__":
    unittest.main()
