import unittest
from tools.coding.website_state import WebsiteStateManager, ActiveWebsiteState

class TestWebsiteState(unittest.TestCase):
    def test_01_singleton(self):
        mgr1 = WebsiteStateManager.get_instance()
        mgr2 = WebsiteStateManager.get_instance()
        self.assertIs(mgr1, mgr2)

    def test_02_set_get_active_website(self):
        mgr = WebsiteStateManager.get_instance()
        mgr.clear()
        self.assertIsNone(mgr.get_active_website())

        state = ActiveWebsiteState(
            project_name="Bella Tavola",
            output_directory="/tmp/bella",
            local_url="http://127.0.0.1:5177",
            port=5177
        )
        mgr.set_active_website(state)
        active = mgr.get_active_website()
        self.assertIsNotNone(active)
        self.assertEqual(active.project_name, "Bella Tavola")

    def test_03_url_updates(self):
        mgr = WebsiteStateManager.get_instance()
        mgr.update_temporary_url("https://test.trycloudflare.com")
        self.assertEqual(mgr.get_active_website().temporary_public_url, "https://test.trycloudflare.com")

        mgr.update_permanent_url("https://bella.vercel.app", status="deployed")
        self.assertEqual(mgr.get_active_website().permanent_public_url, "https://bella.vercel.app")
        self.assertEqual(mgr.get_active_website().hosting_status, "deployed")

if __name__ == "__main__":
    unittest.main()
