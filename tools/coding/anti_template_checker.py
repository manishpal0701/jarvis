"""
tools/coding/anti_template_checker.py
Anti-Template System for Jarvis Reference-Driven Website Builder.

Enforces strict anti-template checks before code generation:
- Prevents repetitive generation of fallback developer portfolio templates.
- Rejects candidate designs containing excessive reuse of banned design tokens:
  - Oversized background name / MANISH typography
  - Developer terminal widget
  - Particle canvas background
  - Standard glassmorphism card grid
  - Marquee strip
  - Gradient CTA with cyan glow
- Forces fresh composition generation when similarity score > 0.35.
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AntiTemplateCheckResult:
    similarity_score: float
    is_rejected: bool
    design_regeneration_required: bool
    rejected_reasons: List[str]
    banned_tokens_detected: List[str]
    composition_family: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "similarity_score": round(self.similarity_score, 3),
            "is_rejected": self.is_rejected,
            "design_regeneration_required": self.design_regeneration_required,
            "rejected_reasons": self.rejected_reasons,
            "banned_tokens_detected": self.banned_tokens_detected,
            "composition_family": self.composition_family
        }


class AntiTemplateChecker:
    """
    Evaluates planned site composition and design tokens against banned template patterns.
    Triggers fresh composition generation if similarity threshold is breached.
    """

    BANNED_TOKENS = {
        "oversized_background_typography": ["oversized manish", "manish background", "oversized name", "manish typography", "bg-text-manish"],
        "developer_terminal_widget": ["terminal widget", "developer terminal", "code editor container", "bash_prompt", "terminal_box"],
        "particle_canvas_background": ["particle canvas", "cyber particle bg", "particlesjs", "interactive_particles"],
        "glassmorphism_card_grid": ["glassmorphism card grid", "standard_glass_card", "border-cyan-500/20 backdrop-blur-md"],
        "marquee_strip": ["tech marquee", "infinite marquee strip", "marquee_container"],
        "cyan_gradient_cta": ["bg-gradient-to-r from-cyan-500 to-blue-600", "cyan glow cta", "bold_glow_gradient"],
        "developer_portfolio_layout": ["developer portfolio template", "hero_asymmetric_terminal", "a_modern_dark_luxury_developer_portfolio"]
    }

    SIMILARITY_THRESHOLD = 0.35

    @classmethod
    def evaluate_composition(
        cls,
        planned_composition: Dict[str, Any],
        visual_dna: Any = None,
        category: str = "custom"
    ) -> AntiTemplateCheckResult:
        """
        Evaluates planned composition and visual direction.
        Returns AntiTemplateCheckResult.
        """
        reasons = []
        detected_tokens = []
        similarity = 0.05  # Base baseline score

        comp_str = json.dumps(planned_composition).lower()
        if visual_dna:
            if hasattr(visual_dna, "to_dict"):
                comp_str += " " + json.dumps(visual_dna.to_dict()).lower()
            else:
                comp_str += " " + str(visual_dna).lower()

        # Check banned tokens
        for token_cat, patterns in cls.BANNED_TOKENS.items():
            for pat in patterns:
                if pat in comp_str:
                    detected_tokens.append(f"{token_cat}:{pat}")
                    reasons.append(f"Excessive reuse of banned template element: '{pat}' ({token_cat})")
                    similarity += 0.20
                    break

        # Check section ordering similarity to default developer portfolio
        category_str = category.value if hasattr(category, 'value') else str(category or "")
        cat_low = category_str.lower()

        section_order = planned_composition.get("section_order", []) if isinstance(planned_composition, dict) else []
        if section_order == ["Navbar", "Hero", "About", "Skills", "Projects", "Contact", "Footer"]:
            if cat_low not in ["developer_portfolio", "personal_portfolio", "portfolio", "creative_portfolio"]:
                similarity += 0.35
                reasons.append("Default developer portfolio section ordering detected for non-portfolio website category")

        # Category-specific template check (Strict anti-portfolio gate for non-portfolio categories)
        if cat_low not in ["developer_portfolio", "personal_portfolio", "portfolio"]:
            portfolio_keywords = ["developerhero", "technicalbio", "skillmatrix", "featuredprojects", "codeterminal", "manish", "flutter developer", "terminal widget"]
            for kw in portfolio_keywords:
                if kw in comp_str:
                    similarity += 0.50
                    reasons.append(f"Forbidden developer portfolio element '{kw}' detected in non-portfolio category '{category}'")
                    break


        is_rejected = similarity > cls.SIMILARITY_THRESHOLD or len(detected_tokens) > 0
        family = planned_composition.get("family", "CUSTOM_FRESH_FAMILY")

        print(f"[ANTI_TEMPLATE_CHECK] similarity_score={similarity:.3f} threshold={cls.SIMILARITY_THRESHOLD} rejected={is_rejected} tokens={len(detected_tokens)}", flush=True)

        return AntiTemplateCheckResult(
            similarity_score=similarity,
            is_rejected=is_rejected,
            design_regeneration_required=is_rejected,
            rejected_reasons=reasons,
            banned_tokens_detected=detected_tokens,
            composition_family=family
        )

    @classmethod
    def inspect_generated_code(
        cls,
        code_dict: Dict[str, str],
        category: str = "custom"
    ) -> AntiTemplateCheckResult:
        """
        Inspects generated TSX files to ensure no placeholder component names are rendered as text headers.
        """
        reasons = []
        detected_tokens = []
        similarity = 0.05

        placeholder_patterns = [
            "businesshero —", "businessoverview —", "businessservices —",
            "whychooseus —", "businessprocess —", "producthero —",
            "problemsolution —", "keyfeatures —", "howitworks —",
            "spatial component //", "raw block //", "organic businesshero",
            "organic businessoverview", "raw block //"
        ]

        full_code = " ".join(code_dict.values()).lower() if isinstance(code_dict, dict) else str(code_dict).lower()

        for pat in placeholder_patterns:
            if pat in full_code:
                detected_tokens.append(f"placeholder_ui:{pat}")
                reasons.append(f"Internal component identifier placeholder detected in rendered text: '{pat}'")
                similarity += 0.50

        category_str = category.value if hasattr(category, 'value') else str(category or "")
        cat_low = category_str.lower()
        if cat_low not in ["developer_portfolio", "personal_portfolio", "portfolio"]:

            portfolio_keywords = ["developerhero", "technicalbio", "skillmatrix", "featuredprojects", "codeterminal", "manish", "flutter developer"]
            for kw in portfolio_keywords:
                if kw in full_code:
                    similarity += 0.50
                    reasons.append(f"Forbidden developer portfolio element '{kw}' detected in non-portfolio category '{category}'")
                    break

        is_rejected = similarity > cls.SIMILARITY_THRESHOLD or len(detected_tokens) > 0

        return AntiTemplateCheckResult(
            similarity_score=similarity,
            is_rejected=is_rejected,
            design_regeneration_required=is_rejected,
            rejected_reasons=reasons,
            banned_tokens_detected=detected_tokens,
            composition_family="CODE_INSPECTION_CHECK"
        )

    @classmethod
    def generate_fresh_composition(cls, category: str, visual_dna: Any = None, attempt: int = 1) -> Dict[str, Any]:
        """
        Generates a fresh composition layout guarantees distinct structure for the category.
        """
        cat_low = category.lower()

        if "restaurant" in cat_low or "cafe" in cat_low or "food" in cat_low:
            return {
                "family": "GASTRONOMY_WARM_ARTISAN",
                "hero_structure": "centered_editorial_banner_with_signature_dish",
                "background_system": "candlelit_warm_ambience",
                "navigation_style": "minimal_top_bar_with_reservation_cta",
                "card_style": "culinary_gold_framed_card",
                "button_style": "gold_leaf_filled_button",
                "section_order": ["Navbar", "Hero", "SignatureDishes", "MenuTabbed", "OurStory", "AmbienceGallery", "ReservationContact", "Footer"],
                "typography_pair": "Playfair Display + Inter",
                "color_palette": {
                    "primary": "#f59e0b", "secondary": "#d97706", "accent": "#78350f",
                    "background": "#0c0a09", "surface": "#1c1917", "text": "#fafaf9"
                }
            }
        elif "ecommerce" in cat_low or "e-commerce" in cat_low or "shop" in cat_low or "store" in cat_low:
            return {
                "family": "COMMERCIAL_PRODUCT_SHOWCASE",
                "hero_structure": "split_hero_product_spotlight_with_badge",
                "background_system": "soft_emerald_organic_canvas",
                "navigation_style": "pill_floating_nav_with_cart_badge",
                "card_style": "emerald_soft_glow_card",
                "button_style": "rounded_emerald_pill_button",
                "section_order": ["Navbar", "Hero", "CategoriesGrid", "BestSellers", "ValueProps", "Reviews", "ContactFooter"],
                "typography_pair": "Outfit + Inter",
                "color_palette": {
                    "primary": "#10b981", "secondary": "#06b6d4", "accent": "#34d399",
                    "background": "#022c22", "surface": "#064e3b", "text": "#ecfdf5"
                }
            }
        elif "agency" in cat_low or "company" in cat_low or "corporate" in cat_low:
            return {
                "family": "SWISS_ARCHITECTURAL_CORPORATE",
                "hero_structure": "asymmetric_left_aligned_grid_column",
                "background_system": "architectural_blueprint_grid",
                "navigation_style": "border_bottom_clean_header",
                "card_style": "clean_architectural_border_box",
                "button_style": "minimal_black_solid_button",
                "section_order": ["Navbar", "Hero", "Capabilities", "CaseStudies", "MetricsGrid", "ClientTestimonials", "ContactSection", "Footer"],
                "typography_pair": "Space Grotesk + Inter",
                "color_palette": {
                    "primary": "#2563eb", "secondary": "#0f172a", "accent": "#3b82f6",
                    "background": "#f8fafc", "surface": "#ffffff", "text": "#090d16"
                }
            }
        else:
            # Alternate directions based on attempt index
            directions = [
                {
                    "family": "FAMILY_B_SWISS_EDITORIAL",
                    "hero_structure": "editorial_typography_headline_left",
                    "background_system": "stark_white_architectural_grid",
                    "navigation_style": "border_bottom_clean",
                    "card_style": "thin_border_card",
                    "button_style": "minimal_flat_button",
                    "section_order": ["Navbar", "Hero", "About", "Services", "WorkShowcase", "Contact"],
                    "typography_pair": "Inter + Fira Code",
                    "color_palette": {"primary": "#2563eb", "background": "#f8fafc", "surface": "#ffffff", "text": "#090d16"}
                },
                {
                    "family": "FAMILY_C_EXPERIMENTAL_BRUTALIST",
                    "hero_structure": "raw_overlapping_block_headline",
                    "background_system": "noise_grain_mesh",
                    "navigation_style": "raw_border_banner",
                    "card_style": "raw_thick_volt_box",
                    "button_style": "raw_block_button",
                    "section_order": ["Navbar", "Hero", "Manifesto", "ServicesStripe", "ProjectsStaggered", "RawContact"],
                    "typography_pair": "Space Grotesk + JetBrains Mono",
                    "color_palette": {"primary": "#ccff00", "background": "#000000", "surface": "#111111", "text": "#ffffff"}
                },
                {
                    "family": "FAMILY_E_EDITORIAL_LUXURY",
                    "hero_structure": "centered_oversized_serif_headline",
                    "background_system": "warm_mahogany_glow",
                    "navigation_style": "minimal_gold_top_rule",
                    "card_style": "gold_foil_border_card",
                    "button_style": "gold_leaf_button",
                    "section_order": ["Navbar", "Hero", "Narrative", "Offerings", "Gallery", "LuxuryContact"],
                    "typography_pair": "Playfair Display + Inter",
                    "color_palette": {"primary": "#f59e0b", "background": "#0c0a09", "surface": "#1c1917", "text": "#fafaf9"}
                }
            ]
            return directions[(attempt - 1) % len(directions)]
