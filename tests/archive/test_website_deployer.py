import unittest
import os
from tools.coding.website_deployer import VercelDeployer, DeploymentResult

class TestWebsiteDeployer(unittest.TestCase):
    def test_01_vercel_cli_checks(self):
        cli_avail = VercelDeployer.is_vercel_cli_available()
        self.assertIsInstance(cli_avail, bool)

        auth_ok = VercelDeployer.is_vercel_authenticated()
        self.assertIsInstance(auth_ok, bool)

    def test_02_nonexistent_directory(self):
        deployer = VercelDeployer()
        res = deployer.deploy("nonexistent/directory/path/12345")
        self.assertFalse(res.success)
        self.assertEqual(res.provider, "vercel")

    def test_03_auth_gate_or_deployment(self):
        deployer = VercelDeployer()
        proj_dir = os.path.join(os.getcwd(), "websites", "bella_tavola_ristorante_italiano")
        if not os.path.exists(proj_dir):
            proj_dir = os.getcwd()

        res = deployer.deploy(proj_dir)
        self.assertIsInstance(res, DeploymentResult)
        if not VercelDeployer.is_vercel_authenticated():
            self.assertFalse(res.success)
            self.assertTrue("authentication required" in res.message.lower() or "not installed" in res.error.lower() or "required" in res.error.lower())

if __name__ == "__main__":
    unittest.main()
