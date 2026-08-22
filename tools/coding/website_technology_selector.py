from dataclasses import dataclass
import re

@dataclass
class TechnologyStackSpec:
    framework: str
    language: str
    styling: str
    runtime: str
    build_system: str
    default_stack: bool = False
    display_name: str = ""

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "language": self.language,
            "styling": self.styling,
            "runtime": self.runtime,
            "build_system": self.build_system,
            "default_stack": self.default_stack,
            "display_name": self.display_name
        }

class WebsiteTechnologySelector:
    """
    Selection layer for website technology stacks.
    Defaults to React + TypeScript + Tailwind CSS + Vite whenever no explicit technology is specified.
    Respects explicit user choices (Next.js, React+TS/JS, Vue, Vanilla HTML/CSS/JS, Java/Spring Boot).
    """

    @classmethod
    def detect_stack(cls, command: str, brief: any = None) -> TechnologyStackSpec:
        cmd = command.lower().strip()

        # 1. Check for Java / Spring Boot
        if any(k in cmd for k in ["java", "spring boot", "springboot", "spring"]):
            return TechnologyStackSpec(
                framework="spring_boot",
                language="java",
                styling="css",
                runtime="jvm",
                build_system="maven",
                default_stack=False,
                display_name="Java + Spring Boot + Thymeleaf"
            )

        # 2. Check for Explicit Next.js
        if "next" in cmd or "nextjs" in cmd or "next.js" in cmd:
            return TechnologyStackSpec(
                framework="nextjs",
                language="typescript",
                styling="tailwind",
                runtime="node",
                build_system="next",
                default_stack=False,
                display_name="Next.js + TypeScript + Tailwind CSS"
            )

        # 3. Check for Vue
        if "vue" in cmd:
            return TechnologyStackSpec(
                framework="vue",
                language="typescript" if ("typescript" in cmd or "ts" in cmd) else "javascript",
                styling="css",
                runtime="node",
                build_system="vite",
                default_stack=False,
                display_name="Vue.js"
            )

        # 4. Check for Explicit Vanilla HTML/CSS/JS
        vanilla_keywords = [
            "html css js", "vanilla", "simple html", "only html", "html css javascript",
            "html/css/js", "plain html", "static html"
        ]
        if any(k in cmd for k in vanilla_keywords):
            return TechnologyStackSpec(
                framework="vanilla",
                language="html_css_js",
                styling="css",
                runtime="browser",
                build_system=None,
                default_stack=False,
                display_name="Vanilla HTML / CSS / JavaScript"
            )

        # 5. Check for Explicit React with custom language/styling (e.g., "React JavaScript", "React plain CSS")
        if "react" in cmd and ("javascript" in cmd or "js" in cmd) and "typescript" not in cmd and "ts" not in cmd:
            return TechnologyStackSpec(
                framework="react",
                language="javascript",
                styling="tailwind" if "tailwind" in cmd else "css",
                runtime="node",
                build_system="vite",
                default_stack=False,
                display_name="React + JavaScript"
            )

        # 6. DEFAULT STACK: React + TypeScript + Tailwind CSS + Vite
        return TechnologyStackSpec(
            framework="react",
            language="typescript",
            styling="tailwind",
            runtime="node",
            build_system="vite",
            default_stack=True,
            display_name="React + TypeScript + Tailwind CSS + Vite"
        )
