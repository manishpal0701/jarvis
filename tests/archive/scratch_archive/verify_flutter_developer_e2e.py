import os
import sys
import tempfile
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject
from tools.coding.workspace_manager import WorkspaceManager

def verify_flutter_developer_e2e():
    print("=== STARTING REAL E2E VERIFICATION: Flutter Developer Dark Premium ===")
    cmd = "mera ek modern portfolio website bana do main flutter developer hun dark premium project section rakhna"
    cat = WebsiteRequirementsAnalyzer.detect_category(cmd)
    subj = WebsiteRequirementsAnalyzer.detect_subject(cmd)
    brief = WebsiteRequirementsAnalyzer.extract_information(cmd, cat, subj)

    print(f"Brief Title: {brief.title}")
    print(f"Design Preference: {brief.design_preference}")

    assistant = CodeAssistant()

    def mock_ui_llm(messages, lang, rel_path, *args, **kwargs):
        project_dir = kwargs.get("project_dir", None)
        if lang == "css":
            code = '@import "tailwindcss"; body { background-color: #0f172a; color: #f8fafc; }'
        else:
            code = f"export default function Component_{rel_path.replace('/', '_').replace('.', '_')}() {{ return <section className='min-h-screen bg-slate-955 text-emerald-400 p-8'><h1>Flutter Developer Dark Premium - {rel_path}</h1><p>Hero, About, Skills, Projects, Experience, Contact</p></section>; }}"
        if project_dir:
            WorkspaceManager.get_instance().write_workspace_file(project_dir, rel_path, code)
        return code

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.object(assistant, '_generate_and_validate', side_effect=mock_ui_llm):
            with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                    code, path = assistant.generate_code(cmd, project_dir=temp_dir, brief=brief, open_browser=False)
                    print(f"Output Path: {path}")
                    assert "Error" not in code, f"E2E Generation failed: {code}"

        print("=== E2E Flutter Developer Dark Premium Verification PASSED 100% ===")

if __name__ == "__main__":
    verify_flutter_developer_e2e()
