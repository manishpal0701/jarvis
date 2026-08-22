import time
import os
import sys

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("  GENERATING MANISH — AI ENGINEER PORTFOLIO       ")
print("==================================================")

t_start = time.perf_counter()

from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject
from tools.coding.website_planner import WebsiteProjectPlanner

prompt = "Jarvis, mera ek modern AI engineer developer portfolio website bana do for Manish."

cat = WebsiteRequirementsAnalyzer.detect_category(prompt)
subj = WebsiteRequirementsAnalyzer.detect_subject(prompt)
brief = WebsiteRequirementsAnalyzer.extract_information(prompt, cat, subj)

brief.person_name = "Manish"
brief.business_name = "Manish — AI Engineer & Full-Stack Developer"

plan = WebsiteProjectPlanner.plan_project(prompt, base_output_dir=os.path.join(os.getcwd(), "websites"), brief=brief)

assistant = CodeAssistant()
print(f"Target Output Directory: {plan.output_directory}")

entry_code, entry_path = assistant.build_website(prompt, brief=brief, open_browser=False)

t_total = time.perf_counter() - t_start

print(f"\n[GENERATION COMPLETE] Total Time: {t_total:.2f}s")
print(f"Entry File: {entry_path}")

# Run production build
from tools.coding.website_deployer import LocalPreviewDeployer
print("\n[RUNNING PRODUCTION BUILD GATE]")
is_built, build_msg = LocalPreviewDeployer.execute_production_build(plan.output_directory)
print(f"Production Build Status: {'SUCCESS' if is_built else 'FAILED'}")
print(f"Build Output Msg: {build_msg[:200]}")
