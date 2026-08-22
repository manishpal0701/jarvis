import os
import sys
import tempfile
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import processCommand, is_coding_task
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.website_planner import WebsiteProjectPlan, WebsiteFilePlan

def test_main_runtime_e2e():
    print("=== STARTING FULL RUNTIME E2E TEST VIA MAIN.PY ENTRY POINT ===")
    cmd = "mera ek modern portfolio website banaa do main ek python developer hun"

    self_is_coding = is_coding_task(cmd)
    print(f"Command: '{cmd}'")
    print(f"is_coding_task check: {self_is_coding}")
    assert self_is_coding is True, "is_coding_task must return True for website build command."

    def mock_ui_llm(messages, lang, rel_path, *args, **kwargs):
        project_dir = kwargs.get("project_dir", None)
        if lang == "css":
            code = '@import "tailwindcss"; body { background-color: #0f172a; color: #f8fafc; }'
        else:
            code = f"export default function Component_{rel_path.replace('/', '_').replace('.', '_')}() {{ return <section className='min-h-screen bg-slate-900 text-white p-8'><h1>Python Developer Portfolio Section</h1><p>Hero, About, Skills, Projects, Experience, Contact</p></section>; }}"
        if project_dir:
            WorkspaceManager.get_instance().write_workspace_file(project_dir, rel_path, code)
        return code

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('tools.coding.code_assistant.CodeAssistant._generate_and_validate', side_effect=mock_ui_llm):
            with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                    with patch('speech.speak'):
                        output_dir = os.path.join(temp_dir, "websites", "python_portfolio")
                        plan = WebsiteProjectPlan(
                            project_name="python_portfolio",
                            framework="react",
                            entry_file="src/App.tsx",
                            output_directory=output_dir,
                            files=[
                                WebsiteFilePlan("package.json", "json", "infrastructure"),
                                WebsiteFilePlan("tsconfig.json", "json", "infrastructure"),
                                WebsiteFilePlan("vite.config.ts", "typescript", "infrastructure"),
                                WebsiteFilePlan("index.html", "html", "infrastructure"),
                                WebsiteFilePlan("src/main.tsx", "tsx", "infrastructure"),
                                WebsiteFilePlan("src/App.tsx", "tsx", "entry"),
                                WebsiteFilePlan("src/index.css", "css", "styling"),
                                WebsiteFilePlan("src/components/Navbar.tsx", "tsx", "component"),
                                WebsiteFilePlan("src/components/Hero.tsx", "tsx", "component"),
                                WebsiteFilePlan("src/components/About.tsx", "tsx", "component"),
                                WebsiteFilePlan("src/components/Skills.tsx", "tsx", "component"),
                                WebsiteFilePlan("src/components/Projects.tsx", "tsx", "component"),
                                WebsiteFilePlan("src/components/Contact.tsx", "tsx", "component")
                            ]
                        )
                        with patch('tools.coding.website_planner.WebsiteProjectPlanner.plan_project', return_value=plan):
                            print("Executing processCommand(cmd)...")
                            processCommand(cmd)

                            print(f"Output Directory: {output_dir}")

                            expected_files = [
                                "package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx",
                                "src/App.tsx", "src/index.css"
                            ]
                            for ef in expected_files:
                                fp = os.path.join(output_dir, ef)
                                assert os.path.isfile(fp), f"File physically missing from disk: {ef}"
                                assert os.path.getsize(fp) > 0, f"File on disk is empty: {ef}"

                            dist_index = os.path.join(output_dir, "dist", "index.html")
                            dist_assets = os.path.join(output_dir, "dist", "assets")
                            assert os.path.isfile(dist_index), "Physical dist/index.html must exist."
                            assert os.path.isdir(dist_assets), "Physical dist/assets directory must exist."
                            assert len(os.listdir(dist_assets)) > 0, "dist/assets must contain built JS/CSS."

    print("=== FULL RUNTIME E2E TEST VIA MAIN.PY PASSED 100% ===")

if __name__ == "__main__":
    test_main_runtime_e2e()
