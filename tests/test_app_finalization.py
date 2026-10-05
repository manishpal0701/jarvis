import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
try:
    import api.websocket.jarvis
    HAS_WEBSOCKET = True
except ModuleNotFoundError:
    HAS_WEBSOCKET = False


from tools.app_builder.app_model import AppState, AppProject
from tools.app_builder.release_artifact_manager import ReleaseArtifactManager
from tools.app_builder.app_finalization_orchestrator import AppFinalizationOrchestrator


class TestAppFinalization(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace = os.path.join(self.test_dir, "test_app")
        os.makedirs(self.workspace, exist_ok=True)
        self.frontend = os.path.join(self.workspace, "frontend")
        self.backend = os.path.join(self.workspace, "backend")
        os.makedirs(self.frontend, exist_ok=True)
        os.makedirs(self.backend, exist_ok=True)

        # Create basic plans
        self._write_json(os.path.join(self.workspace, "architecture_plan.json"), {"app_metadata": {"needs_backend": True}})
        self._write_json(os.path.join(self.workspace, "api_contract.json"), {
            "routes": [{"path": "/api/health", "method": "GET"}]
        })
        self._write_json(os.path.join(self.workspace, "database_plan.json"), {"storage": "file"})
        self._write_json(os.path.join(self.workspace, "implementation_manifest.json"), {
            "files_generated": ["frontend/pubspec.yaml", "backend/package.json"]
        })
        self._write_json(os.path.join(self.workspace, "runtime_test_plan.json"), {"flutter": ["pub_get"]})

        # Create dummy frontend and backend files
        with open(os.path.join(self.frontend, "pubspec.yaml"), "w") as f:
            f.write("name: test_app\n")
        with open(os.path.join(self.backend, "package.json"), "w") as f:
            f.write('{"name": "test_backend", "main": "src/app.js"}\n')

        os.makedirs(os.path.join(self.frontend, "lib", "services"), exist_ok=True)
        with open(os.path.join(self.frontend, "lib", "services", "api_service.dart"), "w") as f:
            f.write("class ApiService { static const String healthUrl = '/api/health'; }\n")

        os.makedirs(os.path.join(self.backend, "src", "routes"), exist_ok=True)
        with open(os.path.join(self.backend, "src", "routes", "health.js"), "w") as f:
            f.write("router.get('/health', (req, res) => res.json({ status: 'ok' }));\n")
        with open(os.path.join(self.backend, "src", "app.js"), "w") as f:
            f.write("app.get('/api/health', healthRouter);\n")

        # Create dummy APK artifact
        self.apk_dir = os.path.join(self.frontend, "build", "app", "outputs", "flutter-apk")
        os.makedirs(self.apk_dir, exist_ok=True)
        self.apk_path = os.path.join(self.apk_dir, "app-debug.apk")
        with open(self.apk_path, "wb") as f:
            f.write(b"APK_DUMMY_BINARY_DATA_CONTENT_TEST")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _create_p5_report(self, status="VERIFIED", device_status="BLOCKED"):
        self._write_json(os.path.join(self.workspace, "runtime_verification_report.json"), {
            "status": status,
            "android": {"device": device_status, "apk_build": "PASS", "runtime": device_status}
        })

    def test_1_phase5_verified_starts_phase6(self):
        """TEST 1: Phase 5 VERIFIED → Phase 6 starts."""
        self._create_p5_report("VERIFIED")
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertIn(res.get("status"), ["READY", "READY_WITH_WARNINGS"])

    def test_2_phase5_failed_blocks_phase6(self):
        """TEST 2: Phase 5 FAILED → Phase 6 blocked."""
        self._create_p5_report("FAILED")
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("status"), "HANDOFF_BLOCKED")

    def test_3_final_workspace_structure_verification(self):
        """TEST 3: Final workspace structure verification."""
        self._create_p5_report("VERIFIED")
        os.remove(os.path.join(self.workspace, "architecture_plan.json"))
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("status"), "HANDOFF_BLOCKED")

    def test_4_implementation_manifest_file_verification(self):
        """TEST 4: Implementation manifest file verification."""
        self._create_p5_report("VERIFIED")
        os.remove(os.path.join(self.frontend, "pubspec.yaml"))
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("status"), "HANDOFF_BLOCKED")

    def test_5_apk_artifact_discovery(self):
        """TEST 5: APK artifact discovery."""
        artifacts = ReleaseArtifactManager.discover_artifacts(self.workspace)
        self.assertTrue(len(artifacts) > 0)
        self.assertTrue(any(a["type"] == "APK_DEBUG" for a in artifacts))

    def test_6_apk_zero_byte_artifact_rejected(self):
        """TEST 6: APK zero-byte artifact rejected."""
        zero_apk = os.path.join(self.apk_dir, "app-release.apk")
        with open(zero_apk, "wb") as f:
            pass  # 0 bytes
        artifacts = ReleaseArtifactManager.discover_artifacts(self.workspace)
        rel_art = [a for a in artifacts if a["type"] == "APK_RELEASE"][0]
        self.assertFalse(rel_art["verified"])

    def test_7_apk_checksum_generation(self):
        """TEST 7: APK checksum generation."""
        sha256 = ReleaseArtifactManager.calculate_sha256(self.apk_path)
        self.assertTrue(len(sha256) == 64)

    def test_8_node_backend_release_readiness(self):
        """TEST 8: Node backend release readiness."""
        self._create_p5_report("VERIFIED")
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("backend_readiness"), "PASS")

    def test_9_api_contract_final_validation(self):
        """TEST 9: API contract final validation."""
        self._create_p5_report("VERIFIED")
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("api_contract_validation"), "PASS")

    def test_10_missing_required_environment_config(self):
        """TEST 10: Missing required environment configuration detected."""
        with open(os.path.join(self.workspace, ".env"), "w") as f:
            f.write("DB_PASSWORD=your_password_here\nSECRET_KEY=placeholder_token\n")
        orch = AppFinalizationOrchestrator()
        env_audit = orch._audit_environment_config(self.workspace)
        self.assertTrue(len(env_audit["warnings"]) > 0)

    def test_11_secrets_not_exposed_in_reports(self):
        """TEST 11: Secrets are not exposed in reports."""
        with open(os.path.join(self.workspace, ".env"), "w") as f:
            f.write("DB_PASSWORD=SuperSecretPass123!\n")
        orch = AppFinalizationOrchestrator()
        env_audit = orch._audit_environment_config(self.workspace)
        report_str = str(env_audit)
        self.assertNotIn("SuperSecretPass123!", report_str)

    def test_12_release_manifest_generated(self):
        """TEST 12: Release manifest generated."""
        self._create_p5_report("VERIFIED")
        orch = AppFinalizationOrchestrator()
        orch.finalize_app(self.workspace, "app123")
        self.assertTrue(os.path.exists(os.path.join(self.workspace, "release_manifest.json")))

    def test_13_final_release_report_generated(self):
        """TEST 13: Final release report generated."""
        self._create_p5_report("VERIFIED")
        orch = AppFinalizationOrchestrator()
        orch.finalize_app(self.workspace, "app123")
        self.assertTrue(os.path.exists(os.path.join(self.workspace, "final_release_report.json")))
        self.assertTrue(os.path.exists(os.path.join(self.workspace, "FINAL_RELEASE_REPORT.md")))

    def test_14_ready_status_generated_when_all_pass(self):
        """TEST 14: READY status generated when all mandatory checks pass & device present."""
        self._create_p5_report("VERIFIED", device_status="PASS")
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("status"), "READY")

    def test_15_ready_with_warnings_for_non_critical_device_absence(self):
        """TEST 15: READY_WITH_WARNINGS generated for non-critical device absence."""
        self._create_p5_report("VERIFIED", device_status="BLOCKED")
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("status"), "READY_WITH_WARNINGS")

    def test_16_blocked_status_for_api_mismatch(self):
        """TEST 16: BLOCKED status generated for API mismatch."""
        self._create_p5_report("VERIFIED")
        # Inject API mismatch in contract that route validator will flag
        self._write_json(os.path.join(self.workspace, "api_contract.json"), {
            "routes": [{"path": "/api/nonexistent_route_1234", "method": "POST"}]
        })
        orch = AppFinalizationOrchestrator()
        res = orch.finalize_app(self.workspace, "app123")
        self.assertEqual(res.get("status"), "HANDOFF_BLOCKED")

    def test_17_crash_recovery_resumes_stage(self):
        """TEST 17: Crash recovery resumes from last Phase 6 stage."""
        orch = AppFinalizationOrchestrator()
        orch._save_phase6_state(self.workspace, "ARTIFACT_DISCOVERY", {"test": 1})
        state_file = os.path.join(self.workspace, "phase6_state.json")
        self.assertTrue(os.path.exists(state_file))
        with open(state_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data.get("state"), "ARTIFACT_DISCOVERY")

    def test_18_requirement_version_change_invalidates_finalization(self):
        """TEST 18: Requirement/version change invalidates old finalization."""
        self._create_p5_report("VERIFIED")
        orch = AppFinalizationOrchestrator()
        orch.finalize_app(self.workspace, "app123")
        self.assertFalse(orch.is_finalization_invalidated(self.workspace))

        # Touch architecture_plan.json to simulate re-planning
        import time
        time.sleep(0.01)
        with open(os.path.join(self.workspace, "architecture_plan.json"), "a") as f:
            f.write("\n")
        self.assertTrue(orch.is_finalization_invalidated(self.workspace))

    def test_19_no_unrelated_files_deleted(self):
        """TEST 19: No unrelated files are deleted."""
        custom_file = os.path.join(self.workspace, "user_asset.png")
        with open(custom_file, "w") as f:
            f.write("DATA")
        orch = AppFinalizationOrchestrator()
        orch._cleanup_temporary_artifacts(self.workspace)
        self.assertTrue(os.path.exists(custom_file))

    @unittest.skipUnless(HAS_WEBSOCKET, "fastapi not installed")
    @patch("api.websocket.jarvis.broadcast_sync")
    def test_20_websocket_finalization_events_emitted(self, mock_ws):
        """TEST 20: WebSocket finalization events emitted."""
        self._create_p5_report("VERIFIED")
        orch = AppFinalizationOrchestrator()
        orch.finalize_app(self.workspace, "app123")
        self.assertTrue(mock_ws.called)


if __name__ == "__main__":
    unittest.main()
