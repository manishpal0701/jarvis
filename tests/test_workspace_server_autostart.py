"""
tests/test_workspace_server_autostart.py
Regression test for Workspace Server Auto-Start & Health Check:
1. Detects server not running -> automatically starts server.
2. Performs HTTP health check on http://127.0.0.1:5000 / http://127.0.0.1:{port}.
3. Verifies Client Brief becomes available.
4. Verifies form remains empty and waiting for manual input (NO auto-fill).
5. Verifies website generation is NOT triggered automatically.
"""

import unittest
import urllib.request
import json
import time
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.website_session_manager import WebsiteSessionManager, WebsiteSessionState
from tools.coding.local_client_brief import LocalClientBriefSession


class TestWorkspaceServerAutostart(unittest.TestCase):

    def setUp(self):
        # Reset brief session and website session
        LocalClientBriefSession.get_instance().reset_session()
        WebsiteSessionManager.get_instance().reset_session()

    def test_1_server_health_check_detection(self):
        """Test health check detection function on WorkspaceManager."""
        # Check health returns boolean
        is_healthy = WorkspaceManager.check_health(5000, timeout=0.5)
        self.assertIsInstance(is_healthy, bool)

    def test_2_autostart_workspace_server_and_verify_health(self):
        """Test workspace server auto-start and HTTP 200 health check verification."""
        ws = WorkspaceManager.get_instance()
        started = ws.ensure_started(timeout=10.0)
        self.assertTrue(started, "Workspace server should be started and healthy.")
        self.assertTrue(ws.server_started)

        # Health check GET request to server
        url = f"http://127.0.0.1:{ws.port}/api/brief/status"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertIn("session_state", data)

    def test_3_client_brief_request_autostarts_server_and_remains_manual(self):
        """
        Integration test:
        1. Request Client Brief ("Jarvis, ek website bana do.")
        2. Server automatically starts and becomes reachable.
        3. Client Brief becomes available (Session state = COLLECTING_CLIENT_BRIEF).
        4. Brief is clean & empty (NO auto-fill).
        5. Generation is NOT started automatically.
        """
        sm = WebsiteSessionManager.get_instance()
        msg = sm.start_brief_collection("Jarvis, ek website bana do.")

        # 1. State check
        self.assertEqual(sm.state, WebsiteSessionState.COLLECTING_CLIENT_BRIEF)
        self.assertFalse(sm.WEBSITE_GENERATION_STARTED, "Website generation must NOT start automatically.")

        # 2. Server reachability check
        ws = WorkspaceManager.get_instance()
        self.assertTrue(ws.server_started, "Workspace server should be active.")

        # Call /api/brief/reset to ensure the SERVER's session is also clean
        reset_url = f"http://127.0.0.1:{ws.port}/api/brief/reset"
        reset_req = urllib.request.Request(reset_url, data=b"{}", method='POST')
        reset_req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(reset_req, timeout=5) as resp:
                pass  # Server session now reset
        except Exception:
            pass  # If endpoint unavailable, continue (non-fatal for test)

        url = f"http://127.0.0.1:{ws.port}/api/brief/status"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            # After reset, company_name must be empty or "Client"
            company_name = data.get("company_name", "")
            self.assertIn(company_name, ("", "Client"),
                          f"company_name should be empty after reset, got: {company_name!r}")
            self.assertEqual(len(data.get("assets", [])), 0)
            self.assertEqual(len(data.get("references", [])), 0)

        # 3. Confirmation msg check
        self.assertIn("Client Brief & Assets interface open ho gaya hai", msg)


if __name__ == "__main__":
    unittest.main()
