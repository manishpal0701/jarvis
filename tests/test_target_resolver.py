"""
tests/test_target_resolver.py
Unit tests for JARVIS Phase 5 TargetResolver, Spatial Target Resolution, and Frame Staleness Protection.
"""

import unittest
from tools.computer.target_resolver import TargetResolver
from tools.computer.action_model import ActionTarget
from vision.screen_frame import ScreenFrame
from vision.screen_context import ScreenContext


class TestTargetResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = TargetResolver()

    def test_similarity_calculation(self):
        sim1 = self.resolver._compute_label_similarity("run button", "run button")
        self.assertEqual(sim1, 1.0)

        sim2 = self.resolver._compute_label_similarity("run", "run button")
        self.assertGreaterEqual(sim2, 0.85)

    def test_target_resolution_fallback(self):
        res = self.resolver.resolve_target("NonExistentTargetElement12345", auto_cleanup=True)
        self.assertIsNotNone(res.target)
        self.assertGreaterEqual(res.confidence, 0.40)

    def test_target_staleness_invalidation(self):
        target = ActionTarget(semantic_label="Submit", frame_id="frame_01")
        ctx_same = ScreenContext(frame=ScreenFrame(frame_id="frame_01"), has_changed=False, change_magnitude=0.0)
        self.assertTrue(self.resolver.validate_target_freshness(target, ctx_same))

        ctx_changed = ScreenContext(frame=ScreenFrame(frame_id="frame_02"), has_changed=True, change_magnitude=0.25)
        self.assertFalse(self.resolver.validate_target_freshness(target, ctx_changed))


if __name__ == "__main__":
    unittest.main()
