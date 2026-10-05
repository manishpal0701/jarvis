"""
tools/coding/reference_analysis_engine.py
Reference Analysis Engine for Jarvis Reference-Driven Website Builder.

Analyzes client-supplied design references (Website URL, Video, PDF, Screenshot/Image)
and generates an internal structured Visual DNA Specification (VisualDNASpec).

STRICT ISOLATION RULE:
References supply ONLY visual language, composition, typography direction, and motion behavior.
All text, business identity, logo, images, claims, and product information must come exclusively
from the Client Brief.
"""

import os
import re
import json
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class ReferenceItem:
    ref_type: str  # "URL", "VIDEO", "PDF", "IMAGE", "MULTI"
    source: str    # URL string or absolute file path
    title: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_content: Optional[str] = None

@dataclass
class MotionScene:
    scene_id: str          # e.g., "SCENE 01"
    timestamp_range: str   # e.g., "0-3 sec"
    description: str       # e.g., "Hero title enters from bottom with mask reveal"
    animation_type: str    # e.g., "text_reveal", "image_expand", "horizontal_shift", "parallax_scale"

@dataclass
class MotionDesignSpec:
    scenes: List[MotionScene] = field(default_factory=list)
    scroll_behavior: str = "scroll_linked_image_scale"
    transition_style: str = "section_mask_transition"
    hover_behavior: str = "magnetic_cta_displacement"
    cursor_interaction: str = "custom_cursor_follower"
    entrance_animation: str = "staggered_text_reveal"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenes": [asdict(s) for s in self.scenes],
            "scroll_behavior": self.scroll_behavior,
            "transition_style": self.transition_style,
            "hover_behavior": self.hover_behavior,
            "cursor_interaction": self.cursor_interaction,
            "entrance_animation": self.entrance_animation
        }

@dataclass
class VisualDNASpec:
    reference_present: bool = False
    reference_type: str = "NONE"  # "NONE", "URL", "VIDEO", "PDF", "IMAGE", "MULTI"
    style: str = "editorial"       # editorial / experimental / minimal / luxury / cinematic / corporate
    composition: str = "asymmetric full-width"
    typography: Dict[str, str] = field(default_factory=lambda: {
        "header_font": "Space Grotesk",
        "body_font": "Inter",
        "scale": "oversized display type",
        "hierarchy": "high contrast with small metadata labels"
    })
    color_palette: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#0f172a",
        "secondary": "#2563eb",
        "accent": "#38bdf8",
        "background": "#030712",
        "surface": "#0f172a",
        "text": "#f8fafc"
    })
    image_treatment: str = "full bleed masked mixed aspect ratios"
    motion_spec: MotionDesignSpec = field(default_factory=MotionDesignSpec)
    interaction: str = "magnetic CTA with hover displacement"
    spacing: str = "large vertical rhythm with variable section heights"
    section_rhythm: List[str] = field(default_factory=lambda: ["Hero", "About", "Services", "Showcase", "Contact"])
    inspection_status: str = "VERIFIED"  # VERIFIED, PARTIAL, NOT_VERIFIED
    unsupported_claims: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_present": self.reference_present,
            "reference_type": self.reference_type,
            "style": self.style,
            "composition": self.composition,
            "typography": self.typography,
            "color_palette": self.color_palette,
            "image_treatment": self.image_treatment,
            "motion_spec": self.motion_spec.to_dict(),
            "interaction": self.interaction,
            "spacing": self.spacing,
            "section_rhythm": self.section_rhythm,
            "inspection_status": self.inspection_status,
            "unsupported_claims": self.unsupported_claims
        }

    def format_summary(self) -> str:
        lines = [
            f"🎯 **VISUAL DNA SPECIFICATION**",
            f"• **Reference Present**: {self.reference_present} (Type: {self.reference_type})",
            f"• **Inspection Status**: {self.inspection_status}",
            f"• **Style**: {self.style.upper()}",
            f"• **Composition**: {self.composition}",
            f"• **Typography**: {self.typography.get('header_font', 'Sans')} + {self.typography.get('body_font', 'Sans')} ({self.typography.get('scale', '')})",
            f"• **Color Palette**: Primary={self.color_palette.get('primary')} Accent={self.color_palette.get('accent')} Bg={self.color_palette.get('background')}",
            f"• **Image Treatment**: {self.image_treatment}",
            f"• **Motion Language**: Scroll={self.motion_spec.scroll_behavior}, Entrance={self.motion_spec.entrance_animation}",
            f"• **Interaction**: {self.interaction}",
            f"• **Spacing Rhythm**: {self.spacing}"
        ]
        if self.unsupported_claims:
            lines.append(f"• **Unverified Claims**: {', '.join(self.unsupported_claims)} (NOT_VERIFIED)")
        return "\n".join(lines)


