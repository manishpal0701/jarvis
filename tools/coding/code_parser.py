import re

class CodeParser:
    """
    Parses LLM responses (both streaming chunks and full strings) to extract clean,
    sanitized source code without markdown fences, preambles, or post-explanations.
    """
    
    LANG_MAP = {
        "py": "python",
        "python": "python",
        "js": "javascript",
        "javascript": "javascript",
        "ts": "typescript",
        "typescript": "typescript",
        "jsx": "react",
        "tsx": "react",
        "html": "html",
        "css": "css",
        "dart": "dart",
        "flutter": "dart",
        "json": "json",
        "cpp": "cpp",
        "c++": "cpp",
        "java": "java",
        "sql": "sql",
        "sh": "bash",
        "bash": "bash"
    }

    @classmethod
    def detect_language(cls, text: str, default_ext: str = ".py") -> str:
        """Detects programming language from text markers or file extension."""
        if default_ext.startswith("."):
            ext = default_ext[1:].lower()
            if ext in cls.LANG_MAP:
                return cls.LANG_MAP[ext]

        text_lower = text.lower()
        if "react" in text_lower or "jsx" in text_lower or "useState" in text_lower:
            return "react"
        if "flutter" in text_lower or "import 'package:flutter" in text_lower or "widget" in text_lower:
            return "dart"
        if "def " in text or "import os" in text or "print(" in text:
            return "python"
        if "<!doctype html>" in text_lower or "<html>" in text_lower:
            return "html"
        if "const " in text or "function " in text or "console.log" in text:
            return "javascript"

        return "python"

    @classmethod
    def extract_code(cls, full_text: str) -> str:
        """
        Extracts pure source code from raw LLM text.
        Removes markdown code fences (```lang ... ```), preambles, and post-explanations.
        """
        if not full_text:
            return ""

        # Search for ```lang ... ``` pattern
        code_blocks = re.findall(r"```(?:[a-zA-Z0-9_+#-]+)?\n(.*?)```", full_text, re.DOTALL)
        unclosed_match = re.search(r"```(?:[a-zA-Z0-9_+#-]+)?\n(.*)", full_text, re.DOTALL)

        lines = full_text.splitlines()
        code_lines = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                code_lines.append(line)

        # Determine raw extracted code string
        if code_blocks:
            res_code = max(code_blocks, key=len).strip()
        elif unclosed_match:
            candidate = unclosed_match.group(1).strip()
            res_code = re.sub(r"```$", "", candidate).strip()
        elif code_lines:
            res_code = "\n".join(code_lines).strip()
        else:
            res_code = full_text.strip()

        # Sanitize Next.js framework imports (e.g. import ... from 'next/image') if present in React Vite code
        if "from 'next" in res_code or 'from "next' in res_code:
            res_code = re.sub(r"""import\s+[\s\S]*?\s+from\s+['"]next(?:/[^'"]*)?['"];?\n?""", "", res_code)
            res_code = re.sub(r"<Image\s+([^>]*)\/>", r"<img \1 />", res_code)
            res_code = re.sub(r"<Image\s+([^>]*)>", r"<img \1>", res_code)
            res_code = re.sub(r"<\/Image>", r"</img>", res_code)
            res_code = re.sub(r"<Link\s+href=", r"<a href=", res_code)
            res_code = re.sub(r"<\/Link>", r"</a>", res_code)

        return res_code


class StreamCodeExtractor:
    """
    Incremental state-machine stream parser for real-time LLM token streams.
    Ensures that only clean code is streamed to the UI, suppressing markdown fences and preambles.
    """

    def __init__(self):
        self.buffer = ""
        self.extracted_code = ""
        self.in_code_block = False
        self.code_started = False
        self.detected_lang = ""

    def process_chunk(self, chunk: str) -> str:
        """
        Processes an incoming streaming chunk.
        Returns newly extracted clean code snippet (if any).
        """
        self.buffer += chunk
        
        if not self.in_code_block:
            # Look for starting fence ```
            match = re.search(r"```([a-zA-Z0-9_+#-]*)\n", self.buffer)
            if match:
                self.in_code_block = True
                self.code_started = True
                self.detected_lang = match.group(1).strip()
                # Remove everything before the fence
                code_after_fence = self.buffer[match.end():]
                self.buffer = ""
                # Check if there is an ending fence already in chunk
                if "```" in code_after_fence:
                    code_content = code_after_fence.split("```")[0]
                    self.extracted_code += code_content
                    self.in_code_block = False
                    return code_content
                else:
                    self.extracted_code += code_after_fence
                    return code_after_fence
            else:
                # If buffer is long without fence, assume raw code stream
                if len(self.buffer) > 150 and "def " in self.buffer or "import " in self.buffer or "function " in self.buffer or "const " in self.buffer:
                    self.in_code_block = True
                    self.code_started = True
                    code_to_return = self.buffer
                    self.extracted_code += code_to_return
                    self.buffer = ""
                    return code_to_return
                return ""
        else:
            # We are inside code block
            if "```" in chunk:
                parts = chunk.split("```")
                code_part = parts[0]
                self.in_code_block = False
                self.extracted_code += code_part
                return code_part
            else:
                self.extracted_code += chunk
                return chunk

    def get_final_clean_code(self) -> str:
        """Returns the full clean code extracted across the stream."""
        if self.extracted_code.strip():
            # Clean any trailing closing ``` or whitespace
            clean = re.sub(r"```$", "", self.extracted_code).strip()
            return clean
        return CodeParser.extract_code(self.buffer)
