"""
tools/app_builder/feature_coverage_analyzer.py
Phase 14 — Feature Coverage Analyzer & Matrix Generator.
Audits required application features against generated physical source code and constructs `FEATURE_COVERAGE_REPORT`.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from tools.app_builder.app_specification import ApplicationSpecification

logger = logging.getLogger("FeatureCoverageAnalyzer")


class FeatureCoverageAnalyzer:
    """
    Audits physical code generation against target ApplicationSpecification features.
    """

    @classmethod
    def analyze_coverage(cls, workspace_path: str, spec: Optional[ApplicationSpecification] = None) -> Dict[str, Any]:
        """
        Audits workspace files against specification and produces feature coverage matrix.
        """
        abs_workspace = os.path.abspath(workspace_path)
        
        # Load ApplicationSpecification if not provided
        if not spec:
            spec_file = os.path.join(abs_workspace, "application_specification.json")
            if os.path.exists(spec_file):
                try:
                    with open(spec_file, "r", encoding="utf-8") as f:
                        spec = ApplicationSpecification.from_dict(json.load(f))
                except Exception:
                    pass

        if not spec:
            spec = ApplicationSpecification(app_name="JARVIS Application")

        frontend_lib = os.path.join(abs_workspace, "frontend", "lib")
        backend_src = os.path.join(abs_workspace, "backend", "src")

        all_code = ""
        for d in [frontend_lib, backend_src]:
            if os.path.exists(d):
                for root, _, files in os.walk(d):
                    for file in files:
                        if file.endswith((".dart", ".js", ".ts", ".yaml", ".json")):
                            try:
                                with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                                    all_code += f.read().lower() + "\n"
                            except Exception:
                                pass

        features_matrix = []
        overall_pass = True

        # Standard Core Feature Audit Checks
        standard_features = [
            ("Authentication", ["login", "auth", "token", "user"]),
            ("Home / Dashboard", ["home", "dashboard", "main"]),
            ("Navigation", ["materialapp", "navigator", "route", "bottomnavigationbar", "appbar"]),
            ("Backend API Integration", ["http", "api", "baseurl", "fetch", "express", "get", "post"]),
            ("Database Persistence", ["json", "store", "model", "schema", "sharedpreferences", "sqlite"]),
            ("Error Handling & Validation", ["try", "catch", "error", "validator", "exception"])
        ]

        # Domain Specific Core Feature Checks
        if spec.domain == "music":
            standard_features.extend([
                ("Music Search", ["search", "query", "genre"]),
                ("Audio Player Controls", ["player", "song", "audio", "artist", "duration"]),
                ("Playlist Management", ["playlist", "liked", "track"])
            ])
        elif spec.domain == "weather":
            standard_features.extend([
                ("Forecast Display", ["forecast", "temp", "hourly", "daily"]),
                ("City Search", ["search", "city", "location"])
            ])
        elif spec.domain == "expense":
            standard_features.extend([
                ("Expense Analytics & Charts", ["analytics", "chart", "balance", "category"]),
                ("Add Transaction Form", ["add", "transaction", "amount", "income"])
            ])
        elif spec.domain == "product":
            standard_features.extend([
                ("Product Catalog Grid", ["catalog", "product", "price"]),
                ("Shopping Cart & Checkout", ["cart", "checkout", "order"])
            ])

        for feat_name, keywords in standard_features:
            covered = any(kw in all_code for kw in keywords)
            status = "PASS" if covered else "FAIL"
            if status == "FAIL":
                overall_pass = False
            features_matrix.append({
                "feature": feat_name,
                "keywords": keywords,
                "status": status
            })

        # Custom Core Features from Spec
        for user_feat in spec.core_features:
            kw = user_feat.lower()
            covered = (kw in all_code) or any(w in all_code for w in kw.split() if len(w) > 3)
            status = "PASS" if covered else "WARN"
            features_matrix.append({
                "feature": f"Spec Feature: {user_feat}",
                "keywords": [kw],
                "status": status
            })

        report = {
            "status": "PASS" if overall_pass else "FAIL",
            "passed": overall_pass,
            "domain": spec.domain,
            "total_features": len(features_matrix),
            "passed_count": len([f for f in features_matrix if f["status"] == "PASS"]),
            "failed_count": len([f for f in features_matrix if f["status"] == "FAIL"]),
            "matrix": features_matrix
        }

        # Write feature_coverage_report.json
        report_file = os.path.join(abs_workspace, "feature_coverage_report.json")
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"[FEATURE_COVERAGE] status={report['status']} passed={report['passed_count']}/{report['total_features']}")
        except Exception as ex:
            logger.error(f"Failed writing feature_coverage_report.json: {ex}")

        return report

    evaluate = analyze_coverage
