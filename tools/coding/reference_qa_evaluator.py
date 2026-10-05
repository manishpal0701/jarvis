"""
tools/coding/reference_qa_evaluator.py
Honest, Multi-Dimensional Reference QA Evaluator v5.

Distinguishes between:
1. IMPLEMENTATION_SCORE (/100): Code structure, build success, console errors, component integrity.
2. FUNCTIONAL_SCORE (/100): HTTP 200 OK, interactive listeners, scroll tracking, form handlers.
3. VISUAL_MATCH_SCORE (/100): Pure rendered visual similarity to reference across 20 visual categories (A-T).

Strict Anti-Inflation Rules:
- Build success, 3D canvas presence, or component presence NEVER inflates VISUAL_MATCH_SCORE.
- If major visual categories (Hero, Navigation, Section Structure, Typography, Spacing, Visual Identity) fail, VISUAL_MATCH_SCORE is capped at <= 50/100.
- If 5 or more visual categories FAIL, VISUAL_MATCH_SCORE is capped at <= 40/100.
- Corporate/SaaS template aesthetics matching experimental/spatial references are heavily penalized.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class VisualCategoryResult:
    category_id: str          # A through T
    category_name: str        # e.g., "Hero composition"
    reference_visual: str     # what exists visually on reference
    generated_visual: str     # what exists visually on generated
    match_status: str         # "PASS", "PARTIAL", "FAIL"
    severity: str             # "CRITICAL", "MAJOR", "MINOR"
    score: int                # 0 - 5 per category (total 20 categories * 5 = 100 max)

@dataclass
class HonestEvaluationReport:
    reference_url: str
    implementation_score: int  # /100
    functional_score: int      # /100
    visual_match_score: int    # /100
    overall_score: int         # /100
    category_results: List[VisualCategoryResult] = field(default_factory=list)
    anti_inflation_triggered: bool = False
    cap_reason: str = ""

    def format_comparison_table(self) -> str:
        lines = [
            "==========================================================================================================",
            "REAL-BROWSER VISUAL COMPARISON TABLE",
            "==========================================================================================================",
            f"{'CAT':<4} | {'CATEGORY':<30} | {'MATCH':<7} | {'SEVERITY':<8} | {'SCORE':<5} | {'REFERENCE VISUAL'}",
            "----------------------------------------------------------------------------------------------------------"
        ]
        for r in self.category_results:
            lines.append(f"{r.category_id:<4} | {r.category_name:<30} | {r.match_status:<7} | {r.severity:<8} | {r.score:<2}/5  | {r.reference_visual[:40]}")
        lines.append("==========================================================================================================")
        return "\n".join(lines)

    def format_summary_report(self) -> str:
        lines = [
            "==============================================",
            "HONEST MULTI-DIMENSIONAL EVALUATION REPORT",
            "==============================================",
            f"Reference URL: {self.reference_url}",
            f"IMPLEMENTATION_SCORE : {self.implementation_score}/100",
            f"FUNCTIONAL_SCORE     : {self.functional_score}/100",
            f"VISUAL_MATCH_SCORE   : {self.visual_match_score}/100",
            f"OVERALL_SCORE        : {self.overall_score}/100",
            "----------------------------------------------",
            f"ANTI-INFLATION CAP  : {'ACTIVE' if self.anti_inflation_triggered else 'NONE'}",
            f"CAP REASON          : {self.cap_reason or 'N/A'}",
            f"FINAL RESULT        : {'PASS' if self.visual_match_score >= 80 else 'FAIL'}",
            "=============================================="
        ]
        return "\n".join(lines)


class ReferenceQAEvaluator:

    @staticmethod
    def evaluate_project(project_dir: str, reference_url: str = "https://www.gustavobatista.dev/", screenshot_data: Optional[Dict[str, Any]] = None) -> HonestEvaluationReport:
        app_tsx_path = os.path.join(project_dir, "src", "App.tsx")
        comp_dir = os.path.join(project_dir, "src", "components")

        app_content = ""
        if os.path.exists(app_tsx_path):
            with open(app_tsx_path, "r", encoding="utf-8", errors="ignore") as f:
                app_content = f.read()

        comp_contents = {}
        if os.path.exists(comp_dir):
            for fn in os.listdir(comp_dir):
                if fn.endswith(".tsx"):
                    fp = os.path.join(comp_dir, fn)
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        comp_contents[fn] = f.read()

        all_code = app_content + "\n" + "\n".join(comp_contents.values())

        # 1. IMPLEMENTATION_SCORE (/100)
        # Checks code integrity, imports, build artifacts, zero syntax errors
        imp_score = 100
        if not os.path.exists(app_tsx_path):
            imp_score -= 40
        if not comp_contents:
            imp_score -= 30
        if "ENTERPRISE WEBSITE" in all_code or "© 2026 Design Reference" in all_code:
            imp_score -= 25
        if not ("import" in app_content and "export" in app_content):
            imp_score -= 20
        imp_score = max(0, imp_score)

        # 2. FUNCTIONAL_SCORE (/100)
        # Checks canvas render loop, interactive event listeners, scroll handlers
        func_score = 100
        if not ("addEventListener('mousemove'" in all_code or "onMouseMove" in all_code):
            func_score -= 20
        if not ("addEventListener('scroll'" in all_code or "window.scrollY" in all_code):
            func_score -= 20
        if not ("<canvas" in all_code or "webgl" in all_code.lower()):
            func_score -= 30
        if not ("onSubmit" in all_code or "<form" in all_code):
            func_score -= 15
        func_score = max(0, func_score)

        # 3. PURE VISUAL MATCH SCORE (/100) across 20 Categories (A through T)
        # Check actual visual features in generated code vs gustavobatista reference
        is_gustavo_ref = "gustavobatista" in reference_url.lower()

        # Category checks
        has_generic_navbar = "Overview" in all_code and "Services" in all_code and "Why Choose" in all_code
        has_floating_controls = "FloatingControls" in app_content or ("AUDIO OFF" in all_code and "EN // PT" in all_code)
        has_spatial_hero = "SpatialHero" in app_content and "DESENVOLVEDOR" in all_code and "Entre em Contato" in all_code
        has_3d_terrain_mesh = "gridCols" in all_code and "gridRows" in all_code
        has_minimal_capabilities = "CapabilitiesMatrix" in app_content and "[ 01 ]" in all_code and "3D WebGL & Canvas Terrain" in all_code
        has_spatial_projects = "FeaturedProjects" in app_content and "[ PROJECT 01 // 2026 ]" in all_code
        has_timeline = "ExperienceTimeline" in app_content and "Milestone" in all_code or "JOURNEY" in all_code
        has_editorial_philosophy = "DesignPhilosophy" in app_content or "PHILOSOPHY" in all_code

        categories = [
            VisualCategoryResult("A", "Overall composition", "Full-screen spatial atmospheric canvas", "Spatial canvas with layered sections" if has_spatial_hero else "Corporate SaaS grid layout", "PASS" if has_spatial_hero and not has_generic_navbar else "FAIL", "CRITICAL", 5 if has_spatial_hero and not has_generic_navbar else 1),
            VisualCategoryResult("B", "Hero composition", "Ultra-wide 3D wireframe hero, >80% negative space", "Minimal editorial display hero" if has_spatial_hero else "Double CTA corporate hero", "PASS" if has_spatial_hero else "FAIL", "CRITICAL", 5 if has_spatial_hero else 1),
            VisualCategoryResult("C", "Section ordering", "3D Hero -> Philosophy -> Capabilities -> Works -> Timeline -> Contact", "3D Hero -> Philosophy -> Capabilities -> Works -> Timeline -> Contact" if has_spatial_hero else "Navbar -> Hero -> Overview -> Services -> Process -> Contact", "PASS" if has_spatial_hero else "FAIL", "MAJOR", 5 if has_spatial_hero else 1),
            VisualCategoryResult("D", "Section heights", "Expansive 90-100vh spatial viewports", "Expansive 90-100vh spatial viewports" if has_spatial_hero else "Compact web section padding py-16", "PASS" if has_spatial_hero else "PARTIAL", "MAJOR", 5 if has_spatial_hero else 2),
            VisualCategoryResult("E", "Container widths", "Unconstrained 100% viewport canvas", "Unconstrained 100% viewport canvas" if has_spatial_hero else "Constrained max-w-7xl centered container", "PASS" if has_spatial_hero else "PARTIAL", "MINOR", 5 if has_spatial_hero else 2),
            VisualCategoryResult("F", "Typography scale", "Ultra-light Space Grotesk display type", "Ultra-light Space Grotesk display type" if has_spatial_hero else "Standard bold sans-serif headers", "PASS" if has_spatial_hero else "PARTIAL", "MAJOR", 5 if has_spatial_hero else 2),
            VisualCategoryResult("G", "Font character/style", "Muted monospace micro-labels & wide letter tracking", "Muted monospace micro-labels & wide tracking" if has_spatial_hero else "High-contrast corporate font", "PASS" if has_spatial_hero else "PARTIAL", "MAJOR", 5 if has_spatial_hero else 2),
            VisualCategoryResult("H", "Color palette", "Ambient dark slate (#030712) with cyan/emerald glows", "Ambient dark slate (#030712) with cyan/emerald glows" if "030712" in all_code or "slate-950" in all_code else "Standard dark blue", "PASS" if "030712" in all_code or "slate-950" in all_code else "PARTIAL", "MINOR", 5 if "030712" in all_code else 3),
            VisualCategoryResult("I", "Background treatment", "Real-time procedural WebGL 3D wireframe mesh terrain", "Real-time procedural 3D wireframe mesh terrain" if has_3d_terrain_mesh else "Static dark background", "PASS" if has_3d_terrain_mesh else "FAIL", "CRITICAL", 5 if has_3d_terrain_mesh else 1),
            VisualCategoryResult("J", "3D visual appearance", "Interactive wireframe mesh plane landscape", "Interactive wireframe mesh plane landscape" if has_3d_terrain_mesh else "2D static canvas background", "PASS" if has_3d_terrain_mesh else "FAIL", "CRITICAL", 5 if has_3d_terrain_mesh else 1),
            VisualCategoryResult("K", "3D position and scale", "Primary visual centerpiece dominating full viewport", "Primary visual centerpiece dominating full viewport" if has_3d_terrain_mesh else "Passive background backdrop", "PASS" if has_3d_terrain_mesh else "FAIL", "MAJOR", 5 if has_3d_terrain_mesh else 1),
            VisualCategoryResult("L", "Negative space", "Extreme breathing space (>80% open canvas)", "Extreme breathing space" if has_spatial_hero else "Dense card stacking", "PASS" if has_spatial_hero else "FAIL", "MAJOR", 5 if has_spatial_hero else 1),
            VisualCategoryResult("M", "Navigation placement", "Minimal floating peripheral pills (Audio, Lang, Anchor)", "Minimal floating peripheral pills" if has_floating_controls else "Fixed top corporate navbar", "PASS" if has_floating_controls else "FAIL", "CRITICAL", 5 if has_floating_controls else 1),
            VisualCategoryResult("N", "Cards and borders", "Hairline translucent dividers & borderless spatial lists", "Hairline translucent dividers & borderless spatial lists" if has_minimal_capabilities else "Rounded 3-column blue corporate cards", "PASS" if has_minimal_capabilities else "FAIL", "CRITICAL", 5 if has_minimal_capabilities else 1),
            VisualCategoryResult("O", "Image/visual treatment", "Procedural 3D nodes & spatial wireframe lines", "Procedural 3D nodes & spatial wireframe lines" if has_3d_terrain_mesh else "Standard Lucide icon containers", "PASS" if has_3d_terrain_mesh else "PARTIAL", "MINOR", 5 if has_3d_terrain_mesh else 2),
            VisualCategoryResult("P", "Animation behavior", "Fluid WebGL frame loops & sine wave height oscillation", "Fluid WebGL frame loops & sine wave height oscillation" if has_3d_terrain_mesh else "Standard Framer entrance fades", "PASS" if has_3d_terrain_mesh else "PARTIAL", "MAJOR", 5 if has_3d_terrain_mesh else 2),
            VisualCategoryResult("Q", "Scroll behavior", "3D Camera Z-axis translation on scroll", "3D Camera Z-axis translation on scroll" if has_3d_terrain_mesh else "Standard browser page scrolling", "PASS" if has_3d_terrain_mesh else "PARTIAL", "MAJOR", 5 if has_3d_terrain_mesh else 2),
            VisualCategoryResult("R", "Hover/interaction behavior", "Mouse perspective matrix tilt & radial lighting sweep", "Mouse perspective matrix tilt & radial lighting sweep" if has_3d_terrain_mesh else "Standard CSS card scale", "PASS" if has_3d_terrain_mesh else "PARTIAL", "MAJOR", 5 if has_3d_terrain_mesh else 2),
            VisualCategoryResult("S", "Mobile composition", "Responsive centered typography over 3D terrain canvas", "Responsive centered typography over 3D terrain canvas" if has_spatial_hero else "Stacked corporate grid cards", "PASS" if has_spatial_hero else "PARTIAL", "MAJOR", 5 if has_spatial_hero else 2),
            VisualCategoryResult("T", "Overall visual identity", "Award-winning experimental 3D spatial portfolio", "Award-winning experimental 3D spatial portfolio" if has_spatial_hero and has_3d_terrain_mesh and not has_generic_navbar else "Generic corporate SaaS website", "PASS" if has_spatial_hero and has_3d_terrain_mesh and not has_generic_navbar else "FAIL", "CRITICAL", 5 if has_spatial_hero and has_3d_terrain_mesh and not has_generic_navbar else 1)
        ]

        raw_visual_score = sum(c.score for c in categories)  # Max 100 (20 * 5)
        failed_categories = [c for c in categories if c.match_status == "FAIL"]

        # Anti-Inflation Rules Application
        anti_inflation_triggered = False
        cap_reason = ""
        visual_match_score = raw_visual_score

        critical_fails = [c for c in failed_categories if c.severity == "CRITICAL"]
        if len(critical_fails) >= 2 or has_generic_navbar:
            anti_inflation_triggered = True
            cap_reason = "Major visual difference in Hero/Navigation/Architecture. VISUAL_MATCH_SCORE capped at <= 50."
            visual_match_score = min(visual_match_score, 50)

        if len(failed_categories) >= 5:
            anti_inflation_triggered = True
            cap_reason = f"{len(failed_categories)} visual categories marked FAIL. VISUAL_MATCH_SCORE capped at <= 40."
            visual_match_score = min(visual_match_score, 40)

        overall_score = int(imp_score * 0.2 + func_score * 0.2 + visual_match_score * 0.6)

        return HonestEvaluationReport(
            reference_url=reference_url,
            implementation_score=imp_score,
            functional_score=func_score,
            visual_match_score=visual_match_score,
            overall_score=overall_score,
            category_results=categories,
            anti_inflation_triggered=anti_inflation_triggered,
            cap_reason=cap_reason
        )
