import time
import os
import sys

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("   REAL E2E WEBSITE QUALITY TEST & VERIFICATION   ")
print("==================================================")

t_start = time.perf_counter()

prompt = "Jarvis, mere liye ek modern AI Engineer portfolio website bana do."

# 1. Intent Detection & Model Router Verification
from conversation.command_router import CommandRouter
router = CommandRouter()
is_coding = router.is_coding_task(prompt)
mode = router.get_code_assistant().classify_coding_mode(prompt)

from ai.model_router import ModelRouter
m_router = ModelRouter.get_instance()
m_research = m_router.get_model_for_task("website_research")
m_content = m_router.get_model_for_task("website_content")
m_design = m_router.get_model_for_task("website_design")
m_plan = m_router.get_model_for_task("website_planning")
m_code = m_router.get_model_for_task("website_generation")

print(f"[MODEL VERIFICATION]")
print(f"  Research Model: {m_research}")
print(f"  Content Strategy Model: {m_content}")
print(f"  Design System Model: {m_design}")
print(f"  Planning Model: {m_plan}")
print(f"  Code Generation Model: {m_code}\n")

# 2. Execute Research & Design System Stage
from tools.coding.website_researcher import WebsiteResearcher
from tools.coding.website_content_strategist import WebsiteContentStrategist
from tools.coding.website_design_system import WebsiteDesignSystemGenerator

research_spec = WebsiteResearcher.conduct_research(prompt, category="portfolio")
content_spec = WebsiteContentStrategist.generate_content_strategy(research_spec, prompt)
design_system = WebsiteDesignSystemGenerator.generate_design_system(research_spec, prompt)

print(f"[STAGE 1 - RESEARCH & DESIGN]")
print(f"  Category: {research_spec.website_type}")
print(f"  Brand/Person: {content_spec.person_or_brand_name}")
print(f"  Design Theme: {design_system.theme_name}")
print(f"  Sections ({len(research_spec.sections)}): {research_spec.sections}\n")

# 3. Execute Code Assistant build_website
from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
from tools.coding.website_planner import WebsiteProjectPlanner

cat = WebsiteRequirementsAnalyzer.detect_category(prompt)
subj = WebsiteRequirementsAnalyzer.detect_subject(prompt)
brief = WebsiteRequirementsAnalyzer.extract_information(prompt, cat, subj)

assistant = CodeAssistant()
print("[STAGE 2 - CODE GENERATION, STREAMING & BUILD]")
entry_code, entry_path = assistant.build_website(prompt, brief=brief, open_browser=False)

project_dir = os.path.dirname(os.path.dirname(entry_path)) if "src" in entry_path else os.path.dirname(entry_path)

# 4. Local Preview Server Startup
from tools.coding.local_website_server import LocalWebsiteServer
server = LocalWebsiteServer.get_instance()
preview_url, port = server.start_preview(project_dir, port=5174, open_browser=False)

t_total = time.perf_counter() - t_start

print(f"\n==================================================")
print(f"       E2E EXECUTION COMPLETED                    ")
print(f"==================================================")
print(f"Project Path: {project_dir}")
print(f"Entry File: {entry_path}")
print(f"Preview URL: {preview_url}")
print(f"Total Execution Time: {t_total:.2f}s")
