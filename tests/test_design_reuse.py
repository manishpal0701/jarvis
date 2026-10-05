import unittest
from tools.coding.website_design_direction import DesignDirectionEngine, DesignFingerprint, DesignFingerprintStore

class TestDesignReuse(unittest.TestCase):
    def test_reuse_keyword_detection(self):
        self.assertTrue(DesignDirectionEngine.detect_reuse_mode("previous design me banao"))
        self.assertTrue(DesignDirectionEngine.detect_reuse_mode("same design as last time"))
        self.assertTrue(DesignDirectionEngine.detect_reuse_mode("pichli website jaisa"))
        self.assertTrue(DesignDirectionEngine.detect_reuse_mode("reuse previous design"))
        self.assertFalse(DesignDirectionEngine.detect_reuse_mode("Create a website for Microsoft"))

    def test_explicit_design_reuse_execution(self):
        # Save a initial fingerprint
        fp = DesignFingerprint(
            design_id="editorial_luxury",
            hero_composition="Centered oversized headline",
            background_system="warm_mahogany_glow",
            focal_object="GoldSculpturalGeometry",
            typography_system="Playfair Display + Inter",
            color_system={"primary": "#f59e0b"},
            section_compositions=["hero_centered_editorial"],
            animation_language="slow_cinematic_fade",
            three_d_strategy="subtle_floating_geometry"
        )
        DesignFingerprintStore.save_fingerprint(fp)

        # Trigger explicit reuse
        direction, sim_score, is_reuse = DesignDirectionEngine.select_design("pichli website jaisa layout for Tesla", "business", "Tesla")
        self.assertTrue(is_reuse)
        self.assertEqual(direction.design_id, "editorial_luxury")
        self.assertEqual(sim_score, 1.0)

if __name__ == '__main__':
    unittest.main()
