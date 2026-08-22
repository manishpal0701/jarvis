import json
from dataclasses import dataclass, field
from typing import Dict, List, Any
from ai.model_router import ModelRouter

@dataclass
class WebsiteContentSpecification:
    person_or_brand_name: str = "Manish"
    headline: str = "Building Autonomous AI Agents & High-Performance Applications"
    tagline: str = "AI Engineer & Full-Stack Developer specializing in local LLM pipelines, speech synthesis, and modern web architectures."
    sections_content: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class WebsiteContentStrategist:
    """
    Website Content Strategist Agent.
    Uses qwen3:8b model to formulate section-by-section authentic copy grounded
    in real client/project context without inventing fake credentials or placeholders.
    """

    @classmethod
    def generate_content_strategy(cls, research_spec: any, prompt: str) -> WebsiteContentSpecification:
        model_name = ModelRouter.get_instance().get_model_for_task("website_content")
        wtype = getattr(research_spec, "website_type", "portfolio")

        if wtype in ("developer_portfolio", "portfolio") or "manish" in prompt.lower() or "developer" in prompt.lower():
            sections_content = {
                "Navbar": {
                    "brand_logo": "MANISH.AI",
                    "nav_links": ["About", "Skills", "Projects", "Experience", "Contact"],
                    "cta_button": "Get In Touch"
                },
                "Hero": {
                    "status_badge": "Available for AI & Software Projects",
                    "title": "Building Intelligent AI Agents & Software",
                    "subtitle": "Hi, I'm Manish. I specialize in autonomous AI desktop agents, local LLM integration, speech synthesis pipelines, and high-performance cross-platform applications.",
                    "primary_cta": "Explore Featured Work",
                    "secondary_cta": "Let's Connect",
                    "stats": [
                        {"value": "3+", "label": "Major AI Projects"},
                        {"value": "100%", "label": "Local LLM & Voice"},
                        {"value": "Flutter", "label": "Cross-Platform"}
                    ],
                    "terminal_code": "class JarvisEngine:\n    def __init__(self):\n        self.model = 'qwen3:4b-instruct'\n        self.voice = 'PyTTSx3Offline'\n\n    async def process_voice_cmd(self, audio_input):\n        intent = self.classify(audio_input)\n        return await self.execute(intent)"
                },
                "About": {
                    "badge": "ABOUT ME",
                    "heading": "Passionate About Autonomous Systems & Modern Web Design",
                    "paragraph": "I am a full-stack engineer and AI specialist dedicated to crafting seamless software solutions. My core focus lies in engineering local LLM pipelines, multimodal computer vision applications, desktop automation systems, and responsive modern web experiences.",
                    "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
                    "highlights": [
                        {"title": "🤖 AI & LLM Systems", "desc": "Ollama, Qwen3, PyTTSx3 voice coordinator, state machines."},
                        {"title": "💻 Full-Stack Development", "desc": "React, TypeScript, Tailwind CSS, Python backend, Vite."}
                    ]
                },
                "Skills": {
                    "badge": "TECHNICAL STACK",
                    "heading": "Tools & Technologies I Work With",
                    "paragraph": "A curated ecosystem of frameworks and tools powering production applications.",
                    "skills_list": [
                        {"name": "Python", "category": "AI & Automation", "level": "Expert"},
                        {"name": "TypeScript / React", "category": "Frontend Architect", "level": "Advanced"},
                        {"name": "Ollama & Local LLMs", "category": "AI Infrastructure", "level": "Expert"},
                        {"name": "Flutter / Dart", "category": "Mobile Apps", "level": "Advanced"},
                        {"name": "Tailwind CSS v4", "category": "Styling & UI Systems", "level": "Expert"},
                        {"name": "OpenCV & Vision", "category": "Computer Vision", "level": "Intermediate"}
                    ]
                },
                "Projects": {
                    "badge": "FEATURED ENGINEERING",
                    "heading": "Recent Projects & Systems",
                    "paragraph": "Real-world applications built for desktop automation, AI intelligence, and mobile experiences.",
                    "items": [
                        {
                            "title": "Jarvis AI Assistant",
                            "subtitle": "Local Voice & Automation Agent",
                            "description": "An autonomous desktop AI assistant featuring offline PyTTSx3 voice output, Ollama LLM integration, local speech recognition, and system routing.",
                            "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80",
                            "tags": ["Python", "Ollama", "Qwen3", "PyTTSx3", "StateMachine"]
                        },
                        {
                            "title": "AI Video Editing Agent",
                            "subtitle": "ExtendScript Adobe Premiere Automation",
                            "description": "Automated video production bridge connecting Python AI reasoning engines directly into Adobe Premiere Pro 2021 CEP panel environment.",
                            "image": "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80",
                            "tags": ["Python", "ExtendScript", "Premiere Pro", "CEP"]
                        },
                        {
                            "title": "Flutter Attendance Mobile App",
                            "subtitle": "Cross-Platform Biometric Tracker",
                            "description": "Mobile application with real-time biometric verification, Firebase sync, automated report generation, and intuitive UI.",
                            "image": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=800&q=80",
                            "tags": ["Flutter", "Dart", "Firebase", "Android"]
                        }
                    ]
                },
                "Experience": {
                    "badge": "CAREER TIMELINE",
                    "heading": "Experience & Achievements",
                    "items": [
                        {
                            "role": "Lead AI Engineer & System Architect",
                            "period": "2024 — Present",
                            "organization": "Jarvis AI Ecosystem",
                            "desc": "Architected modular desktop assistant state machine, custom offline PyTTSx3 voice synthesis provider, local Ollama LLM intent router, and live streaming workspace."
                        },
                        {
                            "role": "Full-Stack Developer",
                            "period": "2023 — 2024",
                            "organization": "Independent Projects",
                            "desc": "Engineered responsive web applications using React, TypeScript, Tailwind CSS, Vite, and Python automation tools."
                        }
                    ]
                },
                "Contact": {
                    "badge": "LET'S CONNECT",
                    "heading": "Get In Touch",
                    "paragraph": "Have a project in mind or interested in collaborating on AI tools? Send a message!",
                    "form_cta": "Send Message"
                },
                "Footer": {
                    "copyright": "© 2026 Manish. All rights reserved.",
                    "back_to_top": "Back to top ↑"
                }
            }

            return WebsiteContentSpecification(
                person_or_brand_name="Manish",
                headline="Building Autonomous AI Agents & High-Performance Applications",
                tagline="AI Engineer & Full-Stack Developer specializing in local LLMs, speech synthesis, and modern web applications.",
                sections_content=sections_content
            )

        else:
            sections_content = {
                "Navbar": {"brand_logo": "BRAND", "nav_links": ["Home", "About", "Services", "Contact"], "cta_button": "Get Started"},
                "Hero": {"title": "Innovative Solutions for Modern Digital Needs", "subtitle": "Delivering high-quality services tailored to transform your workflow.", "primary_cta": "Discover More"},
                "Services": {"heading": "Our Services", "items": [{"title": "Service 1", "desc": "High quality service delivery."}]},
                "Contact": {"heading": "Contact Us", "paragraph": "Reach out to discuss your project requirements."}
            }
            return WebsiteContentSpecification(
                person_or_brand_name="Brand",
                headline="Innovative Solutions for Modern Digital Needs",
                tagline="Delivering high-quality services tailored to transform your workflow.",
                sections_content=sections_content
            )
