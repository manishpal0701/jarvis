import os
import json
import glob
from dataclasses import dataclass, field

@dataclass
class ProjectPatternSpec:
    framework: str = "react"
    language: str = "typescript"
    styling: str = "tailwind"
    state_management: str = "none"
    routing: str = "none"
    build_tool: str = "vite"
    existing_dependencies: list = field(default_factory=list)
    reusable_components: list = field(default_factory=list)
    display_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "language": self.language,
            "styling": self.styling,
            "state_management": self.state_management,
            "routing": self.routing,
            "build_tool": self.build_tool,
            "existing_dependencies": self.existing_dependencies,
            "reusable_components": self.reusable_components,
            "display_summary": self.display_summary
        }

class ExistingProjectAnalyzer:
    """
    Analyzes an existing codebase before generating modification code.
    Detects framework, language (TS/JS), state management (Redux, Zustand, Context API),
    styling system (Tailwind, CSS Modules, styled-components, plain CSS), and routing.
    Enforces pattern consistency so generated code matches the target project.
    """

    @classmethod
    def analyze_project(cls, project_dir: str) -> ProjectPatternSpec:
        if not project_dir or not os.path.exists(project_dir):
            return ProjectPatternSpec()

        spec = ProjectPatternSpec()
        pkg_path = os.path.join(project_dir, "package.json")
        all_deps = {}

        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
                    deps = pkg_data.get("dependencies", {})
                    dev_deps = pkg_data.get("devDependencies", {})
                    all_deps = {**deps, **dev_deps}
                    spec.existing_dependencies = list(all_deps.keys())
            except Exception as e:
                print(f"[ExistingProjectAnalyzer Warning]: Failed to parse package.json: {e}")

        # 1. Detect Framework
        if "next" in all_deps:
            spec.framework = "nextjs"
            spec.build_tool = "next"
        elif "vue" in all_deps:
            spec.framework = "vue"
            spec.build_tool = "vite" if "vite" in all_deps else "vue-cli"
        elif "react" in all_deps:
            spec.framework = "react"
            spec.build_tool = "vite" if "vite" in all_deps else "webpack"
        elif os.path.exists(os.path.join(project_dir, "pom.xml")):
            spec.framework = "spring_boot"
            spec.language = "java"
            spec.build_tool = "maven"
            spec.display_summary = "Java + Spring Boot Project"
            return spec

        # 2. Detect Language (TypeScript vs JavaScript)
        has_ts = os.path.exists(os.path.join(project_dir, "tsconfig.json")) or "typescript" in all_deps
        if not has_ts:
            ts_files = glob.glob(os.path.join(project_dir, "**/*.ts"), recursive=True) + glob.glob(os.path.join(project_dir, "**/*.tsx"), recursive=True)
            has_ts = len(ts_files) > 0

        spec.language = "typescript" if has_ts else "javascript"

        # 3. Detect State Management
        if "redux" in all_deps or "@reduxjs/toolkit" in all_deps or "react-redux" in all_deps:
            spec.state_management = "redux"
        elif "zustand" in all_deps:
            spec.state_management = "zustand"
        elif "recoil" in all_deps:
            spec.state_management = "recoil"
        elif "mobx" in all_deps:
            spec.state_management = "mobx"
        else:
            context_files = glob.glob(os.path.join(project_dir, "**/Context.*"), recursive=True) + glob.glob(os.path.join(project_dir, "**/*context*.*"), recursive=True)
            if context_files:
                spec.state_management = "context"
            else:
                spec.state_management = "none"

        # 4. Detect Styling System
        if "tailwindcss" in all_deps or os.path.exists(os.path.join(project_dir, "tailwind.config.js")) or os.path.exists(os.path.join(project_dir, "tailwind.config.ts")):
            spec.styling = "tailwind"
        elif "styled-components" in all_deps or "@emotion/react" in all_deps:
            spec.styling = "styled_components"
        else:
            module_css = glob.glob(os.path.join(project_dir, "**/*.module.css"), recursive=True)
            if module_css:
                spec.styling = "css_modules"
            else:
                spec.styling = "plain_css"

        # 5. Detect Routing
        if "react-router-dom" in all_deps or "react-router" in all_deps:
            spec.routing = "react_router"
        elif spec.framework == "nextjs":
            spec.routing = "next_router"
        else:
            spec.routing = "none"

        # 6. Discover Reusable Component names
        comp_dir = os.path.join(project_dir, "src", "components")
        if os.path.exists(comp_dir):
            for root, _, files in os.walk(comp_dir):
                for file in files:
                    if file.endswith((".tsx", ".jsx", ".js", ".ts")):
                        base = os.path.splitext(file)[0]
                        if base not in spec.reusable_components and base != "index":
                            spec.reusable_components.append(base)

        spec.display_summary = (
            f"Framework: {spec.framework.upper()} ({spec.language.upper()}), "
            f"Styling: {spec.styling.upper()}, State: {spec.state_management.upper()}, "
            f"Build: {spec.build_tool.upper()}"
        )
        return spec
