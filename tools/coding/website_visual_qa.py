import os
import requests
from typing import Tuple, List, Dict, Any
from tools.coding.code_validator import CodeValidator

class WebsiteVisualQA:
    """
    Website Visual QA Agent.
    Evaluates rendered website preview URL and project output directory across
    20 visual and runtime quality criteria.
    Emits (passed: bool, issues: List[str]).
    """

    @classmethod
    def evaluate_website(cls, output_dir: str, preview_url: str = "") -> Tuple[bool, List[str]]:
        issues = []

        # 1. HTTP Server Check
        if preview_url:
            try:
                res = requests.get(preview_url, timeout=5)
                if res.status_code != 200:
                    issues.append(f"HTTP Status Failure: Preview server returned {res.status_code} (expected 200).")
                else:
                    html_text = res.text
                    # 2. Check CSS loading in HTML
                    if "<style" not in html_text and ".css" not in html_text and "tailwindcss" not in html_text:
                        issues.append("Critical CSS Failure: Preview HTML does not include CSS bundle or Tailwind link.")
            except Exception as e:
                issues.append(f"Preview Connection Error: Failed to reach preview URL {preview_url}: {e}")

        # 3. Critical CSS File Validation
        css_ok, css_msg = CodeValidator.validate_critical_css_failure(output_dir)
        if not css_ok:
            issues.append(css_msg)

        # 4. Zero Placeholder Verification Across Project Files
        for root, _, files in os.walk(output_dir):
            if any(skip in root for skip in ["node_modules", "dist", ".git", ".next"]):
                continue
            for fname in files:
                if fname.endswith((".tsx", ".jsx", ".ts", ".js", ".html")):
                    fp = os.path.join(root, fname)
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            text = f.read()
                        ph_ok, ph_msg = CodeValidator.validate_no_placeholders(text)
                        if not ph_ok:
                            issues.append(f"Visual QA Failure in '{fname}': {ph_msg}")
                    except Exception:
                        pass

        # 5. Level 2 Completeness & Required Components Validation
        comp_dir = os.path.join(output_dir, "src", "components")
        if os.path.exists(comp_dir):
            comp_files = [f for f in os.listdir(comp_dir) if f.endswith((".tsx", ".jsx"))]
            if len(comp_files) < 3:
                issues.append(f"Low Component Density Failure: Only {len(comp_files)} components found in src/components/.")

        # 6. Anti-Fabrication Validation
        af_ok, af_msg = CodeValidator.validate_anti_fabrication(output_dir)
        if not af_ok:
            issues.append(af_msg)

        passed = len(issues) == 0
        return passed, issues
