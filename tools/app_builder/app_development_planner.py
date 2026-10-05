"""
tools/app_builder/app_development_planner.py
Phase 2 & Phase 3 — Master Architecture & Development Plan Generator.
Consumes AppRequirementsAnalyzer and ArchitecturePlanner to generate complete, machine-readable Phase 3 plans.
"""
import logging
from typing import Dict, Any, List, Optional
from tools.app_builder.app_model import AppBrief
from tools.app_builder.app_requirements_analyzer import AppRequirementsAnalyzer, MissingRequirementDetector
from tools.app_builder.architecture_planner import ArchitecturePlanner

logger = logging.getLogger("AppDevelopmentPlanner")


class AppDevelopmentPlanner:
    """
    Transforms an AppBrief into a structured, machine-readable Phase 3 ArchitecturePlan
    covering requirements analysis, missing requirement detection, screen blueprints, Flutter architecture,
    Node.js backend controllers, shared API contracts, database schemas, UI plans, dependencies, and implementation ordering.
    """

    @classmethod
    def generate_plan(cls, brief: AppBrief, app_id: str = "app_default", brief_version: int = 1) -> Dict[str, Any]:
        """
        Generates full Phase 3 ArchitecturePlan dictionary.
        """
        # 1. App Requirement Analysis (Phase 3.1)
        analyzed_reqs = AppRequirementsAnalyzer.analyze(brief)

        # 2. Missing Requirement Detection (Phase 3.2)
        readiness_check = MissingRequirementDetector.check_requirements(analyzed_reqs, brief)
        analyzed_reqs["readiness_check"] = readiness_check

        # 3. Comprehensive Architecture Plan (Phase 3.3 - 3.11)
        full_arch_plan = ArchitecturePlanner.create_architecture_plan(
            app_id=app_id,
            analyzed_reqs=analyzed_reqs,
            brief_version=brief_version,
            plan_version=1
        )

        # Legacy backward-compatibility fields expected by Phase 2 callers
        full_arch_plan["app_name"] = analyzed_reqs.get("app_name")
        full_arch_plan["sanitized_name"] = "".join(c for c in (analyzed_reqs.get("app_name") or "JarvisApp") if c.isalnum() or c == "_")
        full_arch_plan["domain"] = analyzed_reqs.get("domain")
        full_arch_plan["theme"] = analyzed_reqs.get("ui_design_requirements", {}).get("theme", "Dark Blue Theme")
        full_arch_plan["features"] = analyzed_reqs.get("core_features")

        # Map legacy flutter/node top-level references
        full_arch_plan["flutter"] = dict(full_arch_plan.get("flutter_plan", {}))
        full_arch_plan["node"] = dict(full_arch_plan.get("node_plan", {}))
        full_arch_plan["node"]["endpoints"] = full_arch_plan.get("api_contract", {}).get("endpoints", [])
        
        flutter_dep_pkgs = [d["package"] for d in full_arch_plan.get("dependencies", {}).get("flutter", []) if isinstance(d, dict)]
        node_dep_pkgs = [d["package"] for d in full_arch_plan.get("dependencies", {}).get("node", []) if isinstance(d, dict)]
        
        full_arch_plan["flutter"]["packages"] = flutter_dep_pkgs or ["http", "provider", "shared_preferences", "intl"]
        full_arch_plan["node"]["packages"] = node_dep_pkgs or ["express", "cors", "dotenv", "morgan"]

        logger.info(f"Generated Phase 3 ArchitecturePlan for app_id={app_id} (status={readiness_check['status']})")
        return full_arch_plan
