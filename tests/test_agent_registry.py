import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.agent_result import AgentResult, AgentResultStatus
from agent.agent_registry import AgentRegistry, AgentDescriptor
from agent.task_model import TaskType

class TestAgentRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = AgentRegistry.get_instance()

    def test_01_agent_result_contract(self):
        res = AgentResult(
            success=True,
            task_id="task_123",
            agent_id="test_agent",
            status=AgentResultStatus.SUCCESS,
            result={"key": "val"},
            artifacts=["/path/to/artifact"],
            duration_ms=12.5
        )
        d = res.to_dict()
        self.assertTrue(d["success"])
        self.assertEqual(d["task_id"], "task_123")
        self.assertEqual(d["agent_id"], "test_agent")
        self.assertEqual(d["status"], "SUCCESS")
        self.assertEqual(d["duration_ms"], 12.5)

    def test_02_registry_default_agents(self):
        agents = self.registry.list_agents()
        self.assertGreaterEqual(len(agents), 8, "Registry must contain default wrapped agents")
        
        conversation_agent = self.registry.get_agent("conversation_agent")
        self.assertIsNotNone(conversation_agent)
        self.assertIn(TaskType.CONVERSATIONAL, conversation_agent.supported_tasks)

    def test_03_capability_matching(self):
        app_agent = self.registry.match_agent_for_task(TaskType.APP_BUILD)
        self.assertIsNotNone(app_agent)
        self.assertEqual(app_agent.agent_id, "app_builder_agent")

        video_agent = self.registry.match_agent_for_task(TaskType.VIDEO_EDITING)
        self.assertIsNotNone(video_agent)
        self.assertEqual(video_agent.agent_id, "video_editing_agent")

if __name__ == "__main__":
    unittest.main()
