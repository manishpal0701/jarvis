import os
import unittest
from tools.coding.website_visual_qa import WebsiteVisualQA

class TestContentSourceValidation(unittest.TestCase):
    def test_fabricated_metric_rejection(self):
        # Create temporary dummy dir
        test_dir = os.path.join(os.getcwd(), "scratch", "test_qa_tmp")
        comp_dir = os.path.join(test_dir, "src", "components")
        os.makedirs(comp_dir, exist_ok=True)

        with open(os.path.join(comp_dir, "Hero.tsx"), "w", encoding="utf-8") as f:
            f.write("export const Hero = () => <div>150+ Enterprise Clients 99.99% Uptime</div>;")

        val_ok, msg = WebsiteVisualQA.validate_content_sources(test_dir)
        self.assertFalse(val_ok)
        self.assertIn("150+ enterprise clients", msg.lower())

if __name__ == '__main__':
    unittest.main()
