from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
import re

class WebsiteCategory(Enum):
    DEVELOPER_PORTFOLIO = "developer_portfolio"
    PERSONAL_PORTFOLIO = "personal_portfolio"
    BUSINESS_WEBSITE = "business_website"
    PRODUCT_WEBSITE = "product_website"
    SERVICE_BUSINESS = "service_business"
    RESTAURANT_CAFE = "restaurant_cafe"
    AGENCY_WEBSITE = "agency_website"
    LANDING_PAGE = "landing_page"

    # Aliases for backwards compatibility
    PORTFOLIO = "developer_portfolio"
    BUSINESS = "business_website"
    RESTAURANT = "restaurant_cafe"
    LANDING = "landing_page"
    ECOMMERCE = "ecommerce"
    BLOG = "blog"
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
    research_context: Any = None
    visual_plan: Any = None
    confirmed: bool = False
    client_brief: Any = None
    asset_bindings: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.required_sections:
            cat = str(self.category).lower()
            if cat in ["developer_portfolio", "portfolio"]:
                self.required_sections = ["Hero", "About", "Skills", "Projects", "Experience", "Contact"]
            elif cat == "personal_portfolio":
                self.required_sections = ["Hero", "About", "Expertise", "Work", "Experience", "Contact"]
            elif cat in ["business_website", "business", "company"]:
                self.required_sections = ["Navbar", "BusinessHero", "BusinessValueProp", "Services", "WhyChooseUs", "Contact", "Footer"]
            elif cat in ["product_website", "product"]:
                self.required_sections = ["Navbar", "ProductHero", "ProblemSolution", "Features", "Benefits", "HowItWorks", "CTA", "Footer"]
            elif cat in ["service_business", "service"]:
                self.required_sections = ["Navbar", "ServiceHero", "ServiceValueProp", "Services", "Benefits", "Process", "ContactCTA", "Footer"]
            elif cat in ["restaurant_cafe", "restaurant", "cafe"]:
                self.required_sections = ["Navbar", "HeroBanner", "RestaurantStory", "SignatureDishes", "MenuCategories", "OpeningHoursLocation", "TableReservation", "Footer"]
            elif cat in ["agency_website", "agency"]:
                self.required_sections = ["Navbar", "AgencyHero", "AgencyIntro", "ServicesOverview", "CaseStudies", "Capabilities", "ContactCTA", "Footer"]
            elif cat in ["landing_page", "landing"]:
                self.required_sections = ["Navbar", "LandingHero", "ProblemSection", "SolutionSection", "FeaturesBenefits", "ConversionCTA", "Footer"]
            else:
                self.required_sections = ["Navbar", "Hero", "About", "Services", "Projects", "Contact", "Footer"]

