"""
tools/coding/website_design_direction.py
Centralized Design Direction Engine for Website Builder v4.

Enforces NON-NEGOTIABLE DESIGN DIVERSITY CONTRACT:
- 15 genuinely distinct visual directions covering 8 Structural Families (A through H).
- Context-aware design selection matching industry and brand.
- Render-level Design Fingerprinting & Similarity Scoring (similarity <= 0.45 preferred, > 0.45 rejected).
- Explicit Previous-Design Reuse Mode (triggered by user keywords).
- Prevents accidental visual cloning across generated websites.
"""

import os
import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from tools.coding.website_render_fingerprint import WebsiteRenderFingerprint, WebsiteRenderFingerprinter

@dataclass
class RenderStyleContract:
    hero_layout: str
    background_environment: str
    navigation_style: str
    typography_pair: str
    color_palette: Dict[str, str]
    section_order: List[str]
    section_compositions: List[str]
    card_language: str
    animation_language: str
    spacing_system: str
    cta_style: str
    footer_style: str
    hero_focal_object: str
    interaction_style: str
    border_language: str = "cyan_glass_border"
    button_style: str = "bold_glow_gradient"
    typography_scale: str = "hero_7xl_title_xl_body"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DesignDirection:
    design_id: str
    name: str
    visual_style: str
    hero_composition: str
    background_system: str
    focal_object: str
    typography_system: str
    color_system: Dict[str, str]
    navigation_style: str
    section_compositions: List[str]
    animation_language: str
    scroll_behavior: str
    card_language: str
    image_treatment: str
    atmosphere: str
    three_d_strategy: str
    family: str = "FAMILY A — CINEMATIC SPATIAL"
    border_language: str = "cyan_glass_border"
    button_style: str = "bold_glow_gradient"

    @property
    def structural_family(self) -> str:
        return self.family

    def get_render_contract(self) -> RenderStyleContract:
        return RenderStyleContract(
            hero_layout=self.hero_composition,
            background_environment=self.background_system,
            navigation_style=self.navigation_style,
            typography_pair=self.typography_system,
            color_palette=self.color_system,
            section_order=["Navbar", "Hero", "About", "Services", "Projects", "Contact", "Footer"],
            section_compositions=self.section_compositions,
            card_language=self.card_language,
            animation_language=self.animation_language,
            spacing_system="py-24 px-6 gap-12",
            cta_style=self.button_style,
            footer_style="minimal_column_footer",
            hero_focal_object=self.focal_object,
            interaction_style=self.scroll_behavior,
            border_language=self.border_language,
            button_style=self.button_style
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["render_contract"] = self.get_render_contract().to_dict()
        return d


class DesignLibrary:
    """
    Library of 15 genuinely distinct visual directions mapped to 8 Structural Families.
    """

    @classmethod
    def get_all_directions(cls) -> List[DesignDirection]:
        return [
            # FAMILY A — CINEMATIC SPATIAL
            DesignDirection(
                design_id="cyber_avatar_spatial",
                name="Cyber Avatar Spatial Reference",
                family="FAMILY A — CINEMATIC SPATIAL",
                visual_style="Dark near-black navy environment with dominant cyan/teal rim glow, magenta accents, stylized 3D developer avatar focal subject, and multi-layer depth",
                hero_composition="Stylized 3D developer character focal point with cyan/teal rim glow, typography integrated around subject, compact top nav, and vertical social side rail",
                background_system="multi_layer_cyber_atmosphere_with_cyan_magenta_orbs_and_particles",
                focal_object="Stylized3DDeveloperAvatar",
                typography_system="Space Grotesk + Inter",
                color_system={
                    "primary": "#06b6d4",
                    "secondary": "#ec4899",
                    "accent": "#10b981",
                    "background": "#020617",
                    "surface": "#0b132b",
                    "text": "#f8fafc",
                    "border": "#1e293b"
                },
                navigation_style="compact_header_with_vertical_social_rail",
                section_compositions=["hero_character_focal", "what_i_do_capabilities", "building_journey_timeline", "my_work_numbered_projects", "tech_matrix_orbit", "contact_direct"],
                animation_language="character_float_hover_displacement_and_scroll_reveal",
                scroll_behavior="scene_parallax_and_text_mask_reveal",
                card_language="luminous_cyber_panel_with_cyan_border",
                image_treatment="cyan_duotone_rim_lighting",
                atmosphere="cyber_avatar_luminous_glow",
                three_d_strategy="stylized_developer_avatar_with_3d_depth_layers",
                border_language="cyan_luminous_border",
                button_style="neon_cyan_pill_button"
            ),
            DesignDirection(
                design_id="cinematic_spatial",
                name="Cinematic Spatial",
                family="FAMILY A — CINEMATIC SPATIAL",
                visual_style="Dark spatial atmosphere with cyan/teal luminous highlights and high depth layers",
                hero_composition="Asymmetric split-screen with left-aligned headline and rotating 3D Neural Core on right",
                background_system="cyber_radial_grid",
                focal_object="RotatingCore",
                typography_system="Space Grotesk + Inter",
                color_system={
                    "primary": "#06b6d4",
                    "secondary": "#6366f1",
                    "accent": "#10b981",
                    "background": "#030712",
                    "surface": "#0f172a",
                    "text": "#f8fafc",
                    "border": "#1e293b"
                },
                navigation_style="floating_glass_header",
                section_compositions=["hero_asymmetric", "about_dual_metric", "services_sticky_panel", "tech_matrix", "solutions_layered", "projects_editorial", "contact_split"],
                animation_language="gpu_smooth_3d",
                scroll_behavior="spatial_grid_rotate",
                card_language="spatial_glass_card",
                image_treatment="cyan_duotone_overlay",
                atmosphere="luminous_cyber_glow",
                three_d_strategy="orbit_rings_and_core",
                border_language="cyan_glass_border",
                button_style="bold_glow_gradient"
            ),

            # FAMILY B — SWISS EDITORIAL
            DesignDirection(
                design_id="swiss_minimal",
                name="Swiss Minimal",
                family="FAMILY B — SWISS EDITORIAL",
                visual_style="Clean white/light canvas with strict architectural grid lines, bold dark typography, and cobalt blue accents",
                hero_composition="Left-aligned large typography with structured architectural grid lines and minimal badge",
                background_system="architectural_grid_canvas",
                focal_object="MinimalWireframeCube",
                typography_system="Inter + Fira Code",
                color_system={
                    "primary": "#2563eb",
                    "secondary": "#0f172a",
                    "accent": "#3b82f6",
                    "background": "#f8fafc",
                    "surface": "#ffffff",
                    "text": "#090d16",
                    "border": "#e2e8f0"
                },
                navigation_style="border_bottom_clean",
                section_compositions=["hero_swiss_grid", "about_minimal_cols", "services_numbered_list", "tech_flat_table", "contact_clean_form"],
                animation_language="precise_micro_transitions",
                scroll_behavior="grid_line_reveal",
                card_language="clean_border_card",
                image_treatment="monochrome_crisp",
                atmosphere="stark_clean_canvas",
                three_d_strategy="flat_grid_perspective",
                border_language="thin_architectural_rule",
                button_style="minimal_flat_button"
            ),

            # FAMILY C — EXPERIMENTAL BRUTALIST
            DesignDirection(
                design_id="experimental_brutalist",
                name="Experimental Brutalist",
                family="FAMILY C — EXPERIMENTAL BRUTALIST",
                visual_style="Dark charcoal & volt green brutalism with oversized condensed typography and hard borders",
                hero_composition="Overlapping editorial text blocks with oversized condensed headline and raw geometric containers",
                background_system="noise_grain_mesh",
                focal_object="RotatingBrutalistPolyhedron",
                typography_system="Space Grotesk + JetBrains Mono",
                color_system={
                    "primary": "#ccff00",
                    "secondary": "#ffffff",
                    "accent": "#ff0055",
                    "background": "#000000",
                    "surface": "#111111",
                    "text": "#ffffff",
                    "border": "#333333"
                },
                navigation_style="raw_border_banner",
                section_compositions=["hero_brutalist_overlap", "about_ticker", "services_horizontal_stripes", "projects_staggered", "contact_raw_box"],
                animation_language="high_contrast_snap",
                scroll_behavior="marquee_horizontal_drift",
                card_language="raw_thick_border_box",
                image_treatment="duotone_volt_green",
                atmosphere="gritty_digital_noise",
                three_d_strategy="raw_hard_edge_polyhedrons",
                border_language="thick_solid_volt_border",
                button_style="raw_block_button"
            ),

            # FAMILY D — ORGANIC DIGITAL
            DesignDirection(
                design_id="organic_digital",
                name="Organic Digital",
                family="FAMILY D — ORGANIC DIGITAL",
                visual_style="Soft dark emerald & obsidian theme with fluid organic shapes and rounded glowing geometry",
                hero_composition="Centered rounded headline with fluid breathing glowing Orbs and soft glassmorphic curves",
                background_system="fluid_organic_glow",
                focal_object="FluidBreathingOrb",
                typography_system="Outfit + Inter",
                color_system={
                    "primary": "#10b981",
                    "secondary": "#06b6d4",
                    "accent": "#34d399",
                    "background": "#022c22",
                    "surface": "#064e3b",
                    "text": "#ecfdf5",
                    "border": "#059669"
                },
                navigation_style="rounded_floating_pill",
                section_compositions=["hero_fluid_center", "about_curved_cards", "services_organic_grid", "contact_rounded"],
                animation_language="smooth_fluid_wave",
                scroll_behavior="organic_blob_morph",
                card_language="soft_rounded_glass",
                image_treatment="emerald_soft_glow",
                atmosphere="biomorphic_ambient_glow",
                three_d_strategy="breathing_fluid_orbs",
                border_language="soft_emerald_pill_border",
                button_style="rounded_emerald_pill"
            ),

            # FAMILY E — EDITORIAL LUXURY
            DesignDirection(
                design_id="editorial_luxury",
                name="Editorial Luxury",
                family="FAMILY E — EDITORIAL LUXURY",
                visual_style="Deep charcoal & gold foil luxury aesthetic with high negative space and serif typography",
                hero_composition="Centered oversized headline with warm ambient lighting and subtle floating gold geometry",
                background_system="warm_mahogany_glow",
                focal_object="GoldSculpturalGeometry",
                typography_system="Playfair Display + Inter",
                color_system={
                    "primary": "#f59e0b",
                    "secondary": "#d97706",
                    "accent": "#78350f",
                    "background": "#0c0a09",
                    "surface": "#1c1917",
                    "text": "#fafaf9",
                    "border": "#44403c"
                },
                navigation_style="minimal_border_top",
                section_compositions=["hero_centered_editorial", "story_full_bleed", "services_column_list", "showcase_gallery", "contact_luxurious_form"],
                animation_language="slow_cinematic_fade",
                scroll_behavior="color_atmosphere_shift",
                card_language="gold_foil_border_card",
                image_treatment="warm_high_contrast",
                atmosphere="candlelit_warm_ambience",
                three_d_strategy="subtle_floating_geometry",
                border_language="gold_amber_foil_border",
                button_style="gold_leaf_button"
            ),

            # FAMILY F — AUTOMOTIVE CINEMATIC
            DesignDirection(
                design_id="automotive_cinematic",
                name="Automotive Cinematic",
                family="FAMILY F — AUTOMOTIVE CINEMATIC",
                visual_style="Deep pitch black & electric red automotive theme with light trails and metallic reflections",
                hero_composition="Full-width dark vehicle silhouette banner with speed-inspired light streaks and bold CTA",
                background_system="speed_light_streaks",
                focal_object="AbstractVehicleSilhouette",
                typography_system="Space Grotesk + Inter",
                color_system={
                    "primary": "#e82127",
                    "secondary": "#ffffff",
                    "accent": "#991b1b",
                    "background": "#0c0c0e",
                    "surface": "#18181c",
                    "text": "#ffffff",
                    "border": "#27272a"
                },
                navigation_style="cinematic_top_bar",
                section_compositions=["hero_vehicle_banner", "performance_metrics", "specs_grid", "gallery_full_bleed", "contact_automotive"],
                animation_language="high_speed_parallax",
                scroll_behavior="perspective_tunnel_zoom",
                card_language="metallic_border_card",
                image_treatment="dramatic_low_key_lighting",
                atmosphere="dark_velocity_lights",
                three_d_strategy="speed_light_tunnel",
                border_language="electric_red_metallic_border",
                button_style="speed_red_button"
            ),

            # FAMILY G — FUTURISTIC INTERFACE
            DesignDirection(
                design_id="futuristic_interface",
                name="Futuristic Interface",
                family="FAMILY G — FUTURISTIC INTERFACE",
                visual_style="HUD-inspired digital interface with glowing node streams and monospace data telemetry",
                hero_composition="Split screen with HUD status telemetry box and central holographic energy sphere",
                background_system="hud_data_grid",
                focal_object="HolographicEnergySphere",
                typography_system="JetBrains Mono + Space Grotesk",
                color_system={
                    "primary": "#00f0ff",
                    "secondary": "#7000ff",
                    "accent": "#00ff66",
                    "background": "#050814",
                    "surface": "#0a1026",
                    "text": "#e0f2fe",
                    "border": "#1e295d"
                },
                navigation_style="hud_telemetry_bar",
                section_compositions=["hero_hud_telemetry", "diagnostics_grid", "node_network_services", "data_matrix", "contact_hud_form"],
                animation_language="telemetry_pulse_scan",
                scroll_behavior="hud_scanline_move",
                card_language="hud_neon_panel",
                image_treatment="cyan_hud_scanline",
                atmosphere="holographic_data_stream",
                three_d_strategy="holographic_node_mesh",
                border_language="neon_hud_scan_border",
                button_style="hud_glitch_button"
            ),

            # FAMILY H — CREATIVE AGENCY
            DesignDirection(
                design_id="creative_agency",
                name="Creative Agency",
                family="FAMILY H — CREATIVE AGENCY",
                visual_style="Unconventional dark purple & coral accent theme with bold typography collisions and expressiveness",
                hero_composition="Overlapping editorial headline with dynamic color field background and artistic sculpture",
                background_system="expressive_color_field",
                focal_object="AbstractArtisticSculpture",
                typography_system="Space Grotesk + Playfair Display",
                color_system={
                    "primary": "#ff6b6b",
                    "secondary": "#4ecdc4",
                    "accent": "#ffe66d",
                    "background": "#1a0933",
                    "surface": "#2b1055",
                    "text": "#ffffff",
                    "border": "#4a1c88"
                },
                navigation_style="creative_artistic_bar",
                section_compositions=["hero_artistic_collision", "agency_manifesto", "creative_work_showcase", "contact_artistic"],
                animation_language="expressive_morph_transitions",
                scroll_behavior="color_field_wave",
                card_language="creative_artistic_panel",
                image_treatment="coral_vibrant_overlay",
                atmosphere="artistic_expressive_glow",
                three_d_strategy="expressive_3d_sculpture",
                border_language="artistic_coral_border",
                button_style="creative_gradient_button"
            ),

            # Additional Auxiliary Directions
            DesignDirection(
                design_id="fashion_editorial",
                name="Fashion Editorial",
                family="FAMILY E — EDITORIAL LUXURY",
                visual_style="Monochrome ivory & black high-fashion editorial magazine layout with serif headings",
                hero_composition="Large asymmetric typography collision with full-bleed high-fashion photography",
                background_system="soft_ivory_paper",
                focal_object="FloatingFashionFragment",
                typography_system="Playfair Display + Inter",
                color_system={
                    "primary": "#171717",
                    "secondary": "#525252",
                    "accent": "#a3a3a3",
                    "background": "#fafafa",
                    "surface": "#ffffff",
                    "text": "#0a0a0a",
                    "border": "#e5e5e5"
                },
                navigation_style="editorial_header_minimal",
                section_compositions=["hero_editorial_collision", "magazine_lookbook", "collection_grid", "brand_narrative"],
                animation_language="elegant_slow_fade",
                scroll_behavior="editorial_parallax_reveal",
                card_language="flat_frameless_panel",
                image_treatment="monochrome_high_fashion",
                atmosphere="minimal_magazine_paper",
                three_d_strategy="floating_paper_fragments",
                border_language="monochrome_thin_rule",
                button_style="minimal_black_button"
            ),
            DesignDirection(
                design_id="premium_restaurant",
                name="Premium Restaurant",
                family="FAMILY E — EDITORIAL LUXURY",
                visual_style="Rich mahogany stone & amber gold fine dining theme with culinary photography",
                hero_composition="Warm candlelit dining hero banner with Reserve Table CTA and signature food preview",
                background_system="candlelit_warm_ambience",
                focal_object="CulinaryArtistryFocal",
                typography_system="Playfair Display + Inter",
                color_system={
                    "primary": "#f59e0b",
                    "secondary": "#d97706",
                    "accent": "#78350f",
                    "background": "#0c0a09",
                    "surface": "#1c1917",
                    "text": "#fafaf9",
                    "border": "#44403c"
                },
                navigation_style="gastronomy_gold_nav",
                section_compositions=["hero_culinary_banner", "signature_dishes_grid", "tabbed_menu", "chef_story", "ambience_gallery", "reservation_form"],
                animation_language="warm_gentle_glow",
                scroll_behavior="amber_light_shift",
                card_language="culinary_gold_card",
                image_treatment="warm_appetizing_food",
                atmosphere="candlelit_gastronomy",
                three_d_strategy="floating_ingredients_depth",
                border_language="gold_amber_foil_border",
                button_style="gold_leaf_button"
            ),
            DesignDirection(
                design_id="architecture_spatial",
                name="Architecture Spatial",
                family="FAMILY B — SWISS EDITORIAL",
                visual_style="Slate gray & terracotta architectural theme with geometric grid lines and wireframes",
                hero_composition="Architectural 3D perspective wireframe layout with clean structural text columns",
                background_system="architectural_blueprint_grid",
                focal_object="3DArchitecturalWireframe",
                typography_system="Space Grotesk + Inter",
                color_system={
                    "primary": "#c2410c",
                    "secondary": "#475569",
                    "accent": "#ea580c",
                    "background": "#0f172a",
                    "surface": "#1e293b",
                    "text": "#f8fafc",
                    "border": "#334155"
                },
                navigation_style="structural_grid_nav",
                section_compositions=["hero_wireframe_structure", "blueprint_specs", "project_blueprints", "contact_architecture"],
                animation_language="structural_line_draw",
                scroll_behavior="perspective_elevation_shift",
                card_language="blueprint_panel",
                image_treatment="terracotta_wireframe",
                atmosphere="blueprint_grid_ambience",
                three_d_strategy="geometric_building_wireframe",
                border_language="terracotta_wire_border",
                button_style="structural_block_button"
            ),
            DesignDirection(
                design_id="neo_retro_digital",
                name="Neo-Retro Digital",
                family="FAMILY C — EXPERIMENTAL BRUTALIST",
                visual_style="CRT dark violet & magenta synthwave theme with controlled neon glow and scanlines",
                hero_composition="Retro synthwave perspective grid with glowing magenta headline and 3D synth cube",
                background_system="synthwave_retro_grid",
                focal_object="3DSynthwaveCube",
                typography_system="Space Grotesk + Fira Code",
                color_system={
                    "primary": "#d946ef",
                    "secondary": "#8b5cf6",
                    "accent": "#06b6d4",
                    "background": "#0f051d",
                    "surface": "#1e0b36",
                    "text": "#fae8ff",
                    "border": "#4c1d95"
                },
                navigation_style="synthwave_neon_header",
                section_compositions=["hero_synthwave_grid", "retro_services_list", "pixel_portfolio", "contact_neon_box"],
                animation_language="neon_flicker_scan",
                scroll_behavior="retro_grid_scroll",
                card_language="retro_neon_border_card",
                image_treatment="magenta_synthwave_duotone",
                atmosphere="vaporwave_neon_haze",
                three_d_strategy="rotating_synthwave_polyhedrons",
                border_language="magenta_neon_border",
                button_style="synthwave_glow_button"
            ),
            DesignDirection(
                design_id="glass_architecture",
                name="Glass Architecture",
                family="FAMILY A — CINEMATIC SPATIAL",
                visual_style="Translucent slate & icy cyan theme with multi-stacked transparent glass surfaces and depth blur",
                hero_composition="Stacked translucent glass panels floating over icy cyan gradient background",
                background_system="icy_cyan_glass_depth",
                focal_object="StackedGlassPrism",
                typography_system="Inter + JetBrains Mono",
                color_system={
                    "primary": "#38bdf8",
                    "secondary": "#818cf8",
                    "accent": "#34d399",
                    "background": "#030712",
                    "surface": "#0f172a",
                    "text": "#f0f9ff",
                    "border": "#1e293b"
                },
                navigation_style="translucent_glass_floating_bar",
                section_compositions=["hero_stacked_glass", "about_frosted_cards", "services_translucent_grid", "contact_glass_modal"],
                animation_language="refractive_blur_shift",
                scroll_behavior="depth_glass_parallax",
                card_language="spatial_glass_panel",
                image_treatment="frost_cyan_blur",
                atmosphere="icy_translucent_glow",
                three_d_strategy="refractive_glass_stack",
                border_language="cyan_glass_border",
                button_style="bold_glow_gradient"
            ),
            DesignDirection(
                design_id="product_showcase",
                name="Product Showcase",
                family="FAMILY G — FUTURISTIC INTERFACE",
                visual_style="Dark navy & indigo product-first theme with floating product interface and interactive tabs",
                hero_composition="Floating product interface dashboard centered over glowing indigo core with CTA buttons",
                background_system="indigo_dashboard_ambience",
                focal_object="FloatingProductDashboard",
                typography_system="Inter + Space Grotesk",
                color_system={
                    "primary": "#6366f1",
                    "secondary": "#06b6d4",
                    "accent": "#10b981",
                    "background": "#090d16",
                    "surface": "#111827",
                    "text": "#f9fafb",
                    "border": "#1f2937"
                },
                navigation_style="saas_product_nav",
                section_compositions=["hero_product_dashboard", "feature_deep_dive", "value_props", "pricing_matrix", "contact_saas"],
                animation_language="dashboard_ui_pop",
                scroll_behavior="feature_tab_reveal",
                card_language="product_dashboard_card",
                image_treatment="clean_ui_screenshot",
                atmosphere="indigo_saas_glow",
                three_d_strategy="floating_ui_dashboard",
                border_language="indigo_panel_border",
                button_style="product_indigo_button"
            ),
            DesignDirection(
                design_id="data_intelligence",
                name="Data Intelligence",
                family="FAMILY G — FUTURISTIC INTERFACE",
                visual_style="Slate 950 & sapphire blue theme with animated chart grids, metric matrices, and analytical widgets",
                hero_composition="Asymmetric layout with analytical metric cards on left and interactive data visualizer on right",
                background_system="sapphire_data_grid",
                focal_object="3DDataVisualizerMesh",
                typography_system="Inter + JetBrains Mono",
                color_system={
                    "primary": "#3b82f6",
                    "secondary": "#0284c7",
                    "accent": "#10b981",
                    "background": "#020617",
                    "surface": "#0f172a",
                    "text": "#f8fafc",
                    "border": "#1e293b"
                },
                navigation_style="analytics_header",
                section_compositions=["hero_data_visualizer", "metric_pillars", "analytical_matrix", "case_studies", "contact_enterprise"],
                animation_language="data_stream_pulse",
                scroll_behavior="chart_grow_reveal",
                card_language="analytical_metric_card",
                image_treatment="sapphire_data_overlay",
                atmosphere="precision_data_ambience",
                three_d_strategy="3d_data_bar_chart",
                button_style="analytics_blue_button"
            )
        ]

    @classmethod
    def get_direction(cls, design_id: str) -> Optional[DesignDirection]:
        for d in cls.get_all_directions():
            if d.design_id.lower() == design_id.lower():
                return d
        return None


class DesignDirectionEngine:
    """
    Centralized Design Direction Engine.
    Detects reuse mode, computes render-level similarity scores, selects context-aware non-repeating designs,
    and records telemetry.
    """

    REUSE_KEYWORDS = [
        "previous design", "same design as last time", "pichli website jaisa",
        "pichla design", "reuse previous design", "same visual style",
        "use the previous layout", "same design", "last website jaisa design",
        "use the previous design", "reuse the previous"
    ]

    NEGATIVE_KEYWORDS = [
        "do not reuse", "don't reuse", "dont reuse", "do not use previous", "don't use previous",
        "dont use previous", "not reuse", "no reuse", "different design", "new design"
    ]

    @classmethod
    def detect_reuse_mode(cls, command: str) -> bool:
        cmd_lower = command.lower()
        if any(neg in cmd_lower for neg in cls.NEGATIVE_KEYWORDS):
            return False
        return any(kw in cmd_lower for kw in cls.REUSE_KEYWORDS)

    @classmethod
    def direction_to_fingerprint(cls, direction: DesignDirection) -> WebsiteRenderFingerprint:
        """
        Converts a DesignDirection into a WebsiteRenderFingerprint for similarity scoring.
        """
        return WebsiteRenderFingerprint(
            design_id=direction.design_id,
            hero_layout=direction.hero_composition,
            hero_visual_type=direction.focal_object,
            hero_alignment="left_headline_right_focal" if "split" in direction.hero_composition.lower() else "centered_editorial",
            navigation_style=direction.navigation_style,
            background_environment=direction.background_system,
            background_animation=direction.animation_language,
            typography_pair=direction.typography_system,
            color_system=direction.color_system,
            section_compositions=direction.section_compositions,
            card_language=direction.card_language,
            button_style=direction.button_style,
            border_language=direction.border_language,
            image_treatment=direction.image_treatment,
            three_d_object_type=direction.three_d_strategy,
            motion_language=direction.animation_language,
            scroll_behavior=direction.scroll_behavior
        )

    @classmethod
    def compute_similarity(cls, candidate: DesignDirection, recent_fingerprints: List[WebsiteRenderFingerprint]) -> float:
        """
        Calculates DESIGN_SIMILARITY_SCORE (0.00 to 1.00) between candidate design direction
        and recent render fingerprints.
        """
        if not recent_fingerprints:
            return 0.0

        cand_fp = cls.direction_to_fingerprint(candidate)
        scores = [WebsiteRenderFingerprinter.compute_similarity(cand_fp, fp) for fp in recent_fingerprints]

        return max(scores) if scores else 0.0

    @classmethod
    def select_design(cls, command: str, category: str = "business", company_name: str = "") -> tuple[DesignDirection, float, bool]:
        """
        Selects a DesignDirection for the prompt.
        Returns (selected_direction, similarity_score, is_reuse_mode).
        Emits telemetry logs:
        [WEBSITE_DESIGN_SELECTION] mode=NEW|REUSE design_id=...
        [WEBSITE_DESIGN_ID] design_id=...
        [WEBSITE_DESIGN_SIMILARITY] score=...
        [WEBSITE_DESIGN_REUSE] enabled=True|False
        """
        is_reuse = cls.detect_reuse_mode(command)
        all_dirs = DesignLibrary.get_all_directions()
        recent_fps = WebsiteRenderFingerprinter.get_recent_fingerprints()

        if is_reuse and recent_fps:
            # Re-use previous design specification and fingerprint
            last_fp = recent_fps[-1]
            matching_dir = next((d for d in all_dirs if d.design_id == last_fp.design_id), all_dirs[0])
            print(f"[WEBSITE_DESIGN_SELECTION] mode=REUSE design_id={matching_dir.design_id}", flush=True)
            print(f"[WEBSITE_DESIGN_ID] design_id={matching_dir.design_id}", flush=True)
            print(f"[WEBSITE_DESIGN_SIMILARITY] score=1.00", flush=True)
            print(f"[WEBSITE_DESIGN_REUSE] enabled=True", flush=True)
            return matching_dir, 1.00, True

        # Context-aware candidate filtering
        cat_lower = (category or "").lower()
        cmd_lower = command.lower()

        candidate_pool = []
        if cat_lower in ["restaurant_cafe", "restaurant", "cafe"] or any(k in cmd_lower for k in ["cafe", "restaurant", "food", "dining"]):
            candidate_pool = [d for d in all_dirs if d.design_id in ("premium_restaurant", "editorial_luxury", "organic_digital")]
        elif cat_lower in ["agency_website", "agency"] or "agency" in cmd_lower:
            candidate_pool = [d for d in all_dirs if d.design_id in ("creative_agency", "editorial_luxury", "swiss_minimal")]
        elif cat_lower in ["product_website", "product"] or any(k in cmd_lower for k in ["product", "saas"]):
            candidate_pool = [d for d in all_dirs if d.design_id in ("product_showcase", "glass_architecture", "cinematic_spatial", "futuristic_interface")]
        elif cat_lower in ["service_business", "service"] or "service" in cmd_lower:
            candidate_pool = [d for d in all_dirs if d.design_id in ("swiss_minimal", "data_intelligence", "organic_digital")]
        elif cat_lower in ["landing_page", "landing"] or "landing" in cmd_lower:
            candidate_pool = [d for d in all_dirs if d.design_id in ("product_showcase", "experimental_brutalist", "swiss_minimal")]
        elif cat_lower in ["developer_portfolio", "portfolio"] or "developer" in cmd_lower:
            candidate_pool = [d for d in all_dirs if d.design_id in ("cyber_avatar_spatial", "experimental_brutalist", "neo_retro_digital")]
        elif cat_lower in ["personal_portfolio"]:
            candidate_pool = [d for d in all_dirs if d.design_id in ("swiss_minimal", "fashion_editorial", "organic_digital")]
        elif cat_lower in ["business_website", "company", "business"] or any(k in cmd_lower for k in ["company", "corporate", "business", "b2b"]):
            candidate_pool = [d for d in all_dirs if d.design_id in ("data_intelligence", "product_showcase", "swiss_minimal", "architecture_spatial")]
        elif "tesla" in cmd_lower or "auto" in cmd_lower or "car" in cmd_lower:
            candidate_pool = [d for d in all_dirs if d.design_id in ("automotive_cinematic", "futuristic_interface", "swiss_minimal")]
        elif "fashion" in cmd_lower or "clothing" in cmd_lower or "magazine" in cmd_lower or "maison" in cmd_lower:
            candidate_pool = [d for d in all_dirs if d.design_id in ("fashion_editorial", "editorial_luxury", "creative_agency")]
        else:
            candidate_pool = all_dirs


        if not candidate_pool:
            candidate_pool = all_dirs

        # Select candidate with lowest similarity score to recent fingerprints (SIMILARITY <= 0.45 threshold)
        best_candidate = candidate_pool[0]
        lowest_score = 1.0

        for cand in candidate_pool:
            score = cls.compute_similarity(cand, recent_fps)
            if score < lowest_score:
                lowest_score = score
                best_candidate = cand
            if score <= 0.45:
                best_candidate = cand
                lowest_score = score
                break

        # Convert selected direction to fingerprint and persist to store
        fp = cls.direction_to_fingerprint(best_candidate)
        WebsiteRenderFingerprinter.save_fingerprint(fp)

        return best_candidate, lowest_score, False

    @classmethod
    def get_all_directions(cls) -> List[DesignDirection]:
        return DesignLibrary.get_all_directions()

    @classmethod
    def get_direction(cls, design_id: str) -> Optional[DesignDirection]:
        return DesignLibrary.get_direction(design_id)
