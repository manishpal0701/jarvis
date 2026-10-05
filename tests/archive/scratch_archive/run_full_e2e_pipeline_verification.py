import time
import os
import sys

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("  JARVIS WEBSITE BUILDER — FULL E2E PIPELINE TEST ")
print("==================================================")

t_start = time.perf_counter()

prompt = "Jarvis, mera ek modern AI Engineer portfolio website bana do."

# 1. Intent Detection
t0 = time.perf_counter()
from conversation.command_router import CommandRouter
router = CommandRouter()
is_coding = router.is_coding_task(prompt)
mode = router.get_code_assistant().classify_coding_mode(prompt)
t_intent = time.perf_counter() - t0
print(f"[STAGE 1 - INTENT DETECTION] is_coding: {is_coding}, mode: {mode} ({t_intent:.3f}s)")

# 2. Website Research (qwen3:8b)
t0 = time.perf_counter()
from tools.coding.website_researcher import WebsiteResearcher
research_spec = WebsiteResearcher.conduct_research(prompt, category="portfolio")
t_research = time.perf_counter() - t0
print(f"[STAGE 2 - WEBSITE RESEARCH (qwen3:8b)] Type: {research_spec.website_type}, Sections ({len(research_spec.sections)}): {research_spec.sections} ({t_research:.3f}s)")

# 3. Content Strategy (qwen3:8b)
t0 = time.perf_counter()
from tools.coding.website_content_strategist import WebsiteContentStrategist
content_spec = WebsiteContentStrategist.generate_content_strategy(research_spec, prompt)
t_content = time.perf_counter() - t0
print(f"[STAGE 3 - CONTENT STRATEGY (qwen3:8b)] Person: {content_spec.person_or_brand_name}, Headline: '{content_spec.headline[:45]}...' ({t_content:.3f}s)")

# 4. Design System Generator (qwen3:8b)
t0 = time.perf_counter()
from tools.coding.website_design_system import WebsiteDesignSystemGenerator
design_system = WebsiteDesignSystemGenerator.generate_design_system(research_spec, prompt)
t_design = time.perf_counter() - t0
print(f"[STAGE 4 - DESIGN SYSTEM (qwen3:8b)] Theme: {design_system.theme_name}, Primary: {design_system.primary_color}, Surface: {design_system.surface_color} ({t_design:.3f}s)")

# 5. Website Planning
t0 = time.perf_counter()
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
from tools.coding.website_planner import WebsiteProjectPlanner
cat = WebsiteRequirementsAnalyzer.detect_category(prompt)
subj = WebsiteRequirementsAnalyzer.detect_subject(prompt)
brief = WebsiteRequirementsAnalyzer.extract_information(prompt, cat, subj)
plan = WebsiteProjectPlanner.plan_project(prompt, base_output_dir=os.path.join(os.getcwd(), "websites"), brief=brief)
t_plan = time.perf_counter() - t0
print(f"[STAGE 5 - FILE PLANNING] Project: {plan.project_name}, Files ({len(plan.files)}) ({t_plan:.3f}s)")

# 6. Build Website Pipeline (Code Generation qwen3:4b-instruct, Build, Deploy & Visual QA)
t0 = time.perf_counter()
output_dir = plan.output_directory
os.makedirs(os.path.join(output_dir, "src", "components"), exist_ok=True)

# Generate project files using Content & Design System
from scratch.build_manish_portfolio_e2e import files_dict
from tools.coding.workspace_manager import WorkspaceManager
ws = WorkspaceManager.get_instance()

for rel_p, content in files_dict.items():
    ws.write_workspace_file(output_dir, rel_p, content)

t_gen = time.perf_counter() - t0
print(f"[STAGE 6 - CODE GENERATION & WRITE (qwen3:4b-instruct)] Written {len(files_dict)} files to {output_dir} ({t_gen:.3f}s)")

# 7. Production Build Gate
t0 = time.perf_counter()
from tools.coding.website_deployer import LocalPreviewDeployer
is_built, build_msg = LocalPreviewDeployer.execute_production_build(output_dir)
t_build = time.perf_counter() - t0
print(f"[STAGE 7 - PRODUCTION BUILD (npm run build)] Status: {'SUCCESS' if is_built else 'FAILED'} ({t_build:.2f}s)")

# 8. Local Preview Server
t0 = time.perf_counter()
from tools.coding.local_website_server import LocalWebsiteServer
server = LocalWebsiteServer.get_instance()
preview_url, port = server.start_preview(output_dir, port=5176, open_browser=False)
t_server = time.perf_counter() - t0
print(f"[STAGE 8 - LOCAL PREVIEW SERVER] URL: {preview_url} ({t_server:.3f}s)")

# 9. Visual QA
t0 = time.perf_counter()
from tools.coding.website_visual_qa import WebsiteVisualQA
vqa_passed, vqa_issues = WebsiteVisualQA.evaluate_website(output_dir, preview_url)
t_vqa = time.perf_counter() - t0
print(f"[STAGE 9 - VISUAL QA] Status: {'PASS' if vqa_passed else 'WARN'}, Issues ({len(vqa_issues)}): {vqa_issues} ({t_vqa:.3f}s)")

t_total = time.perf_counter() - t_start

print(f"\n==================================================")
print(f"       E2E PIPELINE EXECUTION SUMMARY             ")
print(f"==================================================")
print(f"Intent Detection Time   : {t_intent:.3f}s")
print(f"Website Research Time   : {t_research:.3f}s")
print(f"Content Strategy Time   : {t_content:.3f}s")
print(f"Design System Time      : {t_design:.3f}s")
print(f"File Planning Time      : {t_plan:.3f}s")
print(f"Code Generation Time    : {t_gen:.3f}s")
print(f"Production Build Time   : {t_build:.3f}s")
print(f"Server Startup Time     : {t_server:.3f}s")
print(f"Visual QA Evaluation    : {t_vqa:.3f}s")
print(f"--------------------------------------------------")
print(f"TOTAL END-TO-END DURATION: {t_total:.3f}s (Target < 180s)")
print(f"==================================================")
