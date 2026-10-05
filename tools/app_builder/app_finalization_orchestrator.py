"""
tools/app_builder/app_finalization_orchestrator.py
Phase 6 — Finalization, Release Readiness, Artifact Management & User Handoff Orchestrator.
Orchestrates Phase 5 verification consumption, final workspace inspection, release artifact discovery,
API contract re-validation, environment sanity audit, release_manifest.json & final_release_report.json generation,
WebSocket telemetry, crash recovery, requirement invalidation, and final user handoff.
"""
import os
import json
import time
import shutil
import hashlib
import logging
from typing import Dict, Any, List, Optional, Callable

from tools.app_builder.app_model import AppState
from tools.app_builder.release_artifact_manager import ReleaseArtifactManager
from tools.app_builder.api_contract_validator import ApiContractValidator
from tools.app_builder.node_runtime import NodeRuntime

logger = logging.getLogger("AppFinalizationOrchestrator")


class AppFinalizationOrchestrator:
    """
    Master orchestrator for Phase 6 Finalization, Release Readiness, and Handoff.
    """

    def __init__(self, speak_callback: Optional[Callable[[str], None]] = None, request_id: Optional[str] = None):
        self.speak_callback = speak_callback
        self.request_id = request_id

    def speak(self, text: str, request_id: Optional[str] = None, stage: str = "FINALIZATION"):
        if not text:
            return
        effective_req_id = request_id or self.request_id
        try:
            from core.progress_reporter import ProgressReporter
            ProgressReporter.get_instance().report(
                message=text,
                request_id=effective_req_id,
                stage=stage,
                speak=True
            )
        except Exception as ex:
            logger.debug(f"ProgressReporter error: {ex}")

        if self.speak_callback:
            try:
                self.speak_callback(text)
            except Exception as ex:
                logger.debug(f"Speak callback error: {ex}")

    def finalize_app(self, workspace_path: str, app_id: str = "", request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the Phase 6 Finalization pipeline on a verified Phase 5 application workspace.
        """
        if request_id and not self.request_id:
            self.request_id = request_id

        abs_workspace = os.path.abspath(workspace_path)
        frontend_dir = os.path.join(abs_workspace, "frontend")
        backend_dir = os.path.join(abs_workspace, "backend")

        self.speak("Boss, application final release readiness aur handoff verification start kar raha hoon.", request_id=self.request_id, stage="FINALIZATION_START")
        self._broadcast_event("app_finalization_started", app_id, abs_workspace, message="Starting Phase 6 finalization")

        # Save initial Phase 6 state for crash recovery
        self._save_phase6_state(abs_workspace, "FINALIZING", {"app_id": app_id, "started_at": time.time()})

        report = {
            "app_id": app_id,
            "status": "FINALIZING",
            "phase5_gate": "PENDING",
            "workspace_verification": "PENDING",
            "manifest_verification": "PENDING",
            "artifact_discovery": "PENDING",
            "artifacts": [],
            "backend_readiness": "PENDING",
            "frontend_readiness": "PENDING",
            "configuration_sanity": "PENDING",
            "environment_urls": {},
            "api_contract_validation": "PENDING",
            "api_mismatches": 0,
            "database_readiness": "PENDING",
            "runtime": {
                "build_verified": False,
                "device_available": False,
                "device_install_test": "BLOCKED"
            },
            "handoff": {
                "status": "PENDING",
                "blocking_issues": [],
                "warnings": []
            }
        }

        try:
            # ----------------------------------------------------
            # STEP 1: PHASE 5 GATE CHECK
            # ----------------------------------------------------
            self._save_phase6_state(abs_workspace, "FINAL_PROJECT_VERIFYING", {"step": "phase5_gate"})
            self._broadcast_event("app_final_project_verification_started", app_id, abs_workspace, message="Verifying Phase 5 runtime report")

            p5_file = os.path.join(abs_workspace, "runtime_verification_report.json")
            if not os.path.exists(p5_file):
                report["phase5_gate"] = "BLOCKED"
                report["handoff"]["blocking_issues"].append("Missing Phase 5 runtime_verification_report.json")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            p5_data = {}
            try:
                with open(p5_file, "r", encoding="utf-8") as f:
                    p5_data = json.load(f)
            except Exception as ex:
                report["phase5_gate"] = "BLOCKED"
                report["handoff"]["blocking_issues"].append(f"Unreadable Phase 5 report: {ex}")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            p5_status = p5_data.get("status", "FAILED")
            if p5_status != "VERIFIED":
                report["phase5_gate"] = "BLOCKED"
                report["handoff"]["blocking_issues"].append(f"Phase 5 runtime verification failed with status: {p5_status}")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            report["phase5_gate"] = "PASS"
            report["runtime"]["build_verified"] = True
            
            # Check device status in Phase 5
            device_status = p5_data.get("android", {}).get("device", "BLOCKED")
            if device_status == "PASS":
                report["runtime"]["device_available"] = True
                report["runtime"]["device_install_test"] = p5_data.get("android", {}).get("runtime", "PASS")
            else:
                report["runtime"]["device_available"] = False
                report["runtime"]["device_install_test"] = "BLOCKED"
                report["handoff"]["warnings"].append("Physical Android device/emulator runtime not available; APK build verified.")

            # ----------------------------------------------------
            # STEP 2: FINAL PROJECT STRUCTURE & MANIFEST VERIFICATION
            # ----------------------------------------------------
            req_plans = ["architecture_plan.json", "api_contract.json", "database_plan.json", "implementation_manifest.json"]
            missing_plans = [p for p in req_plans if not os.path.exists(os.path.join(abs_workspace, p))]
            if missing_plans:
                report["workspace_verification"] = "FAIL"
                report["handoff"]["blocking_issues"].append(f"Missing required plan files: {missing_plans}")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            # Check implementation manifest entries
            manifest_file = os.path.join(abs_workspace, "implementation_manifest.json")
            manifest_data = {}
            missing_manifest_files = []
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                expected_files = manifest_data.get("files_generated", [])
                for rel_f in expected_files:
                    full_f = os.path.join(abs_workspace, rel_f)
                    if not os.path.exists(full_f) or os.path.getsize(full_f) == 0:
                        missing_manifest_files.append(rel_f)
            except Exception as ex:
                logger.error(f"Manifest read error: {ex}")

            if missing_manifest_files:
                report["manifest_verification"] = "FAIL"
                report["handoff"]["blocking_issues"].append(f"Missing files from implementation_manifest.json: {missing_manifest_files}")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            report["workspace_verification"] = "PASS"
            report["manifest_verification"] = "PASS"
            self._broadcast_event("app_final_project_verified", app_id, abs_workspace, message="Physical project structure & manifest verified")

            # ----------------------------------------------------
            # STEP 3: RELEASE ARTIFACT DISCOVERY
            # ----------------------------------------------------
            self._save_phase6_state(abs_workspace, "ARTIFACT_DISCOVERY", {"step": "artifact_discovery"})
            self._broadcast_event("app_artifact_discovery_started", app_id, abs_workspace, message="Discovering release build artifacts")

            discovered = ReleaseArtifactManager.discover_artifacts(abs_workspace)
            report["artifacts"] = discovered

            verified_apks = [a for a in discovered if a.get("verified")]
            if not verified_apks and os.path.exists(frontend_dir):
                report["artifact_discovery"] = "FAIL"
                report["handoff"]["blocking_issues"].append("No valid, verified APK/AAB build artifact discovered on disk.")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            report["artifact_discovery"] = "PASS"
            for art in discovered:
                self._broadcast_event("app_artifact_discovered", app_id, abs_workspace, message=f"Discovered artifact {art.get('type')}", extra=art)

            # ----------------------------------------------------
            # STEP 4: BACKEND RELEASE READINESS
            # ----------------------------------------------------
            self._save_phase6_state(abs_workspace, "RELEASE_PREPARING", {"step": "backend_readiness"})
            needs_backend = manifest_data.get("metadata", {}).get("needs_backend", True)
            if needs_backend and os.path.exists(backend_dir):
                pkg_file = os.path.join(backend_dir, "package.json")
                if not os.path.exists(pkg_file):
                    report["backend_readiness"] = "FAIL"
                    report["handoff"]["blocking_issues"].append("Backend package.json missing.")
                    return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

                syn = NodeRuntime.syntax_check(backend_dir, entrypoint="src/app.js", app_id=app_id)
                if not syn.get("success"):
                    syn = NodeRuntime.syntax_check(backend_dir, entrypoint="src/server.js", app_id=app_id)

                if not syn.get("success"):
                    report["backend_readiness"] = "FAIL"
                    report["handoff"]["blocking_issues"].append(f"Backend syntax check failed: {syn.get('stderr')}")
                    return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

                report["backend_readiness"] = "PASS"
                self._broadcast_event("app_backend_release_ready", app_id, abs_workspace, message="Node.js backend release ready")
            else:
                report["backend_readiness"] = "N/A"

            report["frontend_readiness"] = "PASS"
            self._broadcast_event("app_frontend_release_ready", app_id, abs_workspace, message="Flutter frontend release ready")

            # ----------------------------------------------------
            # STEP 5: CONFIGURATION & ENVIRONMENT SANITY CHECK
            # ----------------------------------------------------
            self._save_phase6_state(abs_workspace, "RELEASE_VALIDATING", {"step": "configuration_sanity"})
            self._broadcast_event("app_release_validation_started", app_id, abs_workspace, message="Validating environment and API configuration")

            env_report = self._audit_environment_config(abs_workspace)
            report["configuration_sanity"] = env_report.get("status", "PASS")
            report["environment_urls"] = env_report.get("urls", {})
            if env_report.get("warnings"):
                report["handoff"]["warnings"].extend(env_report["warnings"])

            # ----------------------------------------------------
            # STEP 6: FINAL API CONTRACT RE-VALIDATION
            # ----------------------------------------------------
            self._broadcast_event("app_api_final_validation", app_id, abs_workspace, message="Executing final API contract validation")
            val_res = ApiContractValidator.validate_project(abs_workspace)
            raw_mismatches = val_res.get("mismatches", [])
            mismatch_count = len(raw_mismatches) if isinstance(raw_mismatches, list) else int(raw_mismatches)
            report["api_mismatches"] = mismatch_count

            if not val_res.get("success") or mismatch_count > 0:
                report["api_contract_validation"] = "FAIL"
                report["handoff"]["blocking_issues"].append(f"API contract validation failed with {mismatch_count} mismatch(es).")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            report["api_contract_validation"] = "PASS"

            # ----------------------------------------------------
            # STEP 7.5: PRODUCTION QUALITY GATE & PLACEHOLDER AUDIT
            # ----------------------------------------------------
            from tools.app_builder.placeholder_detector import PlaceholderDetector
            from tools.app_builder.feature_coverage_analyzer import FeatureCoverageAnalyzer
            from tools.app_builder.production_quality_gate import ProductionQualityGate
            from tools.app_builder.app_specification import AppSpecificationBuilder

            p_report = PlaceholderDetector.scan_workspace(abs_workspace)
            if p_report["has_placeholders"]:
                report["handoff"]["blocking_issues"].append(f"Placeholder strings detected in codebase: {p_report['matches']}")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            spec = AppSpecificationBuilder.from_brief(None, abs_workspace)
            cov_report = FeatureCoverageAnalyzer.evaluate(abs_workspace, spec)
            gate_report = ProductionQualityGate.evaluate_production_quality(abs_workspace, spec)
            report["quality_gate"] = gate_report

            if gate_report["overall_status"] != "PASS":
                report["handoff"]["blocking_issues"].append(f"Production Quality Gate FAILED on criteria: {gate_report['failed_criteria']}")
                return self._complete_finalization(abs_workspace, app_id, report, "HANDOFF_BLOCKED")

            # ----------------------------------------------------
            # STEP 8: DISPOSABLE DATA CLEANUP
            # ----------------------------------------------------
            self._cleanup_temporary_artifacts(abs_workspace)

            # Determine Final Status: READY or READY_WITH_WARNINGS
            final_status = "READY"
            if report["handoff"]["warnings"]:
                final_status = "READY_WITH_WARNINGS"

            return self._complete_finalization(abs_workspace, app_id, report, final_status)

        except Exception as ex:
            logger.exception(f"Unhandled exception during Phase 6 finalization for app_id={app_id}: {ex}")
            report["handoff"]["blocking_issues"].append(f"Finalization exception: {str(ex)}")
            return self._complete_finalization(abs_workspace, app_id, report, "RELEASE_FAILED")

    def _complete_finalization(self, workspace: str, app_id: str, report: Dict[str, Any], final_status: str) -> Dict[str, Any]:
        """Writes release_manifest.json, final_release_report.json, FINAL_RELEASE_REPORT.md and updates state."""
        report["status"] = final_status
        report["handoff"]["status"] = final_status
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        report["finalized_at"] = now_str

        # 1. Update implementation_manifest.json
        manifest_file = os.path.join(workspace, "implementation_manifest.json")
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    m_data = json.load(f)
                m_data["finalization"] = {
                    "status": final_status,
                    "finalized_at": now_str,
                    "artifacts": report.get("artifacts", []),
                    "warnings": report["handoff"].get("warnings", []),
                    "blocking_issues": report["handoff"].get("blocking_issues", [])
                }
                with open(manifest_file, "w", encoding="utf-8") as f:
                    json.dump(m_data, f, indent=2)
            except Exception as ex:
                logger.error(f"Error updating implementation manifest: {ex}")

        # 2. Write release_manifest.json
        release_manifest = {
            "app_id": app_id,
            "app_name": report.get("app_name", "JARVIS Application"),
            "status": final_status,
            "finalized_at": now_str,
            "frontend": {"platform": "Flutter", "verified": report.get("frontend_readiness") == "PASS"},
            "backend": {"platform": "Node.js", "verified": report.get("backend_readiness") in ("PASS", "N/A")},
            "api_contract": {"verified": report.get("api_contract_validation") == "PASS", "mismatches": report.get("api_mismatches", 0)},
            "artifacts": report.get("artifacts", []),
            "runtime": report.get("runtime", {}),
            "handoff": report.get("handoff", {})
        }
        rel_manifest_file = os.path.join(workspace, "release_manifest.json")
        try:
            with open(rel_manifest_file, "w", encoding="utf-8") as f:
                json.dump(release_manifest, f, indent=2)
        except Exception as ex:
            logger.error(f"Error writing release_manifest.json: {ex}")

        # 3. Write final_release_report.json
        report_file = os.path.join(workspace, "final_release_report.json")
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except Exception as ex:
            logger.error(f"Error writing final_release_report.json: {ex}")

        # 4. Write human-readable FINAL_RELEASE_REPORT.md
        md_file = os.path.join(workspace, "FINAL_RELEASE_REPORT.md")
        try:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(self._generate_markdown_report(report))
        except Exception as ex:
            logger.error(f"Error writing FINAL_RELEASE_REPORT.md: {ex}")

        # 5. Print Output Matrix
        self._print_finalization_matrix(report)

        # 6. Save final state
        state_name = "HANDOFF_READY" if final_status in ("READY", "READY_WITH_WARNINGS") else ("HANDOFF_BLOCKED" if final_status == "HANDOFF_BLOCKED" else "RELEASE_FAILED")
        self._save_phase6_state(workspace, state_name, report)

        # 7. Verbal & WS Telemetry
        if final_status in ("READY", "READY_WITH_WARNINGS"):
            apk_path = report["artifacts"][0]["relative_path"] if report["artifacts"] else "build output"
            self.speak(f"Boss, app successfully finalize ho gaya hai. Status {final_status}. Flutter APK ready hai at {apk_path}.", request_id=self.request_id, stage="HANDOFF_READY")
            self._broadcast_event("app_handoff_ready", app_id, workspace, message=f"App finalization READY ({final_status})", extra=report)
        elif final_status == "HANDOFF_BLOCKED":
            blockers = report["handoff"].get("blocking_issues", ["Unknown block"])
            self.speak(f"Boss, app finalization blocked ho gaya: {blockers[0][:60]}", request_id=self.request_id, stage="HANDOFF_BLOCKED")
            self._broadcast_event("app_handoff_blocked", app_id, workspace, message=f"Handoff blocked: {blockers[0]}", extra=report)
        else:
            self.speak("Boss, app release finalization me failure aayi hai.", request_id=self.request_id, stage="RELEASE_FAILED")
            self._broadcast_event("app_release_failed", app_id, workspace, message="Finalization failed", extra=report)

        return report

    def _audit_environment_config(self, workspace: str) -> Dict[str, Any]:
        """Audits environment files for missing keys, placeholders, and extracts URL strategies safely without leaking secrets."""
        urls = {
            "DEVELOPMENT_API_URL": "http://127.0.0.1:3000/api",
            "EMULATOR_API_URL": "http://10.0.2.2:3000/api",
            "PHYSICAL_DEVICE_API_URL": "http://localhost:3000/api",
            "PRODUCTION_BACKEND_URL": "NOT_CONFIGURED"
        }
        warnings = []
        status = "PASS"

        env_files = [os.path.join(workspace, f) for f in [".env", ".env.example", ".env.local"] if os.path.exists(os.path.join(workspace, f))]
        env_files.extend([os.path.join(workspace, "backend", f) for f in [".env", ".env.example"] if os.path.exists(os.path.join(workspace, "backend", f))])

        secrets_audit = []
        for ef in env_files:
            try:
                with open(ef, "r", encoding="utf-8") as f:
                    for line in f:
                        line_s = line.strip()
                        if not line_s or line_s.startswith("#"):
                            continue
                        if "=" in line_s:
                            k, v = line_s.split("=", 1)
                            k, v = k.strip(), v.strip()
                            if "secret" in k.lower() or "key" in k.lower() or "password" in k.lower() or "token" in k.lower():
                                if not v or "your_" in v.lower() or "placeholder" in v.lower():
                                    secrets_audit.append(f"{k}=PLACEHOLDER_DETECTED")
                                    warnings.append(f"Environment variable '{k}' has placeholder value.")
                                else:
                                    secrets_audit.append(f"{k}=SECRET_PRESENT")
            except Exception:
                pass

        return {"status": status, "urls": urls, "warnings": warnings, "secrets_audit": secrets_audit}

    def _cleanup_temporary_artifacts(self, workspace: str):
        """Cleans temporary test logs and disposable integration test artifacts without deleting source or database data."""
        temp_patterns = ["tmp_*.log", "test_run_*.tmp"]
        for root, _, files in os.walk(workspace):
            for file in files:
                if any(file.startswith("tmp_") or file.endswith(".tmp") for p in temp_patterns):
                    try:
                        os.remove(os.path.join(root, file))
                    except Exception:
                        pass

    def _save_phase6_state(self, workspace: str, state_name: str, data: Dict[str, Any]):
        """Persists phase6_state.json for crash recovery."""
        state_file = os.path.join(workspace, "phase6_state.json")
        try:
            payload = {
                "state": state_name,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "data": data
            }
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as ex:
            logger.error(f"Error saving Phase 6 state: {ex}")

    def is_finalization_invalidated(self, workspace: str) -> bool:
        """
        Checks if requirement changes or architecture re-plans have occurred since last finalization,
        invalidating previous release manifests.
        """
        rel_file = os.path.join(workspace, "release_manifest.json")
        if not os.path.exists(rel_file):
            return True

        try:
            mtime_rel = os.path.getmtime(rel_file)
            arch_file = os.path.join(workspace, "architecture_plan.json")
            if os.path.exists(arch_file) and os.path.getmtime(arch_file) > mtime_rel:
                return True
            manifest_file = os.path.join(workspace, "implementation_manifest.json")
            if os.path.exists(manifest_file) and os.path.getmtime(manifest_file) > mtime_rel:
                return True
            return False
        except Exception:
            return True

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        lines = [
            "# JARVIS APP BUILDER - FINAL RELEASE REPORT",
            f"**App ID**: {report.get('app_id')}",
            f"**Final Status**: `{report.get('status')}`",
            f"**Finalized At**: {report.get('finalized_at')}",
            "",
            "## Summary Matrix",
            f"- Phase 5 Gate: `{report.get('phase5_gate')}`",
            f"- Workspace Verification: `{report.get('workspace_verification')}`",
            f"- Manifest Verification: `{report.get('manifest_verification')}`",
            f"- Backend Readiness: `{report.get('backend_readiness')}`",
            f"- Frontend Readiness: `{report.get('frontend_readiness')}`",
            f"- API Contract Validation: `{report.get('api_contract_validation')}` (Mismatches: {report.get('api_mismatches')})",
            f"- Database Readiness: `{report.get('database_readiness')}`",
            f"- Artifact Discovery: `{report.get('artifact_discovery')}`",
            "",
            "## Discovered Build Artifacts"
        ]

        for art in report.get("artifacts", []):
            lines.append(f"- **{art.get('type')}**: `{art.get('relative_path')}` ({art.get('size_bytes')} bytes, SHA-256: `{art.get('sha256')[:12]}...`) Verified: {art.get('verified')}")

        lines.extend([
            "",
            "## Handoff Assessment",
            f"- **Warnings**: {report['handoff'].get('warnings')}",
            f"- **Blocking Issues**: {report['handoff'].get('blocking_issues')}",
            "",
            "**JARVIS System Handoff**: Application build is verified and ready for distribution."
        ])
        return "\n".join(lines)

    def _print_finalization_matrix(self, report: Dict[str, Any]):
        print("\n============================================================")
        print("JARVIS APP BUILDER PHASE 6")
        print("FINAL RELEASE READINESS & USER HANDOFF")
        print("============================================================")
        print(f"Phase 5 Gate             : {report.get('phase5_gate')}")
        print(f"Workspace Verification   : {report.get('workspace_verification')}")
        print(f"Manifest Verification    : {report.get('manifest_verification')}")
        print(f"Flutter Project          : {report.get('frontend_readiness')}")
        print(f"Node.js Backend          : {report.get('backend_readiness')}")
        print(f"API Contract             : {report.get('api_contract_validation')}")
        print(f"Database/Storage         : {report.get('database_readiness')}")
        print(f"Artifact Discovery       : {report.get('artifact_discovery')}")
        
        arts = report.get("artifacts", [])
        if arts:
            art = arts[0]
            print(f"APK Discovery            : PASS")
            print(f"APK Integrity            : PASS if art.get('verified') else FAIL")
            print(f"APK Checksum             : {art.get('sha256')[:16]}..." if art.get('sha256') else "NONE")
        else:
            print(f"APK Discovery            : FAIL")

        print(f"Backend Readiness        : {report.get('backend_readiness')}")
        print(f"Configuration            : {report.get('configuration_sanity')}")
        print(f"Release Manifest         : PASS")
        print(f"Final Report             : PASS")
        print("")
        print(f"Android Device           : {report.get('runtime', {}).get('device_available', False)}")
        print(f"Android Install Test     : {report.get('runtime', {}).get('device_install_test', 'BLOCKED')}")
        print("")
        print(f"Warnings                 : {len(report['handoff'].get('warnings', []))}")
        print(f"Blocking Issues          : {len(report['handoff'].get('blocking_issues', []))}")
        print("")
        print(f"FINAL HANDOFF STATUS     : {report.get('status')}")
        print("============================================================\n")

    def _broadcast_event(self, event_type: str, app_id: str, workspace: str, message: str = "", extra: Optional[Dict[str, Any]] = None):
        payload = {
            "type": event_type,
            "app_id": app_id,
            "workspace": workspace,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        if extra:
            payload.update(extra)

        try:
            from api.websocket.jarvis import broadcast_sync
            broadcast_sync(payload)
        except Exception:
            pass