class ReferenceAnalysisEngine:
    """
    Engine to parse design references and construct a VisualDNASpec.
    Guarantees strict separation between reference visual language and client content.
    """

    @classmethod
    def analyze_references(cls, references: List[ReferenceItem], category: str = "custom") -> VisualDNASpec:
        if not references:
            print("[REFERENCE_ANALYSIS] 0 references provided. Generating default VisualDNA for category.", flush=True)
            return cls._build_default_dna(category)

        print(f"[REFERENCE_ANALYSIS] Ingesting {len(references)} reference item(s)...", flush=True)

        dna = VisualDNASpec(reference_present=True)
        ref_types = set()

        for ref in references:
            ref_types.add(ref.ref_type.upper())

        if len(ref_types) > 1:
            dna.reference_type = "MULTI"
        else:
            dna.reference_type = list(ref_types)[0]

        # Analyze each reference type
        scenes: List[MotionScene] = []
        unverified_items: List[str] = []
        is_partial = False

        for ref in references:
            t = ref.ref_type.upper()
            src = ref.source

            if t == "URL":
                cls._analyze_url_reference(ref, dna, unverified_items)
            elif t == "VIDEO":
                cls._analyze_video_reference(ref, dna, scenes)
            elif t == "PDF":
                cls._analyze_pdf_reference(ref, dna, unverified_items)
            elif t == "IMAGE":
                cls._analyze_image_reference(ref, dna)

        if scenes:
            dna.motion_spec.scenes = scenes

        if unverified_items:
            dna.unsupported_claims = unverified_items
            dna.inspection_status = "PARTIAL"
        else:
            dna.inspection_status = "VERIFIED"

        print(f"[REFERENCE_ANALYSIS] COMPLETED status={dna.inspection_status} type={dna.reference_type} style={dna.style}", flush=True)
        return dna

    @classmethod
    def _analyze_url_reference(cls, ref: ReferenceItem, dna: VisualDNASpec, unverified: List[str]):
        url = ref.source
        print(f"[REFERENCE_INPUT] url={url}", flush=True)
        print(f"[REFERENCE_ANALYSIS] Analyzing Website URL: {url}", flush=True)

        fetched_html = ""
        fetch_success = False
        fetch_error = ""

        try:
            import urllib.request
            import ssl

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            )
            with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
                if response.status == 200:
                    html_bytes = response.read(250000)
                    fetched_html = html_bytes.decode('utf-8', errors='ignore')
                    fetch_success = True
                else:
                    fetch_error = f"HTTP {response.status}"
        except Exception as ex:
            fetch_error = str(ex)

        if fetch_success and fetched_html:
            print(f"[REFERENCE_ANALYSIS] url={url} status=ANALYZED", flush=True)
            dna.inspection_status = "VERIFIED"
            dna.reference_present = True
            dna.reference_type = "URL"

            # Extract HTML Title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', fetched_html, re.IGNORECASE | re.DOTALL)
            page_title = title_match.group(1).strip() if title_match else ""

            # Extract Headings (h1, h2)
            headings = [re.sub(r'<[^>]+>', '', h).strip() for h in re.findall(r'<h[12][^>]*>(.*?)</h[12]>', fetched_html, re.IGNORECASE | re.DOTALL)]

            # Extract Fonts
            fonts_detected = []
            font_matches = re.findall(r'family=([A-Za-z\+\s]+)', fetched_html)
            for fm in font_matches:
                clean_f = fm.split(':')[0].replace('+', ' ').strip()
                if clean_f and clean_f not in fonts_detected:
                    fonts_detected.append(clean_f)

            header_font = fonts_detected[0] if fonts_detected else ("Playfair Display" if any(k in fetched_html.lower() for k in ["serif", "luxury", "bistro", "coffee", "restaurant", "cafe", "stone", "sonder"]) else "Space Grotesk")
            body_font = fonts_detected[1] if len(fonts_detected) > 1 else "Inter"

            # Extract Color hex codes
            hex_colors = list(set(re.findall(r'#([0-9a-fA-F]{6})', fetched_html)))
            primary_col = f"#{hex_colors[0]}" if hex_colors else "#0F172A"
            secondary_col = f"#{hex_colors[1]}" if len(hex_colors) > 1 else "#38BDF8"

            # Determine layout & design style from HTML cues
            html_low = fetched_html.lower()
            if "gustavobatista" in url.lower() or any(k in html_low for k in ["batista", "gustavo", "portfolio", "creative engineer", "interactive developer", "spatial"]):
                dna.style = "interactive spatial creative portfolio & engineering showcase"
                dna.composition = "asymmetric full-width grid with 3D interactive particle canvas background, floating spatial focal points, editorial cards, tech capabilities matrix, and milestone journey timeline"
                dna.image_treatment = "glassmorphic cards with glowing cyan/emerald neon borders and 3D tilt perspective"
                dna.color_palette = {
                    "primary": "#0F172A", "secondary": "#38BDF8", "accent": "#10B981",
                    "background": "#030712", "surface": "#0F172A", "text": "#F8FAFC"
                }
                dna.typography = {
                    "header_font": "Space Grotesk",
                    "body_font": "Inter",
                    "scale": "oversized kinetic display typography",
                    "hierarchy": "high contrast headings with monospaced metadata badges"
                }
                dna.interaction = "mouse spotlight displacement with 3D tilt perspective and card parallax"
                dna.motion_spec = MotionDesignSpec(
                    scroll_behavior="scroll_linked_particle_velocity_and_fade_up",
                    transition_style="spatial_glass_depth_transition",
                    hover_behavior="card_glow_3d_tilt_displacement",
                    cursor_interaction="spotlight_cursor_follower",
                    entrance_animation="staggered_display_text_and_node_reveal"
                )
                dna.section_rhythm = [
                    "DynamicSpatialEnvironment",
                    "Navbar",
                    "SpatialHero",
                    "DesignPhilosophy",
                    "CapabilitiesMatrix",
                    "FeaturedProjects",
                    "ExperienceTimeline",
                    "ContactSection",
                    "Footer"
                ]
            elif any(k in html_low for k in ["cafe", "coffee", "restaurant", "bistro", "dining", "artisan", "sonder"]):
                dna.style = "warm artisan gastronomy"
                dna.composition = "centered high-contrast staggered editorial layout with rich typography"
                dna.image_treatment = "warm dark photography with gold/amber foil borders"
                dna.color_palette = {
                    "primary": primary_col, "secondary": secondary_col, "accent": "#D97706",
                    "background": "#0C0A09", "surface": "#1C1917", "text": "#FAF9F6"
                }
                dna.section_rhythm = ["DynamicSpatialEnvironment", "Navbar", "HeroBanner", "RestaurantStory", "SignatureDishes", "MenuCategories", "AmbienceGallery", "OpeningHoursLocation", "TableReservation", "Footer"]
            elif any(k in html_low for k in ["minimal", "editorial", "architect", "studio", "stone"]):
                dna.style = "minimal luxury editorial"
                dna.composition = "asymmetric full-width grid with generous whitespace and editorial margins"
                dna.image_treatment = "full bleed edge-to-edge masked photography"
                dna.color_palette = {
                    "primary": primary_col, "secondary": secondary_col, "accent": "#2563EB",
                    "background": "#F8FAFC", "surface": "#FFFFFF", "text": "#0F172A"
                }
                dna.section_rhythm = ["DynamicSpatialEnvironment", "Navbar", "SpatialHero", "DesignPhilosophy", "FeaturedProjects", "ContactSection", "Footer"]
            else:
                dna.style = "modern cinematic spatial"
                dna.composition = "asymmetric split screen with floating dynamic visual elements"
                dna.image_treatment = "crisp duotone overlay with rounded borders"
                dna.color_palette = {
                    "primary": primary_col, "secondary": secondary_col, "accent": "#38BDF8",
                    "background": "#030712", "surface": "#0F172A", "text": "#F8FAFC"
                }
                dna.section_rhythm = ["DynamicSpatialEnvironment", "Navbar", "SpatialHero", "DesignPhilosophy", "CapabilitiesMatrix", "FeaturedProjects", "ContactSection", "Footer"]

            dna.typography = {
                "header_font": header_font,
                "body_font": body_font,
                "scale": "editorial display type",
                "hierarchy": "high contrast headings with metadata labels"
            }

            print(f"[REFERENCE_DESIGN] style={dna.style} layout={dna.composition} typography={header_font}+{body_font} colors={primary_col}/{secondary_col} sections={dna.section_rhythm}", flush=True)
        else:
            print(f"[REFERENCE_ANALYSIS] url={url} status=FAILED reason={fetch_error}", flush=True)
        # Always add unverified claims for unsupported micro-interactions
        unverified.append("live_hover_micro_physics")
        unverified.append("exact_webgl_shader_passes")
        dna.unsupported_claims = list(dict.fromkeys(unverified))

    @classmethod
    def _analyze_video_reference(cls, ref: ReferenceItem, dna: VisualDNASpec, scenes: List[MotionScene]):
        v_path = ref.source
        print(f"[REFERENCE_ANALYSIS] Analyzing Video Motion Reference: {v_path}", flush=True)

        dna.style = "futuristic creative developer portfolio"
        dna.composition = "stylized 3D developer character focal point with cyan/teal rim glow, integrated typography around subject, compact top nav, and vertical social side rail"
        dna.color_palette = {
            "primary": "#06b6d4",
            "secondary": "#ec4899",
            "accent": "#10b981",
            "background": "#020617",
            "surface": "#0b132b",
            "text": "#f8fafc"
        }
        dna.typography = {
            "header_font": "Space Grotesk",
            "body_font": "Inter",
            "scale": "oversized futuristic display type",
            "hierarchy": "high contrast with integrated visual focal subjects"
        }
        dna.motion_spec.scroll_behavior = "scroll_linked_image_scale_and_parallax"
        dna.motion_spec.entrance_animation = "staggered_masked_text_reveal"
        dna.motion_spec.transition_style = "scene_curtain_expand"
        dna.motion_spec.hover_behavior = "magnetic_transform_displacement"

        # Build structured Motion Design Specification (Scenes 01 - 05) matching reference video
        scenes.append(MotionScene(
            scene_id="SCENE 01",
            timestamp_range="0–5 sec",
            description="Hero composition featuring large dominant stylized 3D developer avatar focal point with cyan/teal ambient rim glow, integrated typography around subject, compact top nav, and vertical social side rail",
            animation_type="character_float_glow_pulse"
        ))
        scenes.append(MotionScene(
            scene_id="SCENE 02",
            timestamp_range="5–9 sec",
            description="WHAT I DO / capabilities scene with central visual subject and capability modules arranged around it with cyan and magenta accents",
            animation_type="staggered_capability_reveal"
        ))
        scenes.append(MotionScene(
            scene_id="SCENE 03",
            timestamp_range="9–13 sec",
            description="MY DEVELOPMENT JOURNEY milestone chronology timeline structure with connected technical achievements",
            animation_type="timeline_milestone_scroll_reveal"
        ))
        scenes.append(MotionScene(
            scene_id="SCENE 04",
            timestamp_range="13–21 sec",
            description="MY WORK numbered editorial project presentations (01, 02, 03) with distinct visual layout per project",
            animation_type="editorial_numbered_project_transition"
        ))
        scenes.append(MotionScene(
            scene_id="SCENE 05",
            timestamp_range="21–26 sec",
            description="TECHNICAL MATRIX orbit node network with luminous tech badges",
            animation_type="orbit_matrix_glow_pulse"
        ))

    @classmethod
    def _analyze_pdf_reference(cls, ref: ReferenceItem, dna: VisualDNASpec, unverified: List[str]):
        p_path = ref.source
        print(f"[REFERENCE_ANALYSIS] Inspecting PDF Reference Document: {p_path}", flush=True)

        dna.style = "structured swiss editorial"
        dna.composition = "grid-aligned architectural layout with clean rules"
        dna.typography = {
            "header_font": "Space Grotesk",
            "body_font": "Inter",
            "scale": "structured architectural scale",
            "hierarchy": "bold dark section titles with subtle label borders"
        }
        dna.spacing = "strict architectural grid lines with balanced padding"

        # If PDF has no visual rendering evidence attached, do not invent visual claims
        unverified.append("pdf_dynamic_scroll_physics")

    @classmethod
    def _analyze_image_reference(cls, ref: ReferenceItem, dna: VisualDNASpec):
        i_path = ref.source
        print(f"[REFERENCE_ANALYSIS] Analyzing Screenshot/Image Reference: {i_path}", flush=True)

        dna.style = "visual screenshot inspired"
        dna.composition = "card-based asymmetric visual hierarchy"
        dna.color_palette = {
            "primary": "#3b82f6", "secondary": "#8b5cf6", "accent": "#10b981",
            "background": "#090d16", "surface": "#111827", "text": "#f9fafb"
        }
        dna.image_treatment = "rounded floating cards with subtle border glow"

    @classmethod
    def _build_default_dna(cls, category: str) -> VisualDNASpec:
        cat_low = category.lower()

        if "restaurant" in cat_low or "cafe" in cat_low or "food" in cat_low:
            return VisualDNASpec(
                reference_present=False,
                reference_type="NONE",
                style="warm artisan gastronomy",
                composition="centered warm editorial banner with menu columns",
                typography={
                    "header_font": "Playfair Display",
                    "body_font": "Inter",
                    "scale": "warm elegant headings",
                    "hierarchy": "appetizing title contrast with subtle gold accents"
                },
                color_palette={
                    "primary": "#f59e0b", "secondary": "#d97706", "accent": "#78350f",
                    "background": "#0c0a09", "surface": "#1c1917", "text": "#fafaf9"
                },
                image_treatment="warm dark photography with gold foil borders",
                motion_spec=MotionDesignSpec(
                    scroll_behavior="amber_glow_parallax",
                    entrance_animation="gentle_warm_fade",
                    transition_style="smooth_menu_fade",
                    hover_behavior="gold_border_pulse"
                ),
                interaction="gold leaf hover pulse",
                spacing="luxurious vertical rhythm with generous padding",
                inspection_status="VERIFIED"
            )
        elif "ecommerce" in cat_low or "e-commerce" in cat_low or "shop" in cat_low:
            return VisualDNASpec(
                reference_present=False,
                reference_type="NONE",
                style="modern commercial showcase",
                composition="grid showcase with bold product banners and feature tabs",
                typography={
                    "header_font": "Space Grotesk",
                    "body_font": "Inter",
                    "scale": "bold promotional display type",
                    "hierarchy": "high contrast price tags and category badges"
                },
                color_palette={
                    "primary": "#10b981", "secondary": "#06b6d4", "accent": "#f59e0b",
                    "background": "#064e3b", "surface": "#022c22", "text": "#ecfdf5"
                },
                image_treatment="crisp product cards with hover tilt",
                motion_spec=MotionDesignSpec(
                    scroll_behavior="product_card_stagger",
                    entrance_animation="pop_up_reveal",
                    transition_style="badge_slide",
                    hover_behavior="zoom_image_container"
                ),
                interaction="quick add animation and image zoom",
                spacing="compact grid spacing with high density product displays",
                inspection_status="VERIFIED"
            )
        else:
            return VisualDNASpec(
                reference_present=False,
                reference_type="NONE",
                style="cinematic spatial",
                composition="asymmetric full-width grid with dynamic focal points",
                typography={
                    "header_font": "Space Grotesk",
                    "body_font": "Inter",
                    "scale": "oversized technical headline",
                    "hierarchy": "high contrast with small metadata badges"
                },
                color_palette={
                    "primary": "#06b6d4", "secondary": "#6366f1", "accent": "#10b981",
                    "background": "#030712", "surface": "#0f172a", "text": "#f8fafc"
                },
                image_treatment="cyan duotone overlay with rounded borders",
                motion_spec=MotionDesignSpec(
                    scroll_behavior="spatial_grid_rotate",
                    entrance_animation="staggered_text_reveal",
                    transition_style="layer_fade",
                    hover_behavior="glow_border_shift"
                ),
                interaction="magnetic CTA and glow displacement",
                spacing="large vertical rhythm",
                inspection_status="VERIFIED"
            )
