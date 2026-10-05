import json
import re
import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from ai.ai_response_manager import AIResponseManager

@dataclass
class WebsiteCompositionSpec:
    visual_concept: str
    composition: str
    hero_structure: str
    motion_language: str
    background_system: Dict[str, Any]
    typography_system: Dict[str, str]
    section_flow: List[Dict[str, Any]]
    interaction_model: Dict[str, Any]
    asset_plan: List[Dict[str, Any]]
    transition_plan: List[Dict[str, Any]]

@dataclass
class ComponentSpec:
    name: str
    file_path: str
    role: str
    sections: List[str] = field(default_factory=list)
    key_elements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    verified_content: Any = None

    @property
    def section_title(self) -> str:
        from tools.coding.component_generation_pool import ComponentGenerationPool
        return ComponentGenerationPool.section_title(self.name)

@dataclass
class MasterWebsitePlan:
    business_name: str
    category: str
    theme: str
    color_palette: Dict[str, str]
    typography: Dict[str, str]
    hero_spec: Dict[str, str]
    cta_spec: Dict[str, str]
    components: List[ComponentSpec]
    global_styles: str
    design_direction: Any = None
    verified_content: Any = None
    composition_spec: Optional[WebsiteCompositionSpec] = None
    client_brief: Any = None  # ClientBrief object — source of truth for all content

