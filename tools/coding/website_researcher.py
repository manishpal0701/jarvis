import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from ai.model_router import ModelRouter

@dataclass
class WebsiteResearchSpecification:
    website_type: str = "portfolio"
    target_audience: str = "Tech leads, recruiters, and clients"
    visual_direction: str = "Dark luxury developer aesthetic with glassmorphism and code previews"
    sections: List[str] = field(default_factory=list)
    content_requirements: Dict[str, str] = field(default_factory=dict)
    design_patterns: List[str] = field(default_factory=list)
    asset_requirements: List[str] = field(default_factory=list)
    interaction_requirements: List[str] = field(default_factory=list)
    responsive_requirements: List[str] = field(default_factory=list)

class WebsiteResearcher:
    """
    Website Researcher Agent.
    Uses qwen3:8b model to conduct category-specific UX research and generate a
    structured WebsiteResearchSpecification for the requested website brief.
    """

    @classmethod
    def conduct_research(cls, prompt: str, category: str = "portfolio") -> WebsiteResearchSpecification:
        cat = category.lower().strip()
        model_name = ModelRouter.get_instance().get_model_for_task("website_research")

        if cat == "portfolio" or "developer" in prompt.lower() or "engineer" in prompt.lower():
            sections = ["Navbar", "Hero", "About", "Skills", "Featured Projects", "Experience", "Contact", "Footer"]
            content_reqs = {
                "Hero": "Developer headline, tagline, primary/secondary CTA, live terminal code snippet preview, status badge.",
                "About": "Developer biography, core engineering focus, specialization in AI and full-stack systems.",
                "Skills": "Grid of technologies grouped by category with skill level tags.",
                "Projects": "3-column grid of glass cards showing real project thumbnails, tech stack pill badges, and demo links.",
                "Experience": "Timeline of engineering roles and achievements.",
                "Contact": "Interactive contact form, email address, and social links."
            }
            design_patterns = ["Glassmorphism", "Dark Slate Background", "Gradient Glow Headings", "Tech Pill Badges", "Interactive Terminal Mockup"]
            asset_reqs = ["Developer Profile Avatar", "Jarvis AI Assistant Visual", "AI Video Editing Visual", "Flutter Mobile App Visual"]
            interaction_reqs = ["Navbar Smooth Scrolling", "Glass Card Hover Elevate", "Form Submission State", "Mobile Drawer Menu"]
            responsive_reqs = ["Desktop (1440px): 3-column project grid", "Tablet (768px): 2-column grid", "Mobile (390px): 1-column stacked layout with toggle menu"]

            return WebsiteResearchSpecification(
                website_type="developer_portfolio",
                target_audience="Engineers, CTOs, Tech Leads, and AI Recruiters",
                visual_direction="Dark luxury developer aesthetic with cyan/emerald glowing accents, glassmorphic panels, and interactive terminal code mockups",
                sections=sections,
                content_requirements=content_reqs,
                design_patterns=design_patterns,
                asset_requirements=asset_reqs,
                interaction_requirements=interaction_reqs,
                responsive_requirements=responsive_reqs
            )

        elif cat == "restaurant":
            sections = ["Navbar", "Hero Banner", "Special Menu", "About Us", "Gallery", "Opening Hours", "Location & Contact", "Footer"]
            content_reqs = {
                "Hero Banner": "Warm inviting headline, dish highlights, reservation button.",
                "Special Menu": "Categorized menu items with prices, descriptions, and dietary tags.",
                "About Us": "Culinary history and chef philosophy."
            }
            design_patterns = ["Warm Amber/Gold Accent", "Rich Food Cards", "Reservation Modal CTA"]
            asset_reqs = ["Hero Dish Photography", "Gourmet Pizza Visual", "Craft Burger Visual"]
            interaction_reqs = ["Menu Category Filter", "Reservation Form Toggle"]
            responsive_reqs = ["Stacked menu lists on mobile", "2-column grid on tablet"]

            return WebsiteResearchSpecification(
                website_type="restaurant",
                target_audience="Diners, food enthusiasts, and local guests",
                visual_direction="Warm, elegant, food-focused aesthetic with gold/amber accents",
                sections=sections,
                content_requirements=content_reqs,
                design_patterns=design_patterns,
                asset_requirements=asset_reqs,
                interaction_requirements=interaction_reqs,
                responsive_requirements=responsive_reqs
            )

        elif cat == "saas":
            sections = ["Navbar", "Hero", "Value Prop Grid", "Feature Deep Dive", "Pricing Matrix", "Testimonials", "CTA Banner", "Footer"]
            content_reqs = {
                "Hero": "Clear product benefit headline, product screenshot/mockup, free trial CTA.",
                "Feature Deep Dive": "Feature cards with icons and value statements.",
                "Pricing Matrix": "Tiered pricing cards with highlight on recommended plan."
            }
            design_patterns = ["Clean Modern White/Indigo Theme", "Feature Grid", "Pricing Comparison Cards"]
            asset_reqs = ["SaaS Product Dashboard Mockup", "Feature Icons"]
            interaction_reqs = ["Monthly/Yearly Pricing Switcher", "Smooth Nav Scroll"]
            responsive_reqs = ["Responsive pricing matrix", "Mobile hamburger nav"]

            return WebsiteResearchSpecification(
                website_type="saas_product",
                target_audience="Business users, teams, and productivity enthusiasts",
                visual_direction="Clean, modern, high-conversion SaaS aesthetic with indigo accents",
                sections=sections,
                content_requirements=content_reqs,
                design_patterns=design_patterns,
                asset_requirements=asset_reqs,
                interaction_requirements=interaction_reqs,
                responsive_requirements=responsive_reqs
            )

        else:
            sections = ["Navbar", "Hero", "About", "Services", "Projects", "Contact", "Footer"]
            content_reqs = {
                "Hero": "High-impact brand statement and main action button.",
                "Services": "Cards showcasing core business offerings.",
                "Contact": "Inquiry form and office contact details."
            }
            design_patterns = ["Modern Responsive Layout", "Card Grid", "Hover Transitions"]
            asset_reqs = ["Brand Banner Image", "Service Card Thumbnails"]
            interaction_reqs = ["Smooth Nav Scroll", "Button Hover Scale"]
            responsive_reqs = ["Fully responsive 12-column grid system"]

            return WebsiteResearchSpecification(
                website_type=cat,
                target_audience="General audience and prospective clients",
                visual_direction="Modern, clean, professional business theme",
                sections=sections,
                content_requirements=content_reqs,
                design_patterns=design_patterns,
                asset_requirements=asset_reqs,
                interaction_requirements=interaction_reqs,
                responsive_requirements=responsive_reqs
            )
