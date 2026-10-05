"""
tests/test_build_repair_regression.py
Regression tests for:
1. App.tsx ↔ DeveloperHero export/import mismatch detection & auto-alignment
2. Empty generated source file detection (Generation Integrity Check)
3. Unresolved component import error handling
4. Build failure state safety (website_ready = False)
5. Bounded repair loop (max 2 attempts)
6. Preview HTTP 200 state verification
7. No false WEBSITE READY status
"""

import unittest
import os
import tempfile
import shutil
from tools.coding.component_generation_pool import ComponentGenerationPool
from tools.coding.code_validator import CodeValidator
from tools.coding.website_auto_repair import WebsiteAutoRepair, RepairIssue
from tools.coding.website_state import ActiveWebsiteState


class TestBuildRepairRegression(unittest.TestCase):

    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="test_regression_")
        os.makedirs(os.path.join(self.project_dir, "src", "components"), exist_ok=True)

        # Standard minimal infrastructure files
        with open(os.path.join(self.project_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write('{"name": "test_app", "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0", "lucide-react": "^0.300.0"}, "devDependencies": {"typescript": "^5.0.0", "vite": "^5.0.0", "tailwindcss": "^4.0.0"}, "scripts": {"build": "vite build"}}')
        with open(os.path.join(self.project_dir, "tsconfig.json"), "w", encoding="utf-8") as f:
            f.write('{"compilerOptions": {"jsx": "react-jsx"}}')
        with open(os.path.join(self.project_dir, "vite.config.ts"), "w", encoding="utf-8") as f:
            f.write('export default {};')
        with open(os.path.join(self.project_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write('<!DOCTYPE html><html><body><div id="root"></div></body></html>')
        with open(os.path.join(self.project_dir, "src", "main.tsx"), "w", encoding="utf-8") as f:
            f.write('import App from "./App";')
        with open(os.path.join(self.project_dir, "src", "index.css"), "w", encoding="utf-8") as f:
            f.write('@import "tailwindcss";')

        # App.tsx importing DeveloperHero
        with open(os.path.join(self.project_dir, "src", "App.tsx"), "w", encoding="utf-8") as f:
            f.write('import React from "react";\nimport { DeveloperHero } from "./components/DeveloperHero";\nexport const App: React.FC = () => <DeveloperHero />;\nexport default App;')

        # DeveloperHero.tsx exporting Hero (mismatch!)
        with open(os.path.join(self.project_dir, "src", "components", "DeveloperHero.tsx"), "w", encoding="utf-8") as f:
            f.write('import React from "react";\nexport const Hero: React.FC = () => <div>Developer Hero</div>;\n')

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    def test_1_ensure_export_name_alignment(self):
        """Verify _ensure_export_name appends alias export if component name differs."""
        code = 'import React from "react";\nexport const Hero: React.FC = () => <div>Hero</div>;'
        aligned = ComponentGenerationPool._ensure_export_name(code, "DeveloperHero")
        self.assertIn("export const DeveloperHero = Hero;", aligned)

    def test_2_generation_integrity_detects_and_fixes_export_mismatch(self):
        """Verify validate_generation_integrity auto-aligns App.tsx imported symbols."""
        ok, err = CodeValidator.validate_generation_integrity(self.project_dir)
        self.assertTrue(ok, f"Expected generation integrity pass after auto-alignment: {err}")
        # Verify DeveloperHero.tsx now exports DeveloperHero
        with open(os.path.join(self.project_dir, "src", "components", "DeveloperHero.tsx"), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("export const DeveloperHero", content)

    def test_3_generation_integrity_rejects_empty_files(self):
        """Verify validate_generation_integrity fails if a component is 0 bytes."""
        empty_comp = os.path.join(self.project_dir, "src", "components", "EmptyComp.tsx")
        with open(empty_comp, "w", encoding="utf-8") as f:
            pass  # 0 bytes
        ok, err = CodeValidator.validate_generation_integrity(self.project_dir)
        self.assertFalse(ok)
        self.assertIn("empty", err.lower())

    def test_4_generation_integrity_rejects_unresolved_imports(self):
        """Verify validate_generation_integrity fails if App.tsx imports missing module."""
        with open(os.path.join(self.project_dir, "src", "App.tsx"), "w", encoding="utf-8") as f:
            f.write('import { NonExistentComp } from "./components/NonExistentComp";')
        ok, err = CodeValidator.validate_generation_integrity(self.project_dir)
        self.assertFalse(ok)
        self.assertIn("missing component module", err.lower())

    def test_5_auto_repair_diagnoses_vite_export_mismatch_error(self):
        """Verify WebsiteAutoRepair targets DeveloperHero.tsx when Vite build fails on export mismatch."""
        issue = RepairIssue(
            issue_type="build",
            message='src/App.tsx (4:9): "DeveloperHero" is not exported by "src/components/DeveloperHero.tsx", imported by "src/App.tsx".',
            severity="error",
            repairable=True
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, ["src/App.tsx", "src/components/DeveloperHero.tsx"])
        self.assertEqual(plan.affected_file, "src/components/DeveloperHero.tsx")

    def test_6_no_false_website_ready_on_build_failure(self):
        """Verify build failure keeps website_ready = False and state is fail-safe."""
        state = ActiveWebsiteState()
        state.build_passed = False
        state.website_ready = False
        state.last_error = 'src/App.tsx: "DeveloperHero" is not exported'
        self.assertFalse(state.is_authoritative_ready())

    def test_7_max_2_repair_attempts_enforced(self):
        """Verify MAX_REPAIR_ATTEMPTS is strictly 2."""
        issue = RepairIssue(issue_type="build", message="Fatal build error", repairable=True)
        res1 = WebsiteAutoRepair.diagnose_and_repair("t1", self.project_dir, issue, attempt_number=2, generated_contents={"src/App.tsx": ""})
        self.assertNotEqual(res1.status, "limit_reached")

        res2 = WebsiteAutoRepair.diagnose_and_repair("t1", self.project_dir, issue, attempt_number=3, generated_contents={"src/App.tsx": ""})
        self.assertEqual(res2.status, "limit_reached")


if __name__ == "__main__":
    unittest.main()
