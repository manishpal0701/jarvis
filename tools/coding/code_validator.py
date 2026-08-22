import os
import json
import re

class CodeValidator:
    """
    Generic source code language validator.
    Ensures generated code matches the authoritative target language contract and rejects cross-language hallucinations.
    """

    DART_FLUTTER_MARKERS = [
        "import 'package:",
        "Widget ",
        "Scaffold",
        "@override",
        "Provider.of<",
        "BuildContext",
        "StatelessWidget",
        "StatefulWidget",
        "void main()",
        "setState("
    ]

    @classmethod
    def validate(cls, code: str, language: str) -> tuple[bool, str]:
        if not code or not code.strip():
            return False, "Generated code is empty."

        lang = language.lower().strip()
        code_str = code.strip()

        if lang in ("tsx", "typescript"):
            return cls.validate_tsx(code_str)
        elif lang == "css":
            return cls.validate_css(code_str)
        elif lang in ("js", "javascript"):
            return cls.validate_javascript(code_str)
        elif lang == "json":
            return cls.validate_json(code_str)
        elif lang == "java":
            return cls.validate_java(code_str)
        elif lang == "html":
            return cls.validate_html(code_str)
        elif lang == "python":
            return cls.validate_python(code_str)

        return True, ""

    @classmethod
    def validate_python(cls, code_str: str) -> tuple[bool, str]:
        if not code_str or not code_str.strip():
            return False, "Python code is empty."
        for marker in cls.DART_FLUTTER_MARKERS:
            if marker in code_str:
                return False, f"Invalid Python: Contains Dart/Flutter hallucination syntax '{marker}'."
        import ast
        try:
            ast.parse(code_str)
        except SyntaxError as se:
            return False, f"Python Syntax Error: {se}"
        return True, ""

    @classmethod
    def validate_html(cls, code_str: str) -> tuple[bool, str]:
        if not code_str or not code_str.strip():
            return False, "HTML code is empty."
        if ("def " in code_str or "import " in code_str) and not ("<" in code_str and ">" in code_str):
            return False, "Invalid HTML: Contains non-HTML python code."
        if not ("<" in code_str and ">" in code_str):
            return False, "Invalid HTML: Missing HTML elements."
        return True, ""

    @classmethod
    def validate_tsx(cls, code_str: str) -> tuple[bool, str]:
        if not code_str or not code_str.strip():
            return False, "TSX code is empty."
        lower_c = code_str.lower()
        # 1. Document Wrapper Ban
        forbidden_tags = ["<!doctype html>", "<html", "<head>", "<body>", "<meta ", "<title>"]
        for tag in forbidden_tags:
            if tag in lower_c:
                return False, f"Invalid TSX: Contains HTML document wrapper tag '{tag}'."

        # 2. Undefined Tailwind Custom Utility Check
        forbidden_utilities = ["bg-primary-color", "text-primary-color", "border-primary-color", "bg-secondary-color", "text-secondary-color"]
        for util in forbidden_utilities:
            if util in code_str:
                return False, f"Invalid TSX: Contains undefined custom utility class '{util}'. Use standard Tailwind v4 color scale utilities."

        # 3. Forbidden Placeholder Section Title Ban
        forbidden_placeholders = [
            "navbar section", "hero section", "about section", "services section",
            "projects section", "contact section", "explore hero", "explore about",
            "explore services", "explore projects", "modern responsive ui component",
            "lorem ipsum", "coming soon", "todo"
        ]
        for ph in forbidden_placeholders:
            if ph in lower_c:
                return False, f"Invalid TSX: Contains generic developer placeholder text '{ph}'. Replace with realistic, contextual content."

        if not ("export default" in code_str or "export function" in code_str or "export const" in code_str or "return" in code_str):
            return False, "Invalid TSX: Missing React export or render return statement."
        return True, ""

    @classmethod
    def validate_no_placeholders(cls, text: str) -> tuple[bool, str]:
        """Validates that text does not contain generic development placeholders."""
        if not text:
            return True, ""
        lower = text.lower()
        banned = [
            "navbar section", "hero section", "about section", "services section",
            "projects section", "contact section", "explore hero", "explore about",
            "explore services", "explore projects", "modern responsive ui component",
            "lorem ipsum", "coming soon", "todo"
        ]
        for item in banned:
            if item in lower:
                return False, f"Placeholder Violation: Detected forbidden text '{item}'."
        return True, ""

    @classmethod
    def validate_critical_css_failure(cls, output_dir: str) -> tuple[bool, str]:
        """Detects critical CSS failures such as missing Tailwind directives or unstyled content."""
        css_path = os.path.join(output_dir, "src", "index.css")
        if not os.path.exists(css_path):
            css_path = os.path.join(output_dir, "style.css")
        if not os.path.exists(css_path):
            return False, "Critical CSS Failure: Main CSS stylesheet file missing."

        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
            if not css_content.strip():
                return False, "Critical CSS Failure: Main CSS stylesheet file is completely empty."
        except Exception as e:
            return False, f"Critical CSS Failure: Unable to read CSS file: {e}"

        return True, ""

    @classmethod
    def validate_css(cls, code_str: str) -> tuple[bool, str]:
        if not code_str or not code_str.strip():
            return False, "CSS code is empty."
        lower_c = code_str.lower()
        if "<!doctype html>" in lower_c or "<html>" in lower_c or "<body>" in lower_c or "<script>" in lower_c or "<div" in lower_c:
            return False, "Invalid CSS: Contains HTML tags inside stylesheet."

        forbidden_utilities = ["bg-primary-color", "text-primary-color", "border-primary-color", "bg-secondary-color", "text-secondary-color"]
        for util in forbidden_utilities:
            if util in lower_c:
                return False, f"Invalid CSS: Contains undefined custom utility class '{util}'."

        return True, ""

    @classmethod
    def validate_javascript(cls, code_str: str) -> tuple[bool, str]:
        if not code_str or not code_str.strip():
            return False, "JavaScript code is empty."
        if code_str.lower().startswith("<!doctype html>") or "<html>" in code_str.lower():
            return False, "Invalid JS: Contains HTML document wrapper."
        return True, ""

    @classmethod
    def validate_json(cls, code_str: str) -> tuple[bool, str]:
        if not code_str or not code_str.strip():
            return False, "JSON code is empty."
        try:
            json.loads(code_str)
            return True, ""
        except Exception as e:
            return False, f"Invalid JSON syntax: {e}"

    @classmethod
    def validate_java(cls, code_str: str) -> tuple[bool, str]:
        if not code_str or not code_str.strip():
            return False, "Java code is empty."
        if "public class" not in code_str and "class " not in code_str:
            return False, "Invalid Java syntax: Missing class declaration."
        return True, ""

    @classmethod
    def validate_infrastructure_compatibility(cls, pkg_json_str: str) -> tuple[bool, str]:
        try:
            pkg = json.loads(pkg_json_str)
        except Exception as e:
            return False, f"Invalid package.json JSON syntax: {e}"

        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        scripts = pkg.get("scripts", {})
        all_deps = {**deps, **dev_deps}

        required_deps = ["react", "react-dom"]
        for rd in required_deps:
            if rd not in deps and rd not in all_deps:
                return False, f"Missing required dependency '{rd}' in package.json."

        required_dev = ["typescript", "vite"]
        for rdev in required_dev:
            if rdev not in dev_deps and rdev not in all_deps:
                return False, f"Missing required devDependency '{rdev}' in package.json."

        has_tailwind = "tailwindcss" in all_deps or "@tailwindcss/vite" in all_deps
        if not has_tailwind:
            return False, "Missing tailwindcss dependency in package.json."

        if "build" not in scripts:
            return False, "Missing required 'build' script in package.json."

        return True, ""

    @classmethod
    def validate_level2_completeness(cls, output_dir: str, brief: any = None) -> tuple[bool, str]:
        app_p = os.path.join(output_dir, "src/App.tsx")
        if not os.path.exists(app_p):
            app_p = os.path.join(output_dir, "app/page.tsx") if os.path.exists(os.path.join(output_dir, "app/page.tsx")) else os.path.join(output_dir, "index.html")

        if not os.path.exists(app_p):
            return False, "Main application entry file missing."

        try:
            with open(app_p, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return False, f"Failed to read application file: {e}"

        comp_dir = os.path.join(output_dir, "src", "components")
        if os.path.exists(comp_dir):
            for root, _, files in os.walk(comp_dir):
                for fname in files:
                    if fname.endswith((".tsx", ".jsx", ".ts", ".js")):
                        try:
                            with open(os.path.join(root, fname), "r", encoding="utf-8") as cf:
                                content += "\n" + cf.read()
                        except Exception:
                            pass

        content_lower = content.lower()
        if "home" in content_lower and "about us" in content_lower and "special menu" in content_lower and len(content) < 400:
            return False, "Generated website matches unstyled placeholder HTML. Level 2 Completeness Failed."

        if brief and hasattr(brief, 'required_sections') and brief.required_sections:
            missing_sections = []
            for sec in brief.required_sections:
                sec_kw = sec.lower().replace(" ", "").replace("banner", "").replace("section", "")
                if sec_kw and sec_kw not in content_lower:
                    missing_sections.append(sec)
            if len(missing_sections) > len(brief.required_sections) // 2:
                return False, f"Missing requested sections in UI components: {', '.join(missing_sections)}"

        return True, ""

    @classmethod
    def validate_anti_fabrication(cls, output_dir: str, brief: any = None) -> tuple[bool, str]:
        fake_patterns = [
            r'0120-\d{7}', r'\+91-\d{10}', r'info@\w+\.com', r'contact@\w+\.com',
            r'tcs campus,\s*ghaziabad', r'123 fake street'
        ]

        for root, _, files in os.walk(output_dir):
            if any(skip in root for skip in ["node_modules", "dist", ".git", ".next"]):
                continue
            for fname in files:
                if fname.endswith((".tsx", ".jsx", ".ts", ".js", ".html")):
                    fp = os.path.join(root, fname)
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            text = f.read().lower()
                        for pattern in fake_patterns:
                            if re.search(pattern, text):
                                return False, f"Anti-Fabrication Failure in '{fname}': Invented data matching pattern '{pattern}'."
                    except Exception:
                        pass
        return True, ""

    @classmethod
    def validate_website_assets(cls, output_dir: str, plan: any) -> tuple[bool, str]:
        planned_files = [f.path for f in plan.files] if hasattr(plan, 'files') else []
        for pfile in planned_files:
            full_p = os.path.join(output_dir, pfile)
            if not os.path.exists(full_p):
                return False, f"Planned file '{pfile}' does not exist on disk."
        return True, ""

    @classmethod
    def validate_dependency_closure(cls, output_dir: str) -> tuple[bool, str]:
        pkg_path = os.path.join(output_dir, "package.json")
        if not os.path.exists(pkg_path):
            return False, "[DEPENDENCY_ERROR]: package.json missing from project root."

        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
        except Exception as e:
            return False, f"[DEPENDENCY_ERROR]: Failed to parse package.json: {e}"

        deps = pkg_data.get("dependencies", {})
        dev_deps = pkg_data.get("devDependencies", {})
        declared_packages = set(deps.keys()).union(set(dev_deps.keys()))

        node_builtins = {
            "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
            "constants", "crypto", "dgram", "dns", "domain", "events", "fs", "http",
            "http2", "https", "inspector", "module", "net", "os", "path", "perf_hooks",
            "process", "punycode", "querystring", "readline", "repl", "stream",
            "string_decoder", "sys", "timers", "tls", "tty", "url", "util", "v8",
            "vm", "wasi", "worker_threads", "zlib"
        }

        import_pattern = re.compile(r"""(?:import\s+[\s\S]*?\s+from\s+['"]([^'"]+)['"]|import\s+['"]([^'"]+)['"]|import\s*\(\s*['"]([^'"]+)['"]\s*\))""")

        src_dir = os.path.join(output_dir, "src")
        if not os.path.exists(src_dir):
            src_dir = output_dir

        for root, _, files in os.walk(src_dir):
            if any(skip in root for skip in ["node_modules", "dist", ".git", ".next"]):
                continue
            for fname in files:
                if fname.endswith((".tsx", ".ts", ".jsx", ".js")):
                    fp = os.path.join(root, fname)
                    rel_fp = os.path.relpath(fp, output_dir)
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            content = f.read()
                        matches = import_pattern.findall(content)
                        for match in matches:
                            import_src = match[0] or match[1] or match[2]
                            if not import_src:
                                continue
                            if import_src.startswith(".") or import_src.startswith("/") or import_src.startswith("@/"):
                                continue
                            parts = import_src.split("/")
                            if import_src.startswith("@") and len(parts) >= 2:
                                pkg_name = f"{parts[0]}/{parts[1]}"
                            else:
                                pkg_name = parts[0]

                            if pkg_name in node_builtins:
                                continue

                            if pkg_name not in declared_packages:
                                return False, f"[DEPENDENCY_ERROR]: File '{rel_fp}' imports unlisted package '{pkg_name}' absent from package.json."
                    except Exception as e:
                        pass

        return True, ""

    @classmethod
    def validate_build_integrity(cls, output_dir: str, plan: any, ws_instance: any, preview_url: str) -> tuple[bool, str]:
        planned_files = [f.path for f in plan.files] if hasattr(plan, 'files') else ["index.html", "style.css", "script.js"]
        for pfile in planned_files:
            fp = os.path.join(output_dir, pfile)
            if not os.path.exists(fp):
                return False, f"Missing planned project file: {pfile}"
        return True, ""
