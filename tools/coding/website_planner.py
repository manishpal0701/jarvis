import os
import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class WebsiteFilePlan:
    path: str
    language: str
    role: str

@dataclass
class WebsiteProjectPlan:
    project_name: str
    framework: str
    files: List[WebsiteFilePlan] = field(default_factory=list)
    entry_file: str = "index.html"
    output_directory: str = ""

class WebsiteProjectPlanner:
    """
    Generic project planner for website build tasks.
    Determines multi-file structure based on user prompt and technology stack selection.
    Defaults to React + TypeScript + Tailwind CSS + Vite stack.
    """

    @classmethod
    def plan_project(cls, task: str, base_output_dir: str = None, brief: any = None) -> WebsiteProjectPlan:
        task_lower = task.lower()

        if brief is None:
            from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
            cat = WebsiteRequirementsAnalyzer.detect_category(task)
            subj = WebsiteRequirementsAnalyzer.detect_subject(task)
            brief = WebsiteRequirementsAnalyzer.extract_information(task, cat, subj)

        from tools.coding.website_technology_selector import WebsiteTechnologySelector
        tech_spec = WebsiteTechnologySelector.detect_stack(task, brief)
        framework = brief.framework if (brief and getattr(brief, 'framework', None)) else tech_spec.framework

        # 1. Sanitize project slug name
        clean_slug = task_lower
        for stop_word in ["ek", "bana", "banaa", "do", "kar", "create", "make", "build", "website", "site", "webpage", "page"]:
            clean_slug = re.sub(r'\b' + stop_word + r'\b', '', clean_slug)
        slug = re.sub(r'[^a-z0-9_]', '_', clean_slug.strip())
        slug = re.sub(r'_+', '_', slug).strip('_')
        slug = slug[:40].rstrip('_') or "website_project"

        project_name = slug
        if base_output_dir and (os.path.isabs(base_output_dir) or "websites" in base_output_dir.lower()):
            output_dir = base_output_dir
        else:
            if not base_output_dir:
                base_output_dir = os.getcwd()
            output_dir = os.path.join(base_output_dir, "websites", project_name)

        # 2. Vanilla HTML / CSS / JS Explicit Stack
        if framework == "vanilla":
            files = [
                WebsiteFilePlan(path="index.html", language="html", role="Main website HTML structure with semantic sections"),
                WebsiteFilePlan(path="style.css", language="css", role="Modern dark/light responsive CSS styling"),
                WebsiteFilePlan(path="script.js", language="javascript", role="Interactive client-side JavaScript features")
            ]
            return WebsiteProjectPlan(
                project_name=project_name,
                framework="vanilla",
                files=files,
                entry_file="index.html",
                output_directory=output_dir
            )

        # 3. Next.js Stack Plan
        if framework == "nextjs":
            files = [
                WebsiteFilePlan(path="package.json", language="json", role="Next.js package manifest"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="app/page.tsx", language="tsx", role="Next.js App Router home page"),
                WebsiteFilePlan(path="app/globals.css", language="css", role="Global CSS styling"),
                WebsiteFilePlan(path="app/layout.tsx", language="tsx", role="Next.js root layout component")
            ]
            return WebsiteProjectPlan(
                project_name=project_name,
                framework="nextjs",
                files=files,
                entry_file="app/page.tsx",
                output_directory=output_dir
            )

        cat = (getattr(brief, 'category', None) or getattr(brief, 'website_type', 'custom')).lower() if brief else "custom"
        p_lower = task.lower() if task else ""

        # 1. RESTAURANT / CAFE FILE PLAN
        if cat in ["restaurant_cafe", "restaurant", "cafe"] or any(k in p_lower for k in ["restaurant", "bella tavola", "italian", "menu", "cafe", "everfresh"]):
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Restaurant & Cafe')) if brief else "Restaurant & Cafe"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration for React Vite application"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite build tool configuration for React and Tailwind"),
                WebsiteFilePlan(path="index.html", language="html", role=f"HTML entry point container for {biz_name}"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React application main DOM root rendering App component"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing luxury restaurant sections: Navbar, HeroBanner, SignatureDishes, MenuCategories, RestaurantStory, AmbienceGallery, OpeningHoursLocation, TableReservation, Footer"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Tailwind CSS directives, warm amber/stone design variables, Playfair Display typography, and gold card styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Luxury navbar with logo, nav links (Menu, Signature Dishes, Our Story, Gallery, Location & Hours), and Reserve Table button"),
                WebsiteFilePlan(path="src/components/HeroBanner.tsx", language="tsx", role="Gastronomy hero section with background dining visual, headline, and Reserve Table CTA"),
                WebsiteFilePlan(path="src/components/SignatureDishes.tsx", language="tsx", role="Gourmet showcase grid of dishes with prices, food photos, and wine pairings"),
                WebsiteFilePlan(path="src/components/MenuCategories.tsx", language="tsx", role="Interactive fine dining menu tab filter displaying dish names, descriptions, and prices"),
                WebsiteFilePlan(path="src/components/RestaurantStory.tsx", language="tsx", role="Narrative section featuring Chef story, heritage, and dining visual"),
                WebsiteFilePlan(path="src/components/AmbienceGallery.tsx", language="tsx", role="Visual photo grid showcasing dining room, wine cellar, and kitchen"),
                WebsiteFilePlan(path="src/components/OpeningHoursLocation.tsx", language="tsx", role="Dining hours card, address, phone, and location details"),
                WebsiteFilePlan(path="src/components/TableReservation.tsx", language="tsx", role="Interactive table reservation form"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role=f"Elegant footer for {biz_name}"),
                WebsiteFilePlan(path="README.md", language="markdown", role=f"Project documentation for {biz_name}")
            ]

        # 2. DEVELOPER PORTFOLIO FILE PLAN
        elif cat in ["developer_portfolio", "portfolio"] or ("developer" in p_lower and "portfolio" in p_lower):
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Developer Portfolio')) if brief else "Developer Portfolio"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite build tool configuration"),
                WebsiteFilePlan(path="index.html", language="html", role="HTML entry point container"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React application entry point"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing developer portfolio sections"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Tailwind CSS directives and glassmorphic panel styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Developer top navigation bar"),
                WebsiteFilePlan(path="src/components/Hero.tsx", language="tsx", role="High-impact developer hero split-layout with status badge, headline, CTAs, and code terminal preview widget"),
                WebsiteFilePlan(path="src/components/About.tsx", language="tsx", role="About section with developer avatar visual, bio, and engineering focus cards"),
                WebsiteFilePlan(path="src/components/Skills.tsx", language="tsx", role="Technical stack matrix grid"),
                WebsiteFilePlan(path="src/components/Projects.tsx", language="tsx", role="Featured engineering project showcase cards"),
                WebsiteFilePlan(path="src/components/Experience.tsx", language="tsx", role="Career milestone chronology section"),
                WebsiteFilePlan(path="src/components/Contact.tsx", language="tsx", role="Direct developer inquiry form"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Developer footer"),
                WebsiteFilePlan(path="README.md", language="markdown", role=f"Documentation for {biz_name}")
            ]

        # 3. PERSONAL PORTFOLIO FILE PLAN
        elif cat == "personal_portfolio" or "personal" in p_lower:
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Personal Portfolio')) if brief else "Personal Portfolio"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite build configuration"),
                WebsiteFilePlan(path="index.html", language="html", role="HTML container"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React entry point"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing personal identity sections"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Tailwind CSS styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Navigation bar"),
                WebsiteFilePlan(path="src/components/Hero.tsx", language="tsx", role="Personal identity hero section"),
                WebsiteFilePlan(path="src/components/About.tsx", language="tsx", role="Biography & personal philosophy"),
                WebsiteFilePlan(path="src/components/Expertise.tsx", language="tsx", role="Core skills & competencies"),
                WebsiteFilePlan(path="src/components/WorkShowcase.tsx", language="tsx", role="Selected work & portfolio showcase"),
                WebsiteFilePlan(path="src/components/Contact.tsx", language="tsx", role="Contact form"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Footer"),
                WebsiteFilePlan(path="README.md", language="markdown", role="Documentation")
            ]

        # 4. PRODUCT WEBSITE FILE PLAN
        elif cat in ["product_website", "product"] or any(k in p_lower for k in ["product", "saas product", "productivity app"]):
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Product Website')) if brief else "Product Website"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite configuration"),
                WebsiteFilePlan(path="index.html", language="html", role="HTML container"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React entry point"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing product presentation sections"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Global CSS styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Product navigation bar"),
                WebsiteFilePlan(path="src/components/ProductHero.tsx", language="tsx", role="Product hero with visual spotlight & CTA"),
                WebsiteFilePlan(path="src/components/ProblemSolution.tsx", language="tsx", role="Problem vs Solution showcase"),
                WebsiteFilePlan(path="src/components/KeyFeatures.tsx", language="tsx", role="Key product feature matrix"),
                WebsiteFilePlan(path="src/components/ProductBenefits.tsx", language="tsx", role="User benefits & value prop"),
                WebsiteFilePlan(path="src/components/HowItWorks.tsx", language="tsx", role="Step-by-step product workflow"),
                WebsiteFilePlan(path="src/components/ProductCTA.tsx", language="tsx", role="Focused conversion CTA section"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Product footer"),
                WebsiteFilePlan(path="README.md", language="markdown", role="Documentation")
            ]

        # 5. SERVICE BUSINESS FILE PLAN
        elif cat in ["service_business", "service"] or "service" in p_lower:
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Service Business')) if brief else "Service Business"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite configuration"),
                WebsiteFilePlan(path="index.html", language="html", role="HTML container"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React entry point"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing service business sections"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Global CSS styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Navigation bar"),
                WebsiteFilePlan(path="src/components/ServiceHero.tsx", language="tsx", role="Service value proposition hero"),
                WebsiteFilePlan(path="src/components/ServicesList.tsx", language="tsx", role="Service offerings grid"),
                WebsiteFilePlan(path="src/components/ServiceBenefits.tsx", language="tsx", role="Why choose our services"),
                WebsiteFilePlan(path="src/components/ServiceProcess.tsx", language="tsx", role="How our service works"),
                WebsiteFilePlan(path="src/components/ContactCTA.tsx", language="tsx", role="Service booking & contact CTA"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Footer"),
                WebsiteFilePlan(path="README.md", language="markdown", role="Documentation")
            ]

        # 6. AGENCY WEBSITE FILE PLAN
        elif cat in ["agency_website", "agency"] or "agency" in p_lower:
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Creative Agency')) if brief else "Creative Agency"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite configuration"),
                WebsiteFilePlan(path="index.html", language="html", role="HTML container"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React entry point"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing agency sections"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Global CSS styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Agency header bar"),
                WebsiteFilePlan(path="src/components/AgencyHero.tsx", language="tsx", role="Agency manifesto & headline hero"),
                WebsiteFilePlan(path="src/components/AgencyIntro.tsx", language="tsx", role="Agency background & philosophy"),
                WebsiteFilePlan(path="src/components/ServicesOverview.tsx", language="tsx", role="Agency capabilities & services"),
                WebsiteFilePlan(path="src/components/CaseStudies.tsx", language="tsx", role="Selected agency work & case studies"),
                WebsiteFilePlan(path="src/components/AgencyProcess.tsx", language="tsx", role="Agency delivery process"),
                WebsiteFilePlan(path="src/components/ContactCTA.tsx", language="tsx", role="Project inquiry CTA"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Agency footer"),
                WebsiteFilePlan(path="README.md", language="markdown", role="Documentation")
            ]

        # 7. LANDING PAGE FILE PLAN
        elif cat in ["landing_page", "landing"] or "landing" in p_lower:
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Landing Page')) if brief else "Landing Page"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite configuration"),
                WebsiteFilePlan(path="index.html", language="html", role="HTML container"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React entry point"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing focused landing page sections"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Global CSS styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Clean header navigation"),
                WebsiteFilePlan(path="src/components/LandingHero.tsx", language="tsx", role="High-conversion headline hero"),
                WebsiteFilePlan(path="src/components/ProblemSection.tsx", language="tsx", role="Problem statement section"),
                WebsiteFilePlan(path="src/components/SolutionSection.tsx", language="tsx", role="Solution overview section"),
                WebsiteFilePlan(path="src/components/FeaturesBenefits.tsx", language="tsx", role="Core features & benefits grid"),
                WebsiteFilePlan(path="src/components/ConversionCTA.tsx", language="tsx", role="Final action CTA section"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Footer"),
                WebsiteFilePlan(path="README.md", language="markdown", role="Documentation")
            ]

        # 8. BUSINESS WEBSITE FILE PLAN (Default for company / corporate / business)
        else:
            biz_name = getattr(brief, 'business_identity', getattr(brief, 'business_name', 'Business Website')) if brief else "Business Website"
            files = [
                WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
                WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration"),
                WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite build configuration"),
                WebsiteFilePlan(path="index.html", language="html", role=f"HTML container for {biz_name}"),
                WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React entry point"),
                WebsiteFilePlan(path="src/App.tsx", language="tsx", role="Main App component composing business sections"),
                WebsiteFilePlan(path="src/index.css", language="css", role="Tailwind CSS design system variables & enterprise styling"),
                WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Enterprise header navigation"),
                WebsiteFilePlan(path="src/components/BusinessHero.tsx", language="tsx", role="Corporate hero section with value proposition"),
                WebsiteFilePlan(path="src/components/BusinessOverview.tsx", language="tsx", role="Company introduction & mission"),
                WebsiteFilePlan(path="src/components/BusinessServices.tsx", language="tsx", role="Products & services grid"),
                WebsiteFilePlan(path="src/components/WhyChooseUs.tsx", language="tsx", role="Value proposition & key benefits"),
                WebsiteFilePlan(path="src/components/BusinessProcess.tsx", language="tsx", role="How we work process overview"),
                WebsiteFilePlan(path="src/components/ContactForm.tsx", language="tsx", role="Enterprise contact form"),
                WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Corporate footer"),
                WebsiteFilePlan(path="README.md", language="markdown", role=f"Documentation for {biz_name}")
            ]

        return WebsiteProjectPlan(
            project_name=project_name,
            framework="react",
            files=files,
            entry_file="src/App.tsx",
            output_directory=output_dir
        )
