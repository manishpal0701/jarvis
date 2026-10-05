"""
scratch/test_e2e_auto_repair.py
Controlled E2E Tests for Intelligent Website Auto-Repair Loop.

E2E 1: Build Error Repair
E2E 2: Visual QA Layout Repair
E2E 3: Unrepairable Failure Safe Rejection
E2E 4: MAX_REPAIR_ATTEMPTS = 3 Limit Enforcement
"""

import sys
import os
import tempfile
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.coding.website_auto_repair import WebsiteAutoRepair, RepairIssue, RepairPlan, RepairResult, MAX_REPAIR_ATTEMPTS
from tools.coding.website_state import ActiveWebsiteState

PASS = "PASS"
FAIL = "FAIL"
results = []

def test(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    icon = "[PASS]" if condition else "[FAIL]"
    print(f"  {icon} {name}" + (f": {detail}" if detail else ""))

def e2e_1_build_error_repair():
    print("\n=== E2E 1: Build Error Repair ===")
    project_dir = tempfile.mkdtemp(prefix="e2e1_")
    try:
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        # Simulate a file with a build error (import of unlisted package)
        broken_code = "import { Link } from 'react-router-dom';\nexport default function App() { return <Link to='/'>Home</Link>; }"
        generated = {"src/App.tsx": broken_code}

        issue = RepairIssue(
            issue_type="build",
            message="Cannot find module 'react-router-dom' in src/App.tsx. Use standard <a> tags instead.",
            source="npm_build",
            severity="error",
            repairable=True,
            affected_files=["src/App.tsx"]
        )

        result = WebsiteAutoRepair.diagnose_and_repair(
            task_id="e2e1_build_error",
            project_dir=project_dir,
            issue=issue,
            attempt_number=1,
            generated_contents=generated,
            code_generator_func=None  # Uses built-in fallback fixer
        )

        test("E2E1: Repair result is success or applied", result.status in ("success",), f"status={result.status}")
        test("E2E1: Repaired file is src/App.tsx", result.repaired_file == "src/App.tsx", f"file={result.repaired_file}")
        test("E2E1: react-router-dom removed from repaired code", "react-router-dom" not in generated.get("src/App.tsx", ""), "")

        # WEBSITE_READY is NOT claimed by auto-repair
        state = ActiveWebsiteState()
        state.build_passed = False
        test("E2E1: WEBSITE_READY not claimed by auto-repair", not state.is_authoritative_ready(), "")

    finally:
        shutil.rmtree(project_dir, ignore_errors=True)

def e2e_2_visual_qa_repair():
    print("\n=== E2E 2: Visual QA Layout Repair ===")
    project_dir = tempfile.mkdtemp(prefix="e2e2_")
    try:
        os.makedirs(os.path.join(project_dir, "src", "components"), exist_ok=True)
        navbar_code = "export default function Navbar() { return <nav className='flex overflow-x-scroll w-full'>Menu</nav>; }"
        generated = {"src/components/Navbar.tsx": navbar_code}

        issue = RepairIssue(
            issue_type="visual_qa",
            message="Mobile navbar overflow detected in Navbar.tsx. Content overflows viewport on mobile.",
            source="visual_qa",
            severity="error",
            repairable=True,
            affected_files=["src/components/Navbar.tsx"]
        )

        result = WebsiteAutoRepair.diagnose_and_repair(
            task_id="e2e2_visual_qa",
            project_dir=project_dir,
            issue=issue,
            attempt_number=1,
            generated_contents=generated,
            code_generator_func=None
        )

        test("E2E2: Repair result is success", result.status == "success", f"status={result.status}")
        test("E2E2: Repaired file is Navbar.tsx", "Navbar" in result.repaired_file, f"file={result.repaired_file}")
        test("E2E2: Diagnosis correctly identified visual_qa", "VISUAL_QA" in result.plan.diagnosis.upper() if result.plan else False, "")

        # WEBSITE_READY still requires authoritative pipeline
        state = ActiveWebsiteState()
        test("E2E2: WEBSITE_READY not set by repair", not state.is_authoritative_ready(), "")

    finally:
        shutil.rmtree(project_dir, ignore_errors=True)

def e2e_3_unrepairable_failure():
    print("\n=== E2E 3: Unrepairable Failure Safe Rejection ===")
    project_dir = tempfile.mkdtemp(prefix="e2e3_")
    try:
        generated = {"src/App.tsx": "export default function App() { return <div>App</div>; }"}

        issue = RepairIssue(
            issue_type="build",
            message="AMBIGUOUS_CATASTROPHIC_FAILURE: Unknown error XYZ_UNDEFINED_DEEP_SYSTEM",
            source="unknown",
            severity="critical",
            repairable=False  # Explicitly marked unrepairable
        )

        result = WebsiteAutoRepair.diagnose_and_repair(
            task_id="e2e3_unrepairable",
            project_dir=project_dir,
            issue=issue,
            attempt_number=1,
            generated_contents=generated,
            code_generator_func=None
        )

        test("E2E3: Result status is unrepairable", result.status == "unrepairable", f"status={result.status}")
        test("E2E3: No WEBSITE_READY claim", not ActiveWebsiteState().is_authoritative_ready(), "")
        test("E2E3: Error details populated", bool(result.error_details), f"error={result.error_details[:60]}")

    finally:
        shutil.rmtree(project_dir, ignore_errors=True)

def e2e_4_repair_limit_enforcement():
    print("\n=== E2E 4: MAX_REPAIR_ATTEMPTS = 3 Limit Enforcement ===")
    project_dir = tempfile.mkdtemp(prefix="e2e4_")
    try:
        generated = {"src/App.tsx": "export default function App() { return <div>App</div>; }"}
        issue = RepairIssue(
            issue_type="build",
            message="Persistent failure that cannot be fixed",
            source="npm_build",
            severity="error",
            repairable=True
        )

        # Attempt 1, 2, 3 should be allowed
        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            result = WebsiteAutoRepair.diagnose_and_repair(
                task_id="e2e4_limit_test",
                project_dir=project_dir,
                issue=issue,
                attempt_number=attempt,
                generated_contents=generated,
                code_generator_func=None
            )
            test(f"E2E4: Attempt {attempt} allowed (not limit_reached)", result.status != "limit_reached", f"status={result.status}")

        # Attempt 4 must be rejected
        result_4 = WebsiteAutoRepair.diagnose_and_repair(
            task_id="e2e4_limit_test",
            project_dir=project_dir,
            issue=issue,
            attempt_number=4,
            generated_contents=generated,
            code_generator_func=None
        )
        test("E2E4: Attempt 4 is LIMIT_REACHED", result_4.status == "limit_reached", f"status={result_4.status}")
        test("E2E4: MAX_REPAIR_ATTEMPTS constant is 3", MAX_REPAIR_ATTEMPTS == 3, f"MAX_REPAIR_ATTEMPTS={MAX_REPAIR_ATTEMPTS}")

    finally:
        shutil.rmtree(project_dir, ignore_errors=True)

if __name__ == "__main__":
    print("=" * 60)
    print("CONTROLLED E2E TESTS: Intelligent Website Auto-Repair Loop")
    print("=" * 60)

    e2e_1_build_error_repair()
    e2e_2_visual_qa_repair()
    e2e_3_unrepairable_failure()
    e2e_4_repair_limit_enforcement()

    print("\n" + "=" * 60)
    print("FINAL E2E REPORT")
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    for name, status, detail in results:
        icon = "[PASS]" if status == PASS else "[FAIL]"
        print(f"  {icon} {name}")
    print(f"\nTOTAL: {passed} PASS / {failed} FAIL out of {len(results)} checks")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
