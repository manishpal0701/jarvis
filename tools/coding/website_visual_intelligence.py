"""
tools/coding/website_visual_intelligence.py
Website Asset & Visual Intelligence Layer.
Converts research context + user brief into a structured VisualWebsitePlan
with asset specifications, content priorities, responsive strategies, and source traceability.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class AssetRequirement:
    purpose: str = "hero"  # hero, product, service, feature, background, testimonial, logo, icon
    type: str = "image"    # image, icon, vector
    query: str = ""
    source_requirement: str = "public/verified"
    required: bool = True

@dataclass
class ContentPriority:
    primary: List[str] = field(default_factory=list)
    secondary: List[str] = field(default_factory=list)
    tertiary: List[str] = field(default_factory=list)

@dataclass
class ResponsiveRequirement:
    desktop: str = "Full navigation, multi-column grid, expanded visual hero"
    tablet: str = "2-column layout, touch target optimization, adaptive hero"
    mobile: str = "Stacked 1-column layout, drawer menu, touch-friendly CTAs"

@dataclass
class SourceTrace:
    fact: str = ""
    source: str = ""

@dataclass
class VisualWebsitePlan:
    design_direction: str = "Modern clean responsive aesthetic"
    color_direction: str = "Balanced neutral dark slate and cyan accents"
    typography_direction: str = "Modern sans-serif typography (Inter / System UI)"
    layout_style: str = "Multi-section responsive grid container"
    hero_strategy: str = "Impactful headline, value proposition statement, and primary CTA"
    section_strategy: str = "Structured sections (Navbar, Hero, Features/Products, About, Contact, Footer)"
    cta_strategy: str = "High-contrast action buttons for primary goals"
    image_strategy: str = "Category-matched high-resolution imagery and fallback visual cards"
    asset_requirements: List[AssetRequirement] = field(default_factory=list)
    responsive_requirements: ResponsiveRequirement = field(default_factory=ResponsiveRequirement)
    animation_direction: str = "Subtle CSS transitions and smooth section scrolling"
    animation_level: str = "medium"       # low, medium, high
    three_d_level: str = "medium"         # none, low, medium, high
    glassmorphism: bool = True
    parallax: bool = True
    cursor_effects: bool = True
    particles: bool = False
    reduced_motion_support: bool = True
    hero_3d_object_concept: str = "RotatingCore"
    spatial_depth_layers: List[str] = field(default_factory=lambda: ["depth-bg", "depth-atmosphere", "depth-geometry", "depth-object", "depth-ui", "depth-fg"])
    mouse_parallax_enabled: bool = True
    scroll_storytelling_style: str = "asymmetric_flow"
    section_composition_types: List[str] = field(default_factory=lambda: ["hero_asymmetric", "services_split_sticky", "tech_matrix", "solutions_layered_cards", "projects_editorial", "why_us_pillar_grid", "contact_spatial_form"])
    brand_consistency_notes: List[str] = field(default_factory=list)
    content_priority: ContentPriority = field(default_factory=ContentPriority)
    source_traceability: List[SourceTrace] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WebsiteVisualIntelligence:
    """
    Website Visual & Asset Intelligence Agent.
    Converts research context + user brief into a structured VisualWebsitePlan
    before UI code generation. Includes source traceability and graceful fallback safety.
    """

    @classmethod
    def generate_plan(cls, brief: Any, research_context: Optional[Dict[str, Any]] = None, user_command: str = "") -> VisualWebsitePlan:
        """
        Generates a structured VisualWebsitePlan from brief, research context, and user command.
        Emits telemetry logs: [VISUAL_INTELLIGENCE_START], [VISUAL_INTELLIGENCE_PLAN], etc.
        Falls back safely on missing research or errors.
        """
        print("[VISUAL_INTELLIGENCE_START] Generating visual intelligence plan...", flush=True)

        try:
            plan = VisualWebsitePlan()

            # 1. Parse research context if available
            res_dict = {}
            if isinstance(research_context, dict):
                res_dict = research_context
            elif hasattr(research_context, 'to_dict'):
                res_dict = research_context.to_dict()

            entity_name = res_dict.get("official_name") or res_dict.get("entity") or ""
            desc = res_dict.get("description") or ""
            category = res_dict.get("category") or (brief.category if hasattr(brief, 'category') and brief.category else "custom")
            official_url = res_dict.get("official_url") or ""
            raw_sources = res_dict.get("sources") or []

            # Extract source traceability records
            if entity_name and raw_sources:
                plan.source_traceability.append(SourceTrace(fact=f"Official Entity: {entity_name}", source=raw_sources[0]))
            if official_url:
                plan.source_traceability.append(SourceTrace(fact=f"Official Web URL: {official_url}", source=official_url))

            # 2. Company / Topic specific Visual Intelligence Adaptation
            cat_lower = str(category).lower()
            cmd_lower = str(user_command).lower()
            entity_lower = str(entity_name).lower()

            if "tesla" in entity_lower or "electric vehicle" in desc.lower() or "automotive" in desc.lower():
                plan.design_direction = "Dark luxury automotive tech aesthetic with glassmorphic cards and glowing red accents"
                plan.color_direction = "Deep Charcoal/Black (#0c0c0e), Electric Red (#e82127), and Pure White (#ffffff)"
                plan.typography_direction = "Futuristic geometric sans-serif headings with high legibility body"
                plan.layout_style = "Full-bleed hero banner, interactive 3-column product showcase, and minimalist feature grid"
                plan.hero_strategy = "Bold tagline 'The Future of Sustainable Energy', background vehicle visual, and 'Explore Vehicles' CTA"
                plan.animation_level = "high"
                plan.three_d_level = "high"
                plan.glassmorphism = True
                plan.cursor_effects = True
                plan.brand_consistency_notes = [
                    "Minimalist high-contrast dark theme reflecting Tesla clean energy branding",
                    "No invented claims — highlight electric mobility, battery storage, and solar innovation"
                ]
                plan.content_priority.primary = ["Vehicle Innovation Headline", "Explore Models CTA", "Sustainable Energy Mission"]
                plan.content_priority.secondary = ["Electric Vehicles (Model S, 3, X, Y)", "Supercharger & Energy Network"]
                plan.content_priority.tertiary = ["Company Overview", "Contact & Location", "Footer Links"]

                plan.asset_requirements = [
                    AssetRequirement(purpose="hero", type="image", query="Tesla Electric Vehicle Dark Banner", required=True),
                    AssetRequirement(purpose="product", type="image", query="Electric Sedan Showcase", required=True),
                    AssetRequirement(purpose="service", type="image", query="Supercharger Network Station", required=False)
                ]

            elif cat_lower == "restaurant" or "food" in cmd_lower or "dining" in desc.lower() or "restaurant" in cmd_lower:
                plan.design_direction = "Warm mahogany and gold gastronomy theme with rich culinary photography"
                plan.color_direction = "Mahogany Stone (#1c1917), Warm Amber (#f59e0b), and Gold (#d97706)"
                plan.typography_direction = "Playfair Display luxury serif headings with warm clean body text"
                plan.hero_strategy = "Appetizing culinary hero image, 'Reserve Table' primary CTA, 'View Menu' secondary CTA"
                plan.animation_level = "medium"
                plan.three_d_level = "low"
                plan.glassmorphism = False
                plan.cursor_effects = False
                plan.brand_consistency_notes = ["Warm candlelit ambience aesthetic focus"]
                plan.content_priority.primary = ["Culinary Artistry Headline", "Table Reservation CTA"]
                plan.content_priority.secondary = ["Signature Dishes Grid", "Tabbed Interactive Menu"]
                plan.content_priority.tertiary = ["Opening Hours & Location", "Restaurant Story", "Footer Links"]

                plan.asset_requirements = [
                    AssetRequirement(purpose="hero", type="image", query="Gourmet Culinary Banner", required=True),
                    AssetRequirement(purpose="product", type="image", query="Signature Dish Photo", required=True)
                ]

            elif "nike" in entity_lower or "sportswear" in desc.lower() or "athletic" in desc.lower():
                plan.design_direction = "High-energy bold athletic aesthetic with oversized typography and vibrant contrast"
                plan.color_direction = "Pitch Black (#000000), Bright Volt (#ccff00), and Pure White (#ffffff)"
                plan.typography_direction = "Ultra-bold condensed sans-serif headings for high impact"
                plan.hero_strategy = "High-impact athletic imagery with 'Just Do It' energy and Shop Collection CTA"
                plan.animation_level = "high"
                plan.three_d_level = "medium"
                plan.brand_consistency_notes = ["Bold athletic visual hierarchy with high-contrast typography"]
                plan.content_priority.primary = ["Bold Performance Headline", "Shop Latest Collection CTA"]
                plan.content_priority.secondary = ["Featured Sportswear & Footwear", "Athletic Innovations"]
                plan.content_priority.tertiary = ["Brand Story", "Customer Support", "Footer Links"]

                plan.asset_requirements = [
                    AssetRequirement(purpose="hero", type="image", query="High-performance Athletic Runner", required=True),
                    AssetRequirement(purpose="product", type="image", query="Modern Running Sneakers", required=True)
                ]

            elif cat_lower == "portfolio" or "developer" in cmd_lower or "portfolio" in cmd_lower:
                plan.design_direction = "Dark luxury developer aesthetic with glassmorphic panels and glowing cyan accents"
                plan.color_direction = "Deep Slate (#0f172a), Cyan Glow (#06b6d4), and Emerald Accent (#10b981)"
                plan.typography_direction = "Inter / JetBrains Mono for code blocks and terminal elements"
                plan.hero_strategy = "Developer avatar, tagline, live code/terminal widget, and 'View Projects' CTA"
                plan.animation_level = "high"
                plan.three_d_level = "high"
                plan.glassmorphism = True
                plan.cursor_effects = True
                plan.brand_consistency_notes = ["Technical developer aesthetic with glassmorphic cards"]
                plan.content_priority.primary = ["Developer Name & Specialty", "Core Tech Stack", "View Projects CTA"]
                plan.content_priority.secondary = ["Featured Projects Grid", "Skills & Experience Timeline"]
                plan.content_priority.tertiary = ["About Developer", "Contact Form", "Social Links"]

                plan.asset_requirements = [
                    AssetRequirement(purpose="hero", type="image", query="Developer Profile Avatar", required=True),
                    AssetRequirement(purpose="product", type="image", query="AI Assistant Platform Thumbnail", required=True)
                ]

            else:
                # Technology / General Business Visual Plan
                plan.design_direction = "Modern, clean, high-conversion professional technology aesthetic"
                plan.color_direction = "Navy Slate (#0f172a), Cyan Glow (#06b6d4), and Pure White (#ffffff)"
                plan.typography_direction = "Inter / System UI sans-serif headings and body text"
                plan.animation_level = "high" if any(k in cmd_lower for k in ["3d", "animated", "inurum", "futuristic"]) else "medium"
                plan.three_d_level = "high" if any(k in cmd_lower for k in ["3d", "animated", "inurum", "futuristic"]) else "medium"
                plan.glassmorphism = True
                plan.cursor_effects = True if plan.animation_level == "high" else False
                plan.layout_style = "Containerized responsive grid sections with 3D perspective hero"
                plan.hero_strategy = "Impactful value proposition statement, secondary subtitle, and Get Started CTA"
                plan.content_priority.primary = ["Brand Value Proposition Headline", "Get Started CTA"]
                plan.content_priority.secondary = ["Core Business Services", "Key Features Grid"]
                plan.content_priority.tertiary = ["About Us", "Contact Form", "Footer Links"]

                plan.asset_requirements = [
                    AssetRequirement(purpose="hero", type="image", query="Modern Professional Office Banner", required=True)
                ]

            print(f"[VISUAL_INTELLIGENCE_PLAN] Direction: '{plan.design_direction}'", flush=True)
            print(f"[VISUAL_INTELLIGENCE_ASSET_PLAN] Requirements ({len(plan.asset_requirements)} items): {[a.purpose for a in plan.asset_requirements]}", flush=True)
            print(f"[VISUAL_INTELLIGENCE_SOURCE_TRACE] Traceability records ({len(plan.source_traceability)} items)", flush=True)
            print("[VISUAL_INTELLIGENCE_END] Visual intelligence plan generation completed.", flush=True)

            return plan

        except Exception as e:
            print(f"[VISUAL_INTELLIGENCE_FALLBACK] Visual planning notice: {e}. Returning safe minimal visual plan.", flush=True)
            fallback_plan = VisualWebsitePlan()
            print("[VISUAL_INTELLIGENCE_END] Safe minimal visual plan returned.", flush=True)
            return fallback_plan
