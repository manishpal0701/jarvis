import unittest
from tools.coding.website_design_direction import DesignDirectionEngine, DesignLibrary, DesignFingerprint, DesignFingerprintStore

class TestDesignDiversity(unittest.TestCase):
    def test_all_15_directions_unique(self):
        directions = DesignLibrary.get_all_directions()
        self.assertGreaterEqual(len(directions), 15)
        design_ids = [d.design_id for d in directions]
        self.assertEqual(len(design_ids), len(set(design_ids)))

    def test_design_selection_and_similarity(self):
        # First site
        dir1, sim1, reuse1 = DesignDirectionEngine.select_design("Create a tech website for Inurum Technology", "business", "Inurum Technology")
        self.assertIsNotNone(dir1)
        self.assertFalse(reuse1)

        # Second site for different company
        dir2, sim2, reuse2 = DesignDirectionEngine.select_design("Create a restaurant website for Bella Tavola", "restaurant", "Bella Tavola")
        self.assertIsNotNone(dir2)
        self.assertFalse(reuse2)
        self.assertNotEqual(dir1.design_id, dir2.design_id)
        self.assertLess(sim2, 0.70)

if __name__ == '__main__':
    unittest.main()