class WebsiteMasterPlanner:
    """
    Master Website Planner for Turbo Website Builder v5.
    Generates dynamic, art-directed composition specs and file architectures driven by visual direction.
    No hardcoded static template fallbacks.
    """

    @staticmethod
    def generate_master_plan(task: str, brief: Any = None) -> MasterWebsitePlan:
        import time
        start_t = time.time()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[MASTER_PLAN_START] task=\"{task[:40]}\" timestamp={now}", flush=True)

        # PRIORITY 1: brief.client_brief or direct ClientBrief (manually entered by user in Client Brief form)
        _client_brief_obj = getattr(brief, 'client_brief', None)
        if not _client_brief_obj and brief and (hasattr(brief, 'company_name') or hasattr(brief, 'website_type')):
            _client_brief_obj = brief

        biz_name = ""
        if _client_brief_obj:
            biz_name = (
                getattr(_client_brief_obj, 'company_name', '') or
                getattr(_client_brief_obj, 'client_name', '') or ""
            )
            if biz_name in ("", "Client", "Client Enterprise", "Developer Portfolio"):
                biz_name = ""
            if biz_name:
                print(f"[MASTER_PLAN] biz_name_source=CLIENT_BRIEF_FORM value={biz_name!r}", flush=True)

        # PRIORITY 2: brief.business_name (from WebsiteBrief / research)
        if not biz_name:
            biz_name = getattr(brief, 'business_name', '') if brief else ''
            if not biz_name and brief and getattr(brief, 'subject', None):
                biz_name = getattr(brief.subject, 'name', '')

        # PRIORITY 3: extract from task string
        if not biz_name or biz_name in ["Brand", "Client", "Client Brand", "website"]:
            if "for " in task.lower():
                raw_target = task.lower().split("for ")[-1].split(".")[0].strip()
                biz_name = raw_target.title()
            else:
                biz_name = "Enterprise Brand"
        print(f"[MASTER_PLAN] final_biz_name={biz_name!r}", flush=True)

        if brief:
            cat = getattr(brief, 'website_type', None) or getattr(brief, 'category', None) or 'company'
        else:
            from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
            cat = WebsiteRequirementsAnalyzer.detect_category(task) or 'company'


        # Check Visual DNA Spec
        visual_dna = getattr(brief, 'visual_dna', None) if brief else None

        cat_str = cat.value if hasattr(cat, 'value') else str(cat)
        cat_lower = cat_str.lower() if cat_str else "portfolio"
        task_lower = task.lower()

        from tools.coding.website_design_direction import DesignDirectionEngine
        design_dir, sim_score, is_reuse = DesignDirectionEngine.select_design(task, cat_str, biz_name)
        direction = design_dir.name + ": " + design_dir.visual_style

        task_lower = task.lower()

        # Build dynamic WebsiteCompositionSpec using VisualDNA if present
        comp_style = visual_dna.style if visual_dna else design_dir.visual_style
        comp_layout = visual_dna.composition if visual_dna else design_dir.hero_composition
        comp_motion = visual_dna.motion_spec.scroll_behavior if visual_dna else design_dir.scroll_behavior
        comp_palette = visual_dna.color_palette if visual_dna else design_dir.color_system

        composition_spec = WebsiteCompositionSpec(
            visual_concept=f"Art-directed immersive experience ({comp_style}) for {biz_name}",
            composition=comp_layout,
            hero_structure=f"Hero layout matching {comp_style}: {comp_layout}",
            motion_language=comp_motion,
            background_system={
                "type": "layered_canvas_particles",
                "layers": ["base_color", "procedural_gradient", "canvas_particle_mesh", "cursor_light_spotlight", "scroll_clipping"]
            },
            typography_system=visual_dna.typography if visual_dna else {
                "display": "Space Grotesk, sans-serif",
                "body": "Inter, sans-serif",
                "mono": "JetBrains Mono, Fira Code, monospace"
            },
            section_flow=[
                {"name": "DynamicSpatialEnvironment", "role": "3D Spatial Visual Canvas Layer"},
                {"name": "Navbar", "role": "Floating spatial header with glassmorphism"},
                {"name": "Hero", "role": "Kinetic entrance hero"},
                {"name": "About", "role": "Story & philosophy focus"},
                {"name": "Services", "role": "Services and capabilities showcase"},
                {"name": "Projects", "role": "Experiential case studies showcase"},
                {"name": "Contact", "role": "Architectural direct inquiry module"},
                {"name": "Footer", "role": "Atmospheric signature footer"}
            ],
            interaction_model={
                "cursor": "spotlight_displacement",
                "cards": "3d_tilt_parallax",
                "typography": "kinetic_split_reveal"
            },
            asset_plan=[],
            transition_plan=[
                {"type": "morphing_color_field", "from": "hero", "to": "projects"}
            ]
        )

        # Anti-Template Similarity Check Gate
        from tools.coding.anti_template_checker import AntiTemplateChecker
        anti_check = AntiTemplateChecker.evaluate_composition(
            planned_composition={
                "hero_structure": composition_spec.hero_structure,
                "section_order": [s["name"] for s in composition_spec.section_flow],
                "visual_style": comp_style
            },
            visual_dna=visual_dna,
            category=cat
        )

        if anti_check.is_rejected:
            print(f"[ANTI_TEMPLATE_GATE] REJECTED similarity={anti_check.similarity_score:.3f}. Regenerating fresh composition...", flush=True)
            fresh_comp = AntiTemplateChecker.generate_fresh_composition(cat, visual_dna=visual_dna)
            composition_spec.composition = fresh_comp.get("hero_structure", comp_layout)
            composition_spec.hero_structure = fresh_comp.get("hero_structure", comp_layout)
            composition_spec.motion_language = fresh_comp.get("background_system", comp_motion)
            comp_palette = fresh_comp.get("color_palette", comp_palette)

        # TYPE-SPECIFIC COMPOSITION & SECTION ARCHITECTURES (REFERENCE-DRIVEN OVERRIDE)
        if visual_dna and visual_dna.reference_present and getattr(visual_dna, 'section_rhythm', None):
            print(f"[REFERENCE_DRIVEN_ARCHITECTURE] Utilizing reference section rhythm: {visual_dna.section_rhythm}", flush=True)
            ref_component_map = {
                "DynamicSpatialEnvironment": {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Spatial Interactive Canvas Layer", "sections": ["canvas_3d"], "key_elements": ["ParticleCanvas", "Spotlight"], "dependencies": []},
                "FloatingControls": {"name": "FloatingControls", "file_path": "src/components/FloatingControls.tsx", "role": "Floating peripheral UI controls", "sections": ["audio_toggle", "lang"], "key_elements": ["AudioPill", "LangSelect"], "dependencies": []},
                "Navbar": {"name": "FloatingControls", "file_path": "src/components/FloatingControls.tsx", "role": "Floating peripheral UI controls", "sections": ["audio_toggle", "lang"], "key_elements": ["AudioPill", "LangSelect"], "dependencies": []},
                "SpatialHero": {"name": "SpatialHero", "file_path": "src/components/SpatialHero.tsx", "role": "Kinetic entrance hero with display typography", "sections": ["hero_headline", "tagline", "ctas"], "key_elements": ["DisplayHeadline", "StatusBadge", "CTAButtons"], "dependencies": []},
                "DesignPhilosophy": {"name": "DesignPhilosophy", "file_path": "src/components/DesignPhilosophy.tsx", "role": "Editorial philosophy & core principles", "sections": ["philosophy_statement", "pillars"], "key_elements": ["PhilosophyText", "PillarsGrid"], "dependencies": []},
                "CapabilitiesMatrix": {"name": "CapabilitiesMatrix", "file_path": "src/components/CapabilitiesMatrix.tsx", "role": "Interactive tech capabilities & skill matrix", "sections": ["capabilities_grid"], "key_elements": ["CapabilityCards", "TechBadges"], "dependencies": []},
                "FeaturedProjects": {"name": "FeaturedProjects", "file_path": "src/components/FeaturedProjects.tsx", "role": "Selected project case studies & showcase", "sections": ["project_cards"], "key_elements": ["ProjectCards", "ProjectLinks"], "dependencies": []},
                "ExperienceTimeline": {"name": "ExperienceTimeline", "file_path": "src/components/ExperienceTimeline.tsx", "role": "Milestone journey & career timeline", "sections": ["timeline_nodes"], "key_elements": ["MilestoneNodes", "YearBadges"], "dependencies": []},
                "ContactSection": {"name": "ContactSection", "file_path": "src/components/ContactSection.tsx", "role": "Direct inquiry contact module", "sections": ["inquiry_form"], "key_elements": ["InquiryForm", "DirectEmail"], "dependencies": []},
                "Footer": {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Signature spatial atmospheric footer", "sections": ["copyright", "socials"], "key_elements": ["SocialLinks", "Copyright"], "dependencies": []}
            }
            family_components = []
            for sec_name in visual_dna.section_rhythm:
                if sec_name in ref_component_map:
                    family_components.append(ref_component_map[sec_name])
                else:
                    clean_n = re.sub(r'[^A-Za-z0-9]', '', sec_name)
                    if clean_n:
                        family_components.append({
                            "name": clean_n,
                            "file_path": f"src/components/{clean_n}.tsx",
                            "role": f"Reference design section for {sec_name}",
                            "sections": [sec_name.lower()],
                            "key_elements": ["SectionHeader", "ContentGrid"],
                            "dependencies": []
                        })
        elif cat_lower in ["restaurant", "restaurant_cafe", "cafe"]:
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Warm Gastronomy Canvas Layer", "sections": ["ambient_warmth"], "key_elements": ["WarmParticleField"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "Glassmorphism cafe navigation header", "sections": ["brand", "menu_links", "reservation_button"], "key_elements": ["Logo", "MenuLinks", "ReservationBtn"], "dependencies": []},
                {"name": "HeroBanner", "file_path": "src/components/HeroBanner.tsx", "role": "Warm editorial cafe hero banner with client imagery", "sections": ["hero_headline", "hero_subtext", "cta_buttons"], "key_elements": ["CafeTitle", "Tagline", "ClientHeroImage"], "dependencies": []},
                {"name": "RestaurantStory", "file_path": "src/components/RestaurantStory.tsx", "role": "Culinary philosophy & fresh ingredients story", "sections": ["story_text", "values"], "key_elements": ["StoryContent", "Pillars"], "dependencies": []},
                {"name": "SignatureDishes", "file_path": "src/components/SignatureDishes.tsx", "role": "Featured beverages, coffee & culinary creations grid", "sections": ["dishes_grid"], "key_elements": ["DishCards", "PricingBadge"], "dependencies": []},
                {"name": "MenuCategories", "file_path": "src/components/MenuCategories.tsx", "role": "Tabbed food & beverage menu showcase", "sections": ["menu_tabs"], "key_elements": ["CategoryTabs", "MenuItems"], "dependencies": []},
                {"name": "AmbienceGallery", "file_path": "src/components/AmbienceGallery.tsx", "role": "Cafe interior & ambience photo gallery", "sections": ["gallery_grid"], "key_elements": ["GalleryImages"], "dependencies": []},
                {"name": "OpeningHoursLocation", "file_path": "src/components/OpeningHoursLocation.tsx", "role": "Cafe timings, address & directions module", "sections": ["timings", "map"], "key_elements": ["OpeningHours", "LocationAddress"], "dependencies": []},
                {"name": "TableReservation", "file_path": "src/components/TableReservation.tsx", "role": "Table booking & inquiry callout", "sections": ["reservation_form"], "key_elements": ["ReservationForm"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Cafe signature footer with social handles", "sections": ["copyright", "socials"], "key_elements": ["InstagramLink", "Copyright"], "dependencies": []}
            ]
        elif cat_lower in ["product_website", "product"]:
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Product Spotlight Canvas Layer", "sections": ["product_spotlight"], "key_elements": ["InteractiveCore"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "SaaS product navigation bar", "sections": ["product_brand", "nav_links", "get_started_btn"], "key_elements": ["ProductLogo", "NavLinks", "CTA"], "dependencies": []},
                {"name": "ProductHero", "file_path": "src/components/ProductHero.tsx", "role": "High-impact product hero with interface showcase and CTA", "sections": ["headline", "subtext", "product_visual"], "key_elements": ["Headline", "ProductScreenshot", "CTAButton"], "dependencies": []},
                {"name": "ProblemSolution", "file_path": "src/components/ProblemSolution.tsx", "role": "Problem statement vs automated solution comparison", "sections": ["problem_grid", "solution_grid"], "key_elements": ["ProblemCards", "SolutionCards"], "dependencies": []},
                {"name": "KeyFeatures", "file_path": "src/components/KeyFeatures.tsx", "role": "Interactive product features grid", "sections": ["features"], "key_elements": ["FeatureCards", "FeatureIcons"], "dependencies": []},
                {"name": "ProductBenefits", "file_path": "src/components/ProductBenefits.tsx", "role": "User value propositions and efficiency gains", "sections": ["benefits"], "key_elements": ["ValueProps"], "dependencies": []},
                {"name": "HowItWorks", "file_path": "src/components/HowItWorks.tsx", "role": "Step-by-step product workflow explanation", "sections": ["workflow"], "key_elements": ["StepCards"], "dependencies": []},
                {"name": "ProductCTA", "file_path": "src/components/ProductCTA.tsx", "role": "High-conversion product signup CTA", "sections": ["cta_banner"], "key_elements": ["CTAButton"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Product brand footer", "sections": ["links", "copyright"], "key_elements": ["FooterLinks", "Copyright"], "dependencies": []}
            ]
        elif cat_lower in ["service_business", "service"]:
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Service Ambient Grid Layer", "sections": ["ambient_grid"], "key_elements": ["MeshNodes"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "Service company header navigation", "sections": ["logo", "service_links", "book_btn"], "key_elements": ["Logo", "Links", "BookBtn"], "dependencies": []},
                {"name": "ServiceHero", "file_path": "src/components/ServiceHero.tsx", "role": "Service value proposition headline hero", "sections": ["headline", "cta"], "key_elements": ["Headline", "BookCTA"], "dependencies": []},
                {"name": "ServicesList", "file_path": "src/components/ServicesList.tsx", "role": "Dominant service offerings grid", "sections": ["services"], "key_elements": ["ServiceCards"], "dependencies": []},
                {"name": "ServiceBenefits", "file_path": "src/components/ServiceBenefits.tsx", "role": "Why choose our service & client guarantees", "sections": ["benefits"], "key_elements": ["BenefitPillars"], "dependencies": []},
                {"name": "ServiceProcess", "file_path": "src/components/ServiceProcess.tsx", "role": "4-step service delivery process", "sections": ["process"], "key_elements": ["ProcessSteps"], "dependencies": []},
                {"name": "ContactCTA", "file_path": "src/components/ContactCTA.tsx", "role": "Service consultation booking & inquiry form", "sections": ["inquiry"], "key_elements": ["BookingForm"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Service business footer", "sections": ["footer"], "key_elements": ["Copyright"], "dependencies": []}
            ]
        elif cat_lower in ["agency_website", "agency"]:
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Creative Field Canvas Layer", "sections": ["color_field"], "key_elements": ["ColorFieldNodes"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "Creative agency header navigation", "sections": ["logo", "links", "collab_btn"], "key_elements": ["AgencyLogo", "NavLinks", "CollabBtn"], "dependencies": []},
                {"name": "AgencyHero", "file_path": "src/components/AgencyHero.tsx", "role": "Creative manifesto & agency vision hero", "sections": ["manifesto", "ctas"], "key_elements": ["ManifestoText", "WorkCTA"], "dependencies": []},
                {"name": "AgencyIntro", "file_path": "src/components/AgencyIntro.tsx", "role": "Agency introduction & design philosophy", "sections": ["intro"], "key_elements": ["PhilosophyText"], "dependencies": []},
                {"name": "ServicesOverview", "file_path": "src/components/ServicesOverview.tsx", "role": "Agency core capability pillars & services", "sections": ["capabilities"], "key_elements": ["ServiceCards"], "dependencies": []},
                {"name": "CaseStudies", "file_path": "src/components/CaseStudies.tsx", "role": "Selected agency client work & case studies", "sections": ["case_studies"], "key_elements": ["CaseStudyCards"], "dependencies": []},
                {"name": "AgencyProcess", "file_path": "src/components/AgencyProcess.tsx", "role": "Creative strategy & execution process", "sections": ["process"], "key_elements": ["ProcessSteps"], "dependencies": []},
                {"name": "ContactCTA", "file_path": "src/components/ContactCTA.tsx", "role": "Agency project inquiry CTA", "sections": ["contact"], "key_elements": ["InquiryForm"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Creative agency footer", "sections": ["footer"], "key_elements": ["Copyright"], "dependencies": []}
            ]
        elif cat_lower in ["landing_page", "landing"]:
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Kinetic Conversion Canvas Layer", "sections": ["kinetic_bg"], "key_elements": ["KineticMesh"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "Minimal header navigation", "sections": ["brand", "cta"], "key_elements": ["Brand", "CTA"], "dependencies": []},
                {"name": "LandingHero", "file_path": "src/components/LandingHero.tsx", "role": "Focused conversion headline hero", "sections": ["headline", "hero_cta"], "key_elements": ["Headline", "CTAButton"], "dependencies": []},
                {"name": "ProblemSection", "file_path": "src/components/ProblemSection.tsx", "role": "Core friction & problem statement", "sections": ["problem"], "key_elements": ["ProblemCards"], "dependencies": []},
                {"name": "SolutionSection", "file_path": "src/components/SolutionSection.tsx", "role": "Product/service solution breakdown", "sections": ["solution"], "key_elements": ["SolutionCards"], "dependencies": []},
                {"name": "FeaturesBenefits", "file_path": "src/components/FeaturesBenefits.tsx", "role": "Key benefits and capabilities", "sections": ["features"], "key_elements": ["FeaturePillars"], "dependencies": []},
                {"name": "ConversionCTA", "file_path": "src/components/ConversionCTA.tsx", "role": "Final action callout & conversion form", "sections": ["conversion"], "key_elements": ["ActionForm"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Landing page footer", "sections": ["footer"], "key_elements": ["Copyright"], "dependencies": []}
            ]
        elif cat_lower in ["personal_portfolio"]:
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Personal Spatial Canvas Layer", "sections": ["spatial_bg"], "key_elements": ["Orbs"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "Personal top navigation", "sections": ["brand", "links"], "key_elements": ["Name", "Links"], "dependencies": []},
                {"name": "PersonalHero", "file_path": "src/components/PersonalHero.tsx", "role": "Personal identity & introduction hero", "sections": ["identity", "intro"], "key_elements": ["Avatar", "Title"], "dependencies": []},
                {"name": "AboutPerson", "file_path": "src/components/AboutPerson.tsx", "role": "Biography & core focus", "sections": ["bio"], "key_elements": ["Biography"], "dependencies": []},
                {"name": "CoreExpertise", "file_path": "src/components/CoreExpertise.tsx", "role": "Skills & professional capabilities", "sections": ["skills"], "key_elements": ["SkillCards"], "dependencies": []},
                {"name": "WorkShowcase", "file_path": "src/components/WorkShowcase.tsx", "role": "Selected projects & work showcase", "sections": ["projects"], "key_elements": ["WorkCards"], "dependencies": []},
                {"name": "ContactForm", "file_path": "src/components/ContactForm.tsx", "role": "Contact & inquiry form", "sections": ["contact"], "key_elements": ["Form"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Personal footer", "sections": ["footer"], "key_elements": ["Copyright"], "dependencies": []}
            ]
        elif cat_lower in ["developer_portfolio", "portfolio"]:
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Spatial Code Canvas Layer", "sections": ["background_atmosphere"], "key_elements": ["ParticleField", "LightSpotlight"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "Floating spatial navigation bar", "sections": ["brand", "links"], "key_elements": ["Logo", "NavLinks", "StatusBadge"], "dependencies": []},
                {"name": "DeveloperHero", "file_path": "src/components/DeveloperHero.tsx", "role": "Full-stack AI developer kinetic hero", "sections": ["identity", "intro", "ctas"], "key_elements": ["Name", "Role", "CodeTerminal"], "dependencies": []},
                {"name": "TechnicalBio", "file_path": "src/components/TechnicalBio.tsx", "role": "About engineering background & focus", "sections": ["bio", "pillars"], "key_elements": ["Biography", "FocusAreas"], "dependencies": []},
                {"name": "SkillMatrix", "file_path": "src/components/SkillMatrix.tsx", "role": "AI, Full-stack languages & framework grid", "sections": ["skills_grid"], "key_elements": ["SkillCards"], "dependencies": []},
                {"name": "FeaturedProjects", "file_path": "src/components/FeaturedProjects.tsx", "role": "AI & Full-stack project portfolio showcase", "sections": ["project_cards"], "key_elements": ["ProjectCards"], "dependencies": []},
                {"name": "ContactForm", "file_path": "src/components/ContactForm.tsx", "role": "Direct developer inquiry & socials module", "sections": ["form"], "key_elements": ["InquiryForm", "SocialLinks"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "Personal developer footer", "sections": ["footer"], "key_elements": ["Copyright", "NavLinks"], "dependencies": []}
            ]
        else: # BUSINESS_WEBSITE (Default for company / business)
            family_components = [
                {"name": "DynamicSpatialEnvironment", "file_path": "src/components/DynamicSpatialEnvironment.tsx", "role": "3D Enterprise Tech Grid Layer", "sections": ["tech_grid"], "key_elements": ["TechNodes"], "dependencies": []},
                {"name": "Navbar", "file_path": "src/components/Navbar.tsx", "role": "Enterprise B2B navigation header", "sections": ["logo", "nav_links", "contact_btn"], "key_elements": ["EnterpriseLogo", "NavLinks", "ContactBtn"], "dependencies": []},
                {"name": "BusinessHero", "file_path": "src/components/BusinessHero.tsx", "role": "Corporate business hero with value proposition", "sections": ["b2b_headline", "value_prop", "demo_cta"], "key_elements": ["Headline", "ValueProp"], "dependencies": []},
                {"name": "BusinessOverview", "file_path": "src/components/BusinessOverview.tsx", "role": "Company introduction, mission & philosophy", "sections": ["mission"], "key_elements": ["MissionText"], "dependencies": []},
                {"name": "BusinessServices", "file_path": "src/components/BusinessServices.tsx", "role": "Products & services offering grid", "sections": ["services_grid"], "key_elements": ["ServiceCards"], "dependencies": []},
                {"name": "WhyChooseUs", "file_path": "src/components/WhyChooseUs.tsx", "role": "Key benefits and corporate value propositions", "sections": ["benefits"], "key_elements": ["BenefitCards"], "dependencies": []},
                {"name": "BusinessProcess", "file_path": "src/components/BusinessProcess.tsx", "role": "How we work process overview", "sections": ["process"], "key_elements": ["ProcessSteps"], "dependencies": []},
                {"name": "ContactForm", "file_path": "src/components/ContactForm.tsx", "role": "Business consultation & project inquiry form", "sections": ["inquiry_form"], "key_elements": ["ConsultationForm"], "dependencies": []},
                {"name": "Footer", "file_path": "src/components/Footer.tsx", "role": "B2B corporate footer", "sections": ["company_links", "legal"], "key_elements": ["FooterLinks", "Copyright"], "dependencies": []}
            ]


        # LLM Plan Generation
        prompt = (
            f"You are the Master Website Architect. Plan a complete React Vite website in ONE concise JSON object.\n\n"
            f"BUSINESS NAME: {biz_name}\n"
            f"CATEGORY: {cat}\n"
            f"DESIGN ID: {design_dir.design_id}\n"
            f"DESIGN DIRECTION: {direction}\n"
            f"USER TASK: {task}\n\n"
            f"Respond strictly with ONE valid JSON object.\n"
            f"Return ONLY the JSON object. No markdown code blocks, no text explanations."
        )

        messages = [{"role": "user", "content": prompt}]
        ai_manager = AIResponseManager()

        json_data = {}
        try:
            raw_response = ai_manager.generate_response(messages, timeout=15.0)
            cleaned = re.sub(r"```(?:json)?", "", raw_response).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
            json_match = re.search(r"\{[\s\S]*\}", cleaned)
            if json_match:
                json_data = json.loads(json_match.group(0))
        except Exception as e:
            print(f"[WebsiteMasterPlanner Notice]: LLM JSON response notice ({e}). Utilizing art-directed composition plan.")

        if not json_data or "components" not in json_data:
            json_data = {
                "business_name": biz_name,
                "category": cat,
                "theme": direction,
                "color_palette": design_dir.color_system if hasattr(design_dir, 'color_system') else {
                    "primary": "#0f172a", "secondary": "#3b82f6", "accent": "#06b6d4",
                    "background": "#020617", "text": "#f8fafc"
                },
                "typography": {"heading_font": "Space Grotesk, sans-serif"},
                "hero_spec": {"headline": f"Architecting Next-Gen Solutions for {biz_name}", "subheadline": f"High performance digital platform for {biz_name}.", "cta_text": "Explore Works"},
                "cta_spec": {"headline": "Ready to Collaborate?", "cta_text": "Get In Touch"},
                "components": family_components,
                "global_styles": "bg-slate-950 text-slate-100 font-sans min-h-screen"
            }

        v_content = None
        if brief and hasattr(brief, 'research_context') and brief.research_context:
            res_ctx = brief.research_context
            if isinstance(res_ctx, dict):
                v_content = res_ctx.get('verified_content') or res_ctx
            else:
                v_content = getattr(res_ctx, 'verified_content', None) or res_ctx

        valid_family_names = {c["name"] for c in family_components}
        raw_comps = json_data.get("components", family_components)
        if not isinstance(raw_comps, list) or not any(isinstance(c, dict) and c.get("name") in valid_family_names for c in raw_comps):
            raw_comps = family_components

        comps = []
        for c in raw_comps:
            comps.append(ComponentSpec(
                name=c.get("name", "Component"),
                file_path=c.get("file_path", f"src/components/{c.get('name', 'Component')}.tsx"),
                role=c.get("role", "UI component"),
                sections=c.get("sections", []),
                key_elements=c.get("key_elements", []),
                dependencies=c.get("dependencies", []),
                verified_content=v_content
            ))

        # Ensure biz_name is always from client_brief if available (never override with generic fallback)
        final_biz = json_data.get("business_name", biz_name)
        if _client_brief_obj:
            cb_name = getattr(_client_brief_obj, 'company_name', '') or getattr(_client_brief_obj, 'client_name', '')
            if cb_name and cb_name not in ("", "Client", "Client Enterprise", "Developer Portfolio"):
                final_biz = cb_name

        master_plan = MasterWebsitePlan(
            business_name=final_biz,
            category=json_data.get("category", cat),
            theme=json_data.get("theme", direction),
            color_palette=json_data.get("color_palette", {}),
            typography=json_data.get("typography", {}),
            hero_spec=json_data.get("hero_spec", {}),
            cta_spec=json_data.get("cta_spec", {}),
            components=comps,
            global_styles=json_data.get("global_styles", "bg-slate-950 text-slate-100 min-h-screen"),
            design_direction=design_dir,
            verified_content=v_content,
            composition_spec=composition_spec,
            client_brief=_client_brief_obj  # FIX: propagate client_brief into master_plan
        )
        print(f"[MASTER_PLAN_READY_FINAL] business_name={master_plan.business_name!r} client_brief_attached={master_plan.client_brief is not None}", flush=True)

        duration_ms = int((time.time() - start_t) * 1000)
        now_ready = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[MASTER_PLAN_TIMING] duration_ms={duration_ms} timestamp={now_ready}", flush=True)
        print(f"[MASTER_PLAN_READY] components={len(comps)} theme=\"{master_plan.theme[:30]}\" timestamp={now_ready}", flush=True)
        return master_plan

