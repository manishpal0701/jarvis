"""
tools/coding/website_render_fingerprint.py
Render-Level Design Fingerprinting & Similarity Analyzer for Website Builder v4.

Extracts rendered visual architecture from generated HTML/CSS/TSX files:
- DOM section hierarchy & order
- hero layout, alignment & focal visual type
- background environment & animation classes
- typography pair & scale
- color system
- section compositions
- card language & repetition
- button & border styling
- 3D object type & spatial perspective usage
- motion language & scroll behavior
- footer structure

Calculates RENDERED_SIMILARITY_SCORE against historical fingerprints.
Rejects candidates / fails QA when SIMILARITY > 0.45.
"""

import os
import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class WebsiteRenderFingerprint:
    design_id: str = "cinematic_spatial"
    hero_layout: str = "asymmetric_split"
    hero_visual_type: str = "3d_rotating_core"
    hero_alignment: str = "left_headline_right_focal"
    navigation_style: str = "floating_glass_header"
    background_environment: str = "cyber_radial_grid"
    background_animation: str = "animated_mesh_glow"
    typography_pair: str = "Space Grotesk + Inter"
    typography_scale: str = "hero_7xl_title_xl_body"
    color_system: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#06b6d4",
        "secondary": "#6366f1",
        "accent": "#10b981",
        "background": "#030712",
        "text": "#f8fafc"
    })
    section_order: List[str] = field(default_factory=lambda: ["Navbar", "Hero", "About", "Services", "Projects", "Contact", "Footer"])
    section_compositions: List[str] = field(default_factory=lambda: ["hero_asymmetric", "about_dual_metric", "services_sticky_panel", "contact_split"])
    card_language: str = "spatial_glass_card"
    button_style: str = "bold_glow_gradient"
    border_language: str = "cyan_glass_border"
    image_treatment: str = "cyan_duotone_overlay"
    three_d_object_type: str = "orbit_rings_core"
    motion_language: str = "gpu_smooth_3d"
    scroll_behavior: str = "spatial_grid_rotate"
    footer_structure: str = "minimal_column_footer"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebsiteRenderFingerprinter:
    """
    Extracts structural render fingerprint from generated codebase and evaluates
    visual architecture similarity against historical fingerprints.
    """
    STORE_PATH = os.path.join(os.getcwd(), "data", "design_fingerprints.json")

    @classmethod
    def extract_fingerprint(cls, output_dir: str, design_id: str = "") -> WebsiteRenderFingerprint:
        """
        Parses generated TSX components, HTML, and CSS in `output_dir` to extract
        the actual rendered design fingerprint.
        """
        fp = WebsiteRenderFingerprint(design_id=design_id or "cinematic_spatial")

        comp_dir = os.path.join(output_dir, "src", "components")
        index_css_path = os.path.join(output_dir, "src", "index.css")

        all_code = ""
        hero_code = ""
        css_code = ""
        comp_files = []

        if os.path.exists(index_css_path):
            try:
                with open(index_css_path, "r", encoding="utf-8") as f:
                    css_code = f.read()
            except Exception:
                pass

        if os.path.exists(comp_dir):
            for fname in sorted(os.listdir(comp_dir)):
                if fname.endswith((".tsx", ".jsx")):
                    comp_files.append(fname.replace(".tsx", "").replace(".jsx", ""))
                    fpath = os.path.join(comp_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            text = f.read()
                            all_code += "\n" + text
                            if fname.lower().startswith("hero"):
                                hero_code = text
                    except Exception:
                        pass

        if comp_files:
            fp.section_order = comp_files

        code_lower = (all_code + "\n" + css_code).lower()

        # Extract Hero Layout & Visual Type
        if "herobanner" in code_lower or "restaurant" in code_lower or "cafe" in code_lower or "signaturedishes" in code_lower:
            fp.design_id = "premium_restaurant"
            fp.hero_layout = "centered_editorial_luxury"
            fp.hero_visual_type = "sculptural_gold_amber_geometry"
            fp.hero_alignment = "centered_serif_editorial"
            fp.background_environment = "warm_mahogany_ambience"
            fp.background_animation = "candlelit_warm_glow"
            fp.card_language = "gold_foil_border_card"
            fp.border_language = "gold_amber_foil_border"
            fp.button_style = "gold_leaf_button"
            fp.typography_pair = "Playfair Display + Inter"
        elif "enterprisehero" in code_lower or "novastack" in code_lower or "corecapabilities" in code_lower or "casestudies" in code_lower:
            fp.design_id = "data_intelligence"
            fp.hero_layout = "hud_data_split"
            fp.hero_visual_type = "3d_data_bar_chart"
            fp.hero_alignment = "b2b_metrics_left"
            fp.background_environment = "sapphire_data_grid"
            fp.background_animation = "data_stream_pulse"
            fp.card_language = "analytical_metric_card"
            fp.border_language = "indigo_panel_border"
            fp.button_style = "analytics_blue_button"
            fp.typography_pair = "Outfit + Inter"
        elif "developerhero" in code_lower or "skillmatrix" in code_lower or "featuredprojects" in code_lower:
            fp.design_id = "cyber_avatar_spatial"
            fp.hero_layout = "asymmetric_split"
            fp.hero_visual_type = "3d_rotating_core"
            fp.hero_alignment = "left_headline_right_focal"
            fp.background_environment = "cyber_radial_grid"
            fp.background_animation = "animated_mesh_glow"
            fp.card_language = "spatial_glass_card"
            fp.border_language = "cyan_glass_border"
            fp.button_style = "bold_glow_gradient"
            fp.typography_pair = "Space Grotesk + Inter"
        elif "hero_swiss_grid" in code_lower or "swiss" in code_lower and "grid" in code_lower:
            fp.hero_layout = "swiss_grid_left"
            fp.hero_visual_type = "minimal_wireframe_grid"
            fp.hero_alignment = "strict_left_grid"
        elif "brutalist" in code_lower or "raw_border" in code_lower:
            fp.hero_layout = "brutalist_staggered_overlap"
            fp.hero_visual_type = "raw_hard_edge_polyhedron"
            fp.hero_alignment = "overlapping_text_blocks"
        elif "organic" in code_lower or "fluid" in code_lower:
            fp.hero_layout = "centered_organic_orbs"
            fp.hero_visual_type = "breathing_fluid_orbs"
            fp.hero_alignment = "center_title_curved_pill"
        elif "luxury" in code_lower or "culinary" in code_lower or "gold" in code_lower:
            fp.hero_layout = "centered_editorial_luxury"
            fp.hero_visual_type = "sculptural_gold_amber_geometry"
            fp.hero_alignment = "centered_serif_editorial"
        elif "automotive" in code_lower or "vehicle" in code_lower or "speed" in code_lower:
            fp.hero_layout = "full_width_vehicle_banner"
            fp.hero_visual_type = "vehicle_product_silhouette"
            fp.hero_alignment = "left_title_bottom_specs"
        elif "hud" in code_lower or "telemetry" in code_lower:
            fp.hero_layout = "hud_telemetry_split"
            fp.hero_visual_type = "holographic_energy_sphere"
            fp.hero_alignment = "hud_status_left_sphere_right"
        elif "creative" in code_lower or "artistic" in code_lower:
            fp.hero_layout = "artistic_typography_collision"
            fp.hero_visual_type = "expressive_3d_sculpture"
            fp.hero_alignment = "asymmetric_collision"
        else:
            fp.hero_layout = "asymmetric_split"
            fp.hero_visual_type = "3d_rotating_core"
            fp.hero_alignment = "left_headline_right_focal"


        # Background Environment & Animation
        if fp.background_environment in ["cyber_radial_grid", ""]:
            if "architectural_grid_canvas" in code_lower or "bg-slate-50" in code_lower:
                fp.background_environment = "architectural_grid_canvas"
                fp.background_animation = "subtle_line_draw"
            elif "noise_grain_mesh" in code_lower or "bg-black" in code_lower and "volt" in code_lower:
                fp.background_environment = "noise_grain_mesh"
                fp.background_animation = "marquee_drift"
            elif "fluid_organic_glow" in code_lower or "bg-emerald-950" in code_lower:
                fp.background_environment = "fluid_organic_glow"
                fp.background_animation = "blob_morph_wave"
            elif "warm_mahogany" in code_lower or "candlelit" in code_lower or "bg-stone-950" in code_lower:
                fp.background_environment = "warm_mahogany_ambience"
                fp.background_animation = "candlelit_warm_glow"
            elif "speed_light_streaks" in code_lower or "bg-neutral-950" in code_lower and "red" in code_lower:
                fp.background_environment = "speed_light_streaks"
                fp.background_animation = "high_speed_light_tunnel"
            elif "hud_data_grid" in code_lower or "scanline" in code_lower:
                fp.background_environment = "hud_data_grid"
                fp.background_animation = "telemetry_pulse_scan"
            elif "expressive_color_field" in code_lower or "bg-purple" in code_lower:
                fp.background_environment = "expressive_color_field"
                fp.background_animation = "color_field_morph"

        # Typography Pair & Scale
        if fp.typography_pair in ["Space Grotesk + Inter", "Inter + System Sans", ""]:
            if "playfair" in code_lower or "serif" in code_lower:
                fp.typography_pair = "Playfair Display + Inter"
                fp.typography_scale = "editorial_serif_display"
            elif "jetbrains" in code_lower or "fira code" in code_lower or "hud" in code_lower:
                fp.typography_pair = "JetBrains Mono + Space Grotesk"
                fp.typography_scale = "monospace_hud_telemetry"
            elif "outfit" in code_lower:
                fp.typography_pair = "Outfit + Inter"
                fp.typography_scale = "rounded_organic_scale"
            elif "space grotesk" in code_lower:
                fp.typography_pair = "Space Grotesk + Inter"
                fp.typography_scale = "modern_bold_sans"

        # Card & Border Language
        if fp.card_language in ["spatial_glass_card", ""]:
            if "raw_thick_border_box" in code_lower or "border-lime" in code_lower or "border-4" in code_lower:
                fp.card_language = "raw_thick_border_box"
                fp.border_language = "thick_solid_volt_border"
                fp.button_style = "raw_block_button"
            elif "clean_border_card" in code_lower or "border-slate-300" in code_lower:
                fp.card_language = "clean_border_card"
                fp.border_language = "thin_architectural_rule"
                fp.button_style = "minimal_flat_button"
            elif "gold_foil" in code_lower or "culinary_gold" in code_lower or "border-amber" in code_lower:
                fp.card_language = "gold_foil_border_card"
                fp.border_language = "gold_amber_foil_border"
                fp.button_style = "gold_leaf_button"
            elif "soft_rounded_glass" in code_lower or "emerald" in code_lower:
                fp.card_language = "soft_rounded_glass"
                fp.border_language = "soft_emerald_pill_border"
                fp.button_style = "rounded_emerald_pill"
            elif "metallic_border_card" in code_lower or "border-red" in code_lower:
                fp.card_language = "metallic_border_card"
                fp.border_language = "electric_red_metallic_border"
                fp.button_style = "speed_red_button"
            elif "hud_neon_panel" in code_lower or "border-cyan" in code_lower and "mono" in code_lower:
                fp.card_language = "hud_neon_panel"
                fp.border_language = "neon_hud_scan_border"
                fp.button_style = "hud_glitch_button"


        # Extract primary colors from CSS if present
        color_matches = re.findall(r'#([0-9a-fA-F]{6})', code_lower)
        if color_matches:
            unique_colors = list(dict.fromkeys(["#" + c for c in color_matches]))
            if len(unique_colors) >= 3:
                fp.color_system = {
                    "primary": unique_colors[0],
                    "secondary": unique_colors[1],
                    "accent": unique_colors[2],
                    "background": unique_colors[-1]
                }

        return fp

    @classmethod
    def compute_similarity(cls, fp1: WebsiteRenderFingerprint, fp2: WebsiteRenderFingerprint) -> float:
        """
        Calculates exact visual render similarity score (0.00 to 1.00) between two render fingerprints.
        Checks rendered structural attributes.
        """
        checks = [
            (fp1.hero_layout == fp2.hero_layout, 2.0),
            (fp1.hero_visual_type == fp2.hero_visual_type, 2.0),
            (fp1.background_environment == fp2.background_environment, 1.5),
            (fp1.background_animation == fp2.background_animation, 1.5),
            (fp1.typography_pair == fp2.typography_pair, 1.0),
            (fp1.card_language == fp2.card_language, 1.0),
            (fp1.border_language == fp2.border_language, 1.0),
            (fp1.button_style == fp2.button_style, 1.0),
            (fp1.navigation_style == fp2.navigation_style, 1.0),
            (fp1.design_id == fp2.design_id, 2.0)
        ]

        total_weight = sum(w for _, w in checks)
        matched_weight = sum(w for matched, w in checks if matched)

        score = matched_weight / total_weight if total_weight > 0 else 0.0
        return round(score, 2)

    @classmethod
    def get_recent_fingerprints(cls, limit: int = 10) -> List[WebsiteRenderFingerprint]:
        if not os.path.exists(cls.STORE_PATH):
            return []
        try:
            with open(cls.STORE_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                fps = []
                for item in raw_data[-limit:]:
                    fps.append(WebsiteRenderFingerprint(
                        design_id=item.get("design_id", "cinematic_spatial"),
                        hero_layout=item.get("hero_layout", "asymmetric_split"),
                        hero_visual_type=item.get("hero_visual_type", "3d_rotating_core"),
                        hero_alignment=item.get("hero_alignment", "left_headline_right_focal"),
                        navigation_style=item.get("navigation_style", "floating_glass_header"),
                        background_environment=item.get("background_environment", "cyber_radial_grid"),
                        background_animation=item.get("background_animation", "animated_mesh_glow"),
                        typography_pair=item.get("typography_pair", "Space Grotesk + Inter"),
                        typography_scale=item.get("typography_scale", "hero_7xl_title_xl_body"),
                        color_system=item.get("color_system", {}),
                        section_order=item.get("section_order", []),
                        section_compositions=item.get("section_compositions", []),
                        card_language=item.get("card_language", "spatial_glass_card"),
                        button_style=item.get("button_style", "bold_glow_gradient"),
                        border_language=item.get("border_language", "cyan_glass_border"),
                        image_treatment=item.get("image_treatment", "cyan_duotone_overlay"),
                        three_d_object_type=item.get("three_d_object_type", "orbit_rings_core"),
                        motion_language=item.get("motion_language", "gpu_smooth_3d"),
                        scroll_behavior=item.get("scroll_behavior", "spatial_grid_rotate"),
                        footer_structure=item.get("footer_structure", "minimal_column_footer")
                    ))
                return fps
        except Exception:
            return []

    @classmethod
    def save_fingerprint(cls, fp: WebsiteRenderFingerprint):
        fps = cls.get_recent_fingerprints(limit=20)
        fps.append(fp)
        os.makedirs(os.path.dirname(cls.STORE_PATH), exist_ok=True)
        try:
            with open(cls.STORE_PATH, "w", encoding="utf-8") as f:
                json.dump([item.to_dict() for item in fps], f, indent=2)
        except Exception as e:
            print(f"[WebsiteRenderFingerprinter Warning]: Failed to save fingerprint: {e}")
