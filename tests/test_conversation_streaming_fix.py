import unittest
from unittest.mock import MagicMock, patch
import time

from agent.task_model import TaskModel
from agent.agent_result import AgentResult, AgentResultStatus
from agent.agent_registry import AgentRegistry


class TestConversationStreamingFix(unittest.TestCase):

    @patch("ai.ask_ollama.ask_ollama_streaming")
    def test_handle_conversation_calls_streaming(self, mock_ask_streaming):
        """Verify _handle_conversation calls ask_ollama_streaming with correct parameters."""
        mock_ask_streaming.return_value = "Hello Boss, system online hai."
        registry = AgentRegistry.get_instance()
        task = TaskModel(task_id="t101", request_id="test_req_101", user_request="Hello JARVIS", normalized_goal="Hello JARVIS")
        
        result = registry._handle_conversation(task, None)
        
        self.assertTrue(mock_ask_streaming.called)
        args, kwargs = mock_ask_streaming.call_args
        self.assertEqual(args[0], "Hello JARVIS")
        self.assertEqual(kwargs.get("speaker_name"), "Boss")
        self.assertEqual(kwargs.get("relation"), "boss")
        self.assertEqual(kwargs.get("request_id"), "test_req_101")
        self.assertEqual(result.agent_id, "conversation_agent")
        self.assertEqual(result.status, AgentResultStatus.SUCCESS)
        self.assertEqual(result.result, "Hello Boss, system online hai.")

    @patch("ai.ask_ollama.AIResponseManager")
    @patch("ai.ask_ollama.ConversationManager")
    def test_sentence_dispatcher_direct_speech(self, mock_conv_mgr_cls, mock_ai_mgr_cls):
        """Verify sentence dispatcher sends sentence chunks to speech_coordinator when speak_callback is None."""
        from ai.ask_ollama import ask_ollama_streaming
        
        mock_conv_instance = MagicMock()
        mock_conv_mgr_cls.return_value = mock_conv_instance
        mock_ai_instance = MagicMock()
        mock_ai_mgr_cls.return_value = mock_ai_instance
        
        spoken_chunks = []
        mock_speech_coordinator = MagicMock()
        mock_speech_coordinator.speak_chunk = MagicMock(side_effect=lambda chunk, wait=False, request_id=None, chunk_id=None, **kwargs: spoken_chunks.append(chunk))
        mock_speech_coordinator.speak = MagicMock()

        def fake_generate_streaming(messages, sentence_callback, **kwargs):
            sentence_callback("Haan Boss.")
            sentence_callback("Main bilkul sahi kaam kar rahi hoon.")
            return "Haan Boss. Main bilkul sahi kaam kar rahi hoon."

        mock_ai_instance.generate_response_streaming = fake_generate_streaming

        res = ask_ollama_streaming(
            "halat batao",
            speaker_name="Boss",
            relation="boss",
            speech_coordinator=mock_speech_coordinator,
            request_id="test_stream_dispatch_1"
        )

        self.assertEqual(len(spoken_chunks), 2)
        self.assertIn("Haan Boss.", spoken_chunks[0])
        self.assertIn("Main bilkul sahi kaam kar rahi hoon.", spoken_chunks[1])
        # Verify post-stream speak(full_response) was NOT called because _chunk_count > 0
        calls = mock_speech_coordinator.speak.call_args_list
        for call in calls:
            self.assertNotEqual(call.kwargs.get("wait"), True, "full_response post-stream wait=True speak should not be called when chunks were dispatched")

    def test_command_router_no_duplicate_speak_for_conversation_agent(self):
        """Verify command_router does not invoke _speak for conversation_agent results."""
        from conversation.command_router import CommandRouter
        router = CommandRouter()
        router._speak = MagicMock()
        
        mock_agent_result = AgentResult(
            success=True,
            task_id="t1",
            agent_id="conversation_agent",
            status=AgentResultStatus.SUCCESS,
            result="Streaming test response"
        )
        
        with patch("agent.agent_orchestrator.AgentOrchestrator.get_instance") as mock_orch_get:
            mock_orch = MagicMock()
            mock_orch.orchestrate.return_value = mock_agent_result
            mock_orch_get.return_value = mock_orch
            
            router.route_command("kya haal hai", source="voice", sync_execution=True, request_id="test_dup_1")
            
            # _speak should NOT be called for conversation_agent in Priority 13
            router._speak.assert_not_called()


if __name__ == "__main__":
    unittest.main()
