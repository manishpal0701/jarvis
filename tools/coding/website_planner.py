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
        slug = re.sub(r'_+', '_', slug).strip('_') or "website_project"

        project_name = slug
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

        # 4. React + TypeScript + Tailwind + Vite Stack Plan (DEFAULT or Explicit React)
        biz_name = brief.business_name if (brief and brief.business_name) else (brief.subject.name if brief and brief.subject and brief.subject.name else "Manish — AI Engineer & Full-Stack Developer")
        sections_desc = ", ".join(brief.required_sections) if (brief and brief.required_sections) else "Hero, About, Skills, Projects, Experience, Contact, Footer"
        design_desc = brief.design_preference if (brief and brief.design_preference) else "Dark luxury developer aesthetic with glassmorphic cards and glowing cyan accents"

        files = [
            WebsiteFilePlan(path="package.json", language="json", role=f"React Vite package manifest for {biz_name}"),
            WebsiteFilePlan(path="tsconfig.json", language="json", role="TypeScript configuration for React Vite application"),
            WebsiteFilePlan(path="vite.config.ts", language="typescript", role="Vite build tool configuration for React and Tailwind"),
            WebsiteFilePlan(path="index.html", language="html", role="HTML entry point container with root div and script module entry"),
            WebsiteFilePlan(path="src/main.tsx", language="tsx", role="React application main DOM root rendering App component"),
            WebsiteFilePlan(path="src/App.tsx", language="tsx", role=f"Main App component composing glassmorphic sections: {sections_desc}"),
            WebsiteFilePlan(path="src/index.css", language="css", role=f"Tailwind CSS directives, glassmorphic panel utility classes, and custom CSS variables ({design_desc})"),
            WebsiteFilePlan(path="src/components/Navbar.tsx", language="tsx", role="Fixed floating glassmorphic top navigation with logo MANISH.AI, nav links (About, Skills, Projects, Experience, Contact), CTA button, and mobile menu toggle"),
            WebsiteFilePlan(path="src/components/Hero.tsx", language="tsx", role="High-impact developer hero split-layout with status badge, gradient headline 'Building Intelligent AI Agents & Software', CTA buttons, stats counter, and interactive terminal code preview widget"),
            WebsiteFilePlan(path="src/components/About.tsx", language="tsx", role=f"About section with developer avatar visual, biography paragraph, core engineering focus cards, and glassmorphic layout for {biz_name}"),
            WebsiteFilePlan(path="src/components/Skills.tsx", language="tsx", role="Technical stack grid featuring 6 skill cards (Python, TypeScript/React, Ollama & Local LLMs, Flutter/Dart, Tailwind CSS v4, OpenCV) with category pills and proficiency tags"),
            WebsiteFilePlan(path="src/components/Projects.tsx", language="tsx", role="Featured engineering showcase with 3-column glass cards showing real project thumbnails (Jarvis AI Assistant, AI Video Editing Agent, Flutter Attendance Mobile App), tech stack badges, and demo buttons"),
            WebsiteFilePlan(path="src/components/Experience.tsx", language="tsx", role="Career timeline section with role cards, organization names, dates, and key engineering achievements"),
            WebsiteFilePlan(path="src/components/Contact.tsx", language="tsx", role="Interactive contact section with form inputs (Name, Email, Message), submission state, and social links"),
            WebsiteFilePlan(path="src/components/Footer.tsx", language="tsx", role="Footer component with copyright notice, brand links, and back-to-top anchor"),
            WebsiteFilePlan(path="README.md", language="markdown", role=f"Project documentation for {biz_name} React Vite application")
        ]

        return WebsiteProjectPlan(
            project_name=project_name,
            framework="react",
            files=files,
            entry_file="src/App.tsx",
            output_directory=output_dir
        )
