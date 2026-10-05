"""
tests/test_app_runtime.py
Phase 5 Unit Test Suite — Real Build, Run, Integration Testing & Autonomous Debugging.
Tests all Phase 5 classes, command executions, background process handles, health checks, integration tests, error parsing, and telemetry reports.
"""
import os
import json
import shutil
import unittest
from tools.app_builder.app_model import AppProject, AppBrief, AppState
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_development_planner import AppDevelopmentPlanner
from tools.app_builder.app_workspace_manager import AppWorkspaceManager
from tools.app_builder.app_coding_agent import AppCodingAgent
from tools.app_builder.flutter_runtime import FlutterRuntime
from tools.app_builder.node_runtime import NodeRuntime
from tools.app_builder.api_integration_tester import ApiIntegrationTester
from tools.app_builder.runtime_error_analyzer import RuntimeErrorAnalyzer
from tools.app_builder.app_runtime_orchestrator import AppRuntimeOrchestrator


class TestAppRuntime(unittest.TestCase):

    def setUp(self):
        self.app_mgr = AppManager()
        self.app_mgr.reset()
        self.test_dir = os.path.abspath(os.path.join(os.getcwd(), "JARVIS App Projects", "TestRuntimeProject"))
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        self.app_mgr.reset()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # TEST 1: Flutter Runtime Check
    def test_01_flutter_runtime_check(self):
        res = FlutterRuntime.check_flutter()
        self.assertIn("success", res)

    # TEST 2: Node Runtime Check
    def test_02_node_runtime_check(self):
        res = NodeRuntime.check_node()
        self.assertTrue(res["success"])
        self.assertTrue(len(res["node_version"]) > 0)

    # TEST 3: Node Syntax Check
    def test_03_node_syntax_check(self):
        dummy_js = os.path.join(self.test_dir, "backend", "src", "app.js")
        os.makedirs(os.path.dirname(dummy_js), exist_ok=True)
        with open(dummy_js, "w", encoding="utf-8") as f:
            f.write("const express = require('express'); const app = express(); module.exports = app;")

        res = NodeRuntime.syntax_check(os.path.join(self.test_dir, "backend"), entrypoint="src/app.js")
        self.assertTrue(res["success"])

    # TEST 4: Node Process Startup & Health Check
    def test_04_node_server_startup_and_health_check(self):
        dummy_backend = os.path.join(self.test_dir, "backend")
        entry = os.path.join(dummy_backend, "src", "server.js")
        pkg_file = os.path.join(dummy_backend, "package.json")
        os.makedirs(os.path.dirname(entry), exist_ok=True)

        with open(pkg_file, "w", encoding="utf-8") as f:
            f.write('{"name": "test-backend", "type": "commonjs"}')

        server_code = """
const http = require('http');
const port = process.env.PORT || 3099;
const server = http.createServer((req, res) => {
  if (req.url === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'OK' }));
  } else {
    res.writeHead(404);
    res.end();
  }
});
server.listen(port);
"""
        with open(entry, "w", encoding="utf-8") as f:
            f.write(server_code)

        server_info = NodeRuntime.start_server(dummy_backend, port=3099, entrypoint="src/server.js")
        self.assertTrue(server_info["success"])

        # Physical HTTP Health Check
        h_res = NodeRuntime.health_check("http://127.0.0.1:3099/api/health", timeout=5)
        self.assertTrue(h_res["success"])
        self.assertEqual(h_res["status_code"], 200)

        # Stop server
        stop_res = NodeRuntime.stop_server(server_info)
        self.assertTrue(stop_res)

    # TEST 5: API Contract Integration Tester
    def test_05_api_integration_tester(self):
        dummy_backend = os.path.join(self.test_dir, "backend")
        entry = os.path.join(dummy_backend, "src", "server.js")
        pkg_file = os.path.join(dummy_backend, "package.json")
        os.makedirs(os.path.dirname(entry), exist_ok=True)

        with open(pkg_file, "w", encoding="utf-8") as f:
            f.write('{"name": "test-backend", "type": "commonjs"}')

        server_code = """
const http = require('http');
const port = process.env.PORT || 3098;
const items = [];

const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  if (req.url === '/api/health') {
    res.writeHead(200);
    res.end(JSON.stringify({ status: 'OK' }));
  } else if (req.url === '/api/auth/login' && req.method === 'POST') {
    res.writeHead(200);
    res.end(JSON.stringify({ token: 'mock' }));
  } else if (req.url === '/api/items' && req.method === 'POST') {
    items.push({ id: '1', title: 'Item 1' });
    res.writeHead(201);
    res.end(JSON.stringify({ success: true, item: { id: '1', title: 'Item 1' } }));
  } else if (req.url === '/api/items' && req.method === 'GET') {
    res.writeHead(200);
    res.end(JSON.stringify({ data: items }));
  } else if (req.url === '/api/items/1' && req.method === 'DELETE') {
    res.writeHead(200);
    res.end(JSON.stringify({ success: true }));
  } else {
    res.writeHead(404);
    res.end();
  }
});
server.listen(port);
"""
        with open(entry, "w", encoding="utf-8") as f:
            f.write(server_code)

        server_info = NodeRuntime.start_server(dummy_backend, port=3098, entrypoint="src/server.js")
        self.assertTrue(server_info["success"])

        # Perform Integration Test
        api_res = ApiIntegrationTester.test_api_integration(self.test_dir, port=3098)
        self.assertTrue(api_res["success"])
        self.assertEqual(api_res["passed_tests"], 5)

        NodeRuntime.stop_server(server_info)

    # TEST 6: Runtime Error Analyzer Parsing
    def test_06_runtime_error_analyzer(self):
        flutter_log = "error • Undefined name 'authService' • lib/screens/login_screen.dart:42:15 • undefined_identifier"
        parsed = RuntimeErrorAnalyzer.parse_error(flutter_log, platform="flutter")

        self.assertEqual(parsed["platform"], "flutter")
        self.assertEqual(parsed["file"], "lib/screens/login_screen.dart")
        self.assertEqual(parsed["line"], 42)
        self.assertEqual(parsed["column"], 15)
        self.assertIn("Undefined name", parsed["message"])

    # TEST 7: Dynamic Test Plan Generation
    def test_07_runtime_test_plan_generation(self):
        brief = AppBrief(name="TestApp", description="App description", features=["Dashboard"])
        plan = AppDevelopmentPlanner.generate_plan(brief, app_id="test_plan")

        orch = AppRuntimeOrchestrator()
        test_plan = orch.generate_runtime_test_plan(self.test_dir, plan)

        self.assertIn("flutter", test_plan)
        self.assertIn("node", test_plan)
        self.assertIn("integration", test_plan)
        self.assertIn("android", test_plan)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "runtime_test_plan.json")))

    # TEST 8: Device Detection / BLOCKED State Handling
    def test_08_android_device_detection_blocked_handling(self):
        det = FlutterRuntime.detect_devices()
        self.assertIn("has_devices", det)
        
        # If no device, run_app must return BLOCKED state cleanly without crashing
        run_res = FlutterRuntime.run_app(self.test_dir)
        if not det["has_devices"]:
            self.assertEqual(run_res["status"], "BLOCKED")
            self.assertIn("No Android device", run_res["reason"])


if __name__ == "__main__":
    unittest.main()
