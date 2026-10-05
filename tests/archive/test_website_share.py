import unittest
from tools.coding.website_share import TemporaryWebsiteShare

class TestWebsiteShare(unittest.TestCase):
    def test_01_cloudflared_availability(self):
        avail = TemporaryWebsiteShare.is_cloudflared_available()
        self.assertIsInstance(avail, bool)

    def test_02_share_response_structure(self):
        sharer = TemporaryWebsiteShare.get_instance()
        res = sharer.start(port=5177, timeout_sec=2)
        self.assertIn("success", res)
        self.assertIn("local_url", res)
        self.assertIn("public_url", res)
        self.assertIn("provider", res)
        self.assertEqual(res["provider"], "cloudflare")
        self.assertTrue(res["temporary"])

    def test_03_share_stop(self):
        sharer = TemporaryWebsiteShare.get_instance()
        sharer.stop()
        self.assertEqual(sharer.get_public_url(), "")

if __name__ == "__main__":
    unittest.main()