class WebsiteRequirementsAnalyzer:
    @classmethod
    def detect_category(cls, command: str) -> WebsiteCategory:
        cmd = command.lower()

        # 1. Developer Portfolio
        if any(w in cmd for w in ["developer portfolio", "flutter developer", "ai engineer", "full stack developer", "software engineer portfolio", "coder portfolio", "manish portfolio"]):
            return WebsiteCategory.DEVELOPER_PORTFOLIO
        # 2. Personal Portfolio
        if any(w in cmd for w in ["personal portfolio", "designer portfolio", "my portfolio", "resume website", "cv website"]):
            return WebsiteCategory.PERSONAL_PORTFOLIO
        if any(w in cmd for w in ["portfolio", "resume"]):
            if any(w in cmd for w in ["developer", "engineer", "coder", "flutter", "full stack", "python", "ai"]):
                return WebsiteCategory.DEVELOPER_PORTFOLIO
            return WebsiteCategory.PERSONAL_PORTFOLIO
        # 3. Cafe / Restaurant
        if any(w in cmd for w in ["cafe", "restaurant", "everfresh", "dining", "bakery", "kitchen", "coffee", "food"]):
            return WebsiteCategory.RESTAURANT_CAFE
        # 4. Agency
        if any(w in cmd for w in ["agency", "digital agency", "marketing agency", "creative agency", "design agency"]):
            return WebsiteCategory.AGENCY_WEBSITE
        # 5. Product Website
        if any(w in cmd for w in ["product website", "productivity product", "saas product", "app website", "software product", "product landing"]):
            return WebsiteCategory.PRODUCT_WEBSITE
        # 6. Service Business
        if any(w in cmd for w in ["service business", "service website", "consulting firm", "plumbing", "repair service", "salon", "spa website"]):
            return WebsiteCategory.SERVICE_BUSINESS
        # 7. Landing Page
        if any(w in cmd for w in ["landing page", "one page website", "launch page"]):
            return WebsiteCategory.LANDING_PAGE
        # 8. Business / Corporate
        if any(w in cmd for w in ["company", "corporate", "business website", "software company", "novastack", "inurum", "enterprise"]):
            return WebsiteCategory.BUSINESS_WEBSITE
        if any(w in cmd for w in ["business", "b2b"]):
            return WebsiteCategory.BUSINESS_WEBSITE
        if any(w in cmd for w in ["ecommerce", "e-commerce", "shop", "store"]):
            return WebsiteCategory.ECOMMERCE

        return WebsiteCategory.CUSTOM

    @classmethod
    def detect_subject(cls, command: str) -> WebsiteSubject:
        cmd = command.lower()
        name_match = re.search(r'(?:for|liye|name|brand|company|business|cafe|restaurant|client)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:ke|hai|website|site|bana|bnao|with|in|using|on|whatsapp)|$)', command, re.IGNORECASE)
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

        from tools.coding.client_brief_ingestion import ClientBriefManager
        c_brief, status = ClientBriefManager.get_instance().resolve_brief_from_command(command)
        if c_brief:
            brief.client_brief = c_brief
            brief.person_name = c_brief.person_name or c_brief.client_name
            brief.business_name = c_brief.company_name or c_brief.person_name or c_brief.client_name or "Client Business"
            brief.subject.name = brief.business_name
            brief.category = c_brief.website_type
            brief.value_proposition = c_brief.business_description or f"Official Website for {brief.business_name}"
            brief.title = f"{brief.business_name} — Official Website"

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
        if "inurum" in cmd_lower:
            brief.business_name = "Inurum Technology"
            brief.subject.name = "Inurum Technology"
            brief.title = "Inurum Technology — Enterprise Software Engineering & AI"
            brief.category = WebsiteCategory.BUSINESS.value
            brief.required_sections = ["Hero", "About", "Services", "TechStack", "Solutions", "Projects", "WhyChooseUs", "Testimonials", "Contact", "Footer"]
            brief.value_proposition = "Pioneering Enterprise AI, Cloud Architectures, and Autonomous Software Intelligence"
            brief.brand_voice = "Cinematic, technical, authoritative, and innovative"
            brief.design_preference = "Dark luxury spatial technology aesthetic with glassmorphic cards, cyan glow, and interactive 3D perspective"
        elif not c_brief and (category == WebsiteCategory.PORTFOLIO or "developer" in cmd_lower or "engineer" in cmd_lower or "portfolio" in cmd_lower):
            if not brief.subject.name:
                brief.subject.name = brief.person_name or "Developer"
            if not brief.business_name:
                brief.business_name = f"{brief.subject.name} — Developer Portfolio"
            brief.value_proposition = brief.value_proposition or "Building Autonomous AI Agents & High-Performance Applications"
            brief.brand_voice = "Confident, technical, innovative, and sleek"
            brief.design_preference = "Dark luxury developer aesthetic with glassmorphic cards, glowing cyan accents, and interactive terminal widgets"
        else:
            comp_ent = cls.detect_company_entity(command)
            if comp_ent:
                brief.business_name = comp_ent
                brief.subject.name = comp_ent
            elif subject and subject.name:
                brief.business_name = subject.name

        if "flutter" in cmd_lower:
            brief.special_requirements.append("Flutter Developer Focus")
        if "dark" in cmd_lower or "premium" in cmd_lower:
            brief.design_preference = "Dark luxury developer aesthetic"

        return brief

    @classmethod
    def detect_company_entity(cls, command: str) -> Optional[str]:
        """
        Detects if the user prompt mentions a specific company, organization, product, brand, or topic
        that warrants background web research (e.g. 'Tesla', 'XYZ company', 'ABC restaurant').
        Returns entity name string if detected, or None.
        """
        cmd = command.strip()
        cmd_lower = cmd.lower()
        if "inurum" in cmd_lower:
            return "Inurum Technology"
        if "bmw" in cmd_lower:
            return "BMW"
        stop_words = {"mere", "apne", "mujhe", "uske", "unka", "my", "our", "me", "us", "ek", "modern", "good", "best", "new", "this", "any", "website", "web", "page", "landing", "app", "site", "portfolio", "code", "system", "project"}

        # 1. Pattern: <Entity> ke liye / ke waste / for
        m1 = re.search(r'([A-Za-z0-9\.\-]{2,25}(?:\s+(?:company|brand|restaurant|cafe|agency|shop|store))?)\s+(?:ke\s+liye|ke\s+wastere|for)', cmd, re.IGNORECASE)
        if m1:
            candidate = m1.group(1).strip()
            for prefix in ["restaurant", "company", "cafe", "brand", "shop"]:
                if candidate.lower().startswith(prefix + " "):
                    candidate = candidate[len(prefix):].strip()
            if candidate.lower() not in stop_words and len(candidate) >= 2:
                return candidate

        # 2. Pattern: website for <Entity> / landing page for <Entity> / website for <Company>
        m2 = re.search(r'(?:website|landing page|app|site)\s+(?:for|about|of)\s+([A-Za-z0-9\.\-\s]{2,35})', cmd, re.IGNORECASE)
        if m2:
            candidate = m2.group(1).strip()
            # Clean trailing generic prompt words
            candidate = re.sub(r'\s+(?:company|corp|corporation|inc|ltd|gmbh|ke\s+liye|banaa?\s*do)$', '', candidate, flags=re.IGNORECASE).strip()
            if candidate.lower() not in stop_words and len(candidate) >= 2:
                return candidate

        # 2b. Direct 'for <Entity>' match
        m2b = re.search(r'\bfor\s+([A-Z0-9][a-zA-Z0-9\.\-\s]{1,30})', cmd)
        if m2b:
            candidate = m2b.group(1).strip()
            if candidate.lower() not in stop_words and len(candidate) >= 2:
                return candidate

        # 3. Known brands list
        known_brands = ["bmw", "tesla", "apple", "microsoft", "google", "mercedes", "audi", "porsche", "ferrari", "lamborghini", "ford", "toyota", "honda", "volkswagen", "nvidia", "nike", "adidas", "starbucks", "mcdonalds", "zomato", "swiggy", "bella tavola"]
        for brand in known_brands:
            if brand in cmd_lower:
                return brand.upper() if len(brand) <= 3 else brand.capitalize()

        return None

    @classmethod
    def format_brief_summary(cls, brief: Any) -> str:
        subj = getattr(brief, 'subject', None)
        subj_name = subj.name if (subj and getattr(subj, 'name', None)) else (getattr(brief, 'person_name', None) or getattr(brief, 'business_identity', None) or "Client")
        title = getattr(brief, 'title', f"{subj_name} Website")
        category = getattr(brief, 'category', getattr(brief, 'website_type', 'Custom'))
        tech_stack = getattr(brief, 'technology_stack', 'React + TypeScript + Tailwind CSS')
        design_pref = getattr(brief, 'design_preference', getattr(brief, 'brand_preferences', 'Modern Theme'))
        req_sections = getattr(brief, 'required_sections', [])
        summary = (
            f"📋 **Website Brief Summary**:\n"
            f"• **Project Title**: {title}\n"
            f"• **Category**: {str(category).capitalize()}\n"
            f"• **Subject / Brand**: {subj_name}\n"
            f"• **Technology**: {tech_stack}\n"
            f"• **Design Preference**: {design_pref}\n"
            f"• **Required Sections**: {', '.join(req_sections)}"
        )
        if brief.research_context:
            res_ctx = brief.research_context
            official = res_ctx.get("official_name") if isinstance(res_ctx, dict) else getattr(res_ctx, "official_name", "")
            desc = res_ctx.get("description") if isinstance(res_ctx, dict) else getattr(res_ctx, "description", "")
            sources = res_ctx.get("sources") if isinstance(res_ctx, dict) else getattr(res_ctx, "sources", [])
            if official or desc:
                summary += f"\n• **Verified Web Research**: {official or 'Found'} — {desc[:80]}... ({len(sources)} sources)"
        if brief.visual_plan:
            vp = brief.visual_plan
            direction = vp.get("design_direction") if isinstance(vp, dict) else getattr(vp, "design_direction", "")
            hero = vp.get("hero_strategy") if isinstance(vp, dict) else getattr(vp, "hero_strategy", "")
            if direction:
                summary += f"\n• **Visual Intelligence Plan**: {direction} (Hero: {hero[:60]}...)"
        return summary
