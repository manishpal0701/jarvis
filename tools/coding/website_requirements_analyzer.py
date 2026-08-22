from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
import re

class WebsiteCategory(Enum):
    PORTFOLIO = "portfolio"
    ECOMMERCE = "ecommerce"
    RESTAURANT = "restaurant"
    BLOG = "blog"
    LANDING = "landing"
    BUSINESS = "business"
    CUSTOM = "custom"

class SubjectType(Enum):
    PERSON = "person"
    COMPANY = "company"
    PRODUCT = "product"
    SERVICE = "service"
    UNKNOWN = "unknown"

@dataclass
class WebsiteSubject:
    subject_type: str = SubjectType.UNKNOWN.value
    name: str = ""
    domain_or_topic: str = ""
    details: Dict[str, str] = field(default_factory=dict)

@dataclass
class WebsiteBrief:
    category: str = WebsiteCategory.CUSTOM.value
    subject: WebsiteSubject = field(default_factory=WebsiteSubject)
    title: str = "Client Website"
    business_name: str = ""
    person_name: str = ""
    target_audience: str = ""
    offering_details: List[str] = field(default_factory=list)
    pricing: List[str] = field(default_factory=list)
    value_proposition: str = ""
    brand_voice: str = "Professional and modern"
    experience_or_history: str = ""
    contact_info: Dict[str, str] = field(default_factory=dict)
    location: str = ""
    social_links: Dict[str, str] = field(default_factory=dict)
    CTA: str = ""
    design_preference: str = "Modern responsive theme"
    technology_stack: str = "React + TypeScript + Tailwind CSS + Vite"
    framework: str = "react"
    language: str = "typescript"
    styling_system: str = "tailwind"
    build_tool: str = "vite"
    runtime: str = "node"
    build_system: str = "vite"
    image_reference_path: str = ""
    required_sections: List[str] = field(default_factory=list)
    special_requirements: List[str] = field(default_factory=list)
    visual_requirements: List[str] = field(default_factory=list)
    assets_available: List[str] = field(default_factory=list)
    confirmed: bool = False

    def __post_init__(self):
        if not self.required_sections:
            if self.category == WebsiteCategory.PORTFOLIO.value:
                self.required_sections = ["Hero", "About", "Skills", "Projects", "Experience", "Contact"]
            elif self.category == WebsiteCategory.ECOMMERCE.value:
                self.required_sections = ["Hero Banner", "Featured Categories", "Top Products", "Why Shop With Us", "Newsletter / Footer"]
            elif self.category == WebsiteCategory.RESTAURANT.value:
                self.required_sections = ["Hero", "Special Menu", "About Us", "Opening Hours", "Location & Contact"]
            else:
                self.required_sections = ["Hero", "About", "Services", "Projects", "Contact"]

class WebsiteRequirementsAnalyzer:
    @classmethod
    def detect_category(cls, command: str) -> WebsiteCategory:
        cmd = command.lower()
        if any(w in cmd for w in ["portfolio", "resume", "personal", "developer", "designer", "engineer"]):
            return WebsiteCategory.PORTFOLIO
        if any(w in cmd for w in ["ecommerce", "e-commerce", "shop", "store", "products", "sell"]):
            return WebsiteCategory.ECOMMERCE
        if any(w in cmd for w in ["cafe", "restaurant", "food", "menu", "dining", "bakery", "kitchen"]):
            return WebsiteCategory.RESTAURANT
        if any(w in cmd for w in ["blog", "news", "articles", "magazine"]):
            return WebsiteCategory.BLOG
        if any(w in cmd for w in ["landing", "product page", "launch"]):
            return WebsiteCategory.LANDING
        if any(w in cmd for w in ["company", "corporate", "agency", "business"]):
            return WebsiteCategory.BUSINESS
        return WebsiteCategory.CUSTOM

    @classmethod
    def detect_subject(cls, command: str) -> WebsiteSubject:
        cmd = command.lower()
        name_match = re.search(r'(?:for|liye|name|brand|company|business|cafe|restaurant)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:ke|hai|website|site|bana|bnao|with|in)|$)', command, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else ""

        if any(w in cmd for w in ["cafe", "restaurant", "company", "store", "shop", "business", "brand"]):
            subj_type = SubjectType.COMPANY.value
        elif any(w in cmd for w in ["portfolio", "developer", "designer", "engineer", "resume"]):
            subj_type = SubjectType.PERSON.value
        else:
            subj_type = SubjectType.UNKNOWN.value

        return WebsiteSubject(subject_type=subj_type, name=name, domain_or_topic=cmd)

    @classmethod
    def extract_information(cls, command: str, category: WebsiteCategory, subject: WebsiteSubject) -> WebsiteBrief:
        brief = WebsiteBrief(
            category=category.value,
            subject=subject,
            title=f"{subject.name if subject.name else category.value.capitalize()} Website"
        )
        from tools.coding.website_technology_selector import WebsiteTechnologySelector
        tech_spec = WebsiteTechnologySelector.detect_stack(command, brief)
        brief.technology_stack = tech_spec.display_name
        brief.framework = tech_spec.framework
        brief.language = tech_spec.language
        brief.styling_system = tech_spec.styling
        brief.build_tool = tech_spec.build_system
        brief.runtime = tech_spec.runtime
        brief.build_system = tech_spec.build_system

        cmd_lower = command.lower()
        if category == WebsiteCategory.PORTFOLIO or "developer" in cmd_lower or "engineer" in cmd_lower or "portfolio" in cmd_lower:
            if not brief.subject.name:
                brief.subject.name = "Manish"
            brief.business_name = "Manish — AI Engineer & Full-Stack Developer"
            brief.person_name = "Manish"
            brief.value_proposition = "Building Autonomous AI Agents, Local LLM Architecture & High-Performance Web Applications"
            brief.brand_voice = "Confident, technical, innovative, and sleek"
            brief.design_preference = "Dark luxury developer aesthetic with glassmorphic cards, glowing cyan accents, and interactive terminal widgets"

        if "flutter" in cmd_lower:
            brief.special_requirements.append("Flutter Developer Focus")
        if "dark" in cmd_lower or "premium" in cmd_lower:
            brief.design_preference = "Dark luxury developer aesthetic"

        return brief

    @classmethod
    def format_brief_summary(cls, brief: WebsiteBrief) -> str:
        subj_name = brief.subject.name if brief.subject and brief.subject.name else "Client"
        return (
            f"📋 **Website Brief Summary**:\n"
            f"• **Project Title**: {brief.title}\n"
            f"• **Category**: {brief.category.capitalize()}\n"
            f"• **Subject / Brand**: {subj_name}\n"
            f"• **Technology**: {brief.technology_stack}\n"
            f"• **Design Preference**: {brief.design_preference}\n"
            f"• **Required Sections**: {', '.join(brief.required_sections)}"
        )
