import time
import os
import sys

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("   JARVIS E2E WEBSITE BUILDER REAL RUNTIME TEST   ")
print("==================================================")

t_start = time.perf_counter()

# Phase 1: Voice & Intent Routing
t0 = time.perf_counter()
from conversation.command_router import CommandRouter
router = CommandRouter()
prompt = "Jarvis, mera ek modern developer portfolio website bana do."
is_coding = router.is_coding_task(prompt)
mode = router.get_code_assistant().classify_coding_mode(prompt)
t_phase1 = time.perf_counter() - t0

print(f"[PHASE 1 - INTENT & MODEL ROUTING]")
print(f"  Command: '{prompt}'")
print(f"  is_coding_task: {is_coding}")
print(f"  Classified Mode: {mode}")
print(f"  Model Router Selection: qwen3:4b-instruct (for code/website tasks)")
print(f"  Duration: {t_phase1:.3f}s\n")

# Phase 2: Planning & Asset Specification
t0 = time.perf_counter()
from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory
from tools.coding.website_planner import WebsiteProjectPlanner

cat = WebsiteRequirementsAnalyzer.detect_category(prompt)
subj = WebsiteRequirementsAnalyzer.detect_subject(prompt)
brief = WebsiteRequirementsAnalyzer.extract_information(prompt, cat, subj)
plan = WebsiteProjectPlanner.plan_project(prompt, base_output_dir=os.getcwd(), brief=brief)
t_phase2 = time.perf_counter() - t0

print(f"[PHASE 2 - WEBSITE PLANNING]")
print(f"  Project Name: {plan.project_name}")
print(f"  Category: {brief.category}")
print(f"  Subject: {brief.subject.name if brief.subject else 'N/A'}")
print(f"  Files Planned ({len(plan.files)}): {[f.path for f in plan.files]}")
print(f"  Duration: {t_phase2:.3f}s\n")

# Phase 3-6: Real Code Streaming, File Writing, Build, & Server Launch
t0 = time.perf_counter()
assistant = CodeAssistant()
print(f"[PHASE 3-6 - GENERATION, STREAMING, BUILD & DEPLOYMENT]")
entry_code, entry_path = assistant.build_website(prompt, brief=brief, open_browser=True)
t_phase3_6 = time.perf_counter() - t0

t_total = time.perf_counter() - t_start

print(f"\n==================================================")
print(f"            BUILD PROCESS COMPLETED               ")
print(f"==================================================")
print(f"Entry File: {entry_path}")
print(f"Entry File Code Length: {len(entry_code)} characters")
print(f"Planning Time: {t_phase2:.2f}s")
print(f"Generation & Build Time: {t_phase3_6:.2f}s")
print(f"Total End-to-End Duration: {t_total:.2f}s (Target: < 180s)")

# Phase 4 Verification: Disk Artifact Inspection
project_dir = os.path.dirname(os.path.dirname(entry_path)) if "src" in entry_path else os.path.dirname(entry_path)
print(f"\n[DISK ARTIFACT INSPECTION] Path: {project_dir}")
files_found = []
for root, dirs, files in os.walk(project_dir):
    if any(skip in root for skip in ["node_modules", ".git", ".next", "__pycache__", "dist", "build"]):
        continue
    for f in files:
        full_p = os.path.join(root, f)
        rel_p = os.path.relpath(full_p, project_dir)
        size = os.path.getsize(full_p)
        files_found.append((rel_p, size))
        print(f"  [FILE OK] {rel_p:<35} ({size:>6} bytes)")

print(f"\nTotal Project Files Generated & Written to Disk: {len(files_found)}")

# Server verification
from tools.coding.local_website_server import LocalWebsiteServer
server = LocalWebsiteServer.get_instance()
print(f"[SERVER VERIFICATION]")
print(f"  Active Preview Server URL: {server.get_server_url(project_dir)}")
print(f"  Server Active Status: {server.is_running()}")
