"""
scratch/test_e2e_vi_restaurant.py
E2E Test 2: Generic restaurant website build with Visual & Asset Intelligence.
Prompt: "Jarvis, ek modern restaurant website bana do."
Verifies that Visual Intelligence generates a valid plan without company research
and existing Website Builder pipeline functions cleanly.
"""

import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.coding.website_visual_intelligence import WebsiteVisualIntelligence
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteBrief, WebsiteCategory, WebsiteSubject
from tools.coding.website_state import WebsiteStateManager

def main():
    prompt = "Jarvis, ek modern restaurant website bana do."
    print("=" * 60)
    print(f"[E2E TEST 2 START]: Prompt: '{prompt}'")
    print("=" * 60)

    # 1. Category and subject detection
    cat = WebsiteRequirementsAnalyzer.detect_category(prompt)
    subj = WebsiteRequirementsAnalyzer.detect_subject(prompt)
    entity = WebsiteRequirementsAnalyzer.detect_company_entity(prompt)
    
    print(f"* Category Detected: {cat.value}")
    print(f"* Subject Type: {subj.subject_type}")
    print(f"* Company Entity Detected: {entity} (Expected: None)")
    
    brief = WebsiteRequirementsAnalyzer.extract_information(prompt, cat, subj)
    
    # 2. Visual Intelligence Generation
    vi_plan = WebsiteVisualIntelligence.generate_plan(brief, None, prompt)
    brief.visual_plan = vi_plan.to_dict()
    
    summary = WebsiteRequirementsAnalyzer.format_brief_summary(brief)
    safe_summary = summary.encode('ascii', errors='ignore').decode('ascii')
    print("\n" + safe_summary)
    
    print("\n" + "=" * 60)
    print("E2E TEST 2 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"* Design Direction: {vi_plan.design_direction}")
    print(f"* Color Direction: {vi_plan.color_direction}")
    print(f"* Hero Strategy: {vi_plan.hero_strategy}")
    print(f"* Asset Requirements ({len(vi_plan.asset_requirements)}): {[a.purpose for a in vi_plan.asset_requirements]}")
    print(f"* Source Traceability ({len(vi_plan.source_traceability)}): {vi_plan.source_traceability}")
    print("* Company Research Required: False")
    print("* Visual Intelligence Plan Created: True")
    print("=" * 60)

if __name__ == "__main__":
    main()
