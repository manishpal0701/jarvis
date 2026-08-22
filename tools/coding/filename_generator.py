import re
from typing import Optional

class FilenameGenerator:
    """
    Generic, scalable filename generator.
    Converts user prompts into clean, snake_case filenames based on generic NLP slugifying.
    Pipeline: User Prompt -> Extract Primary Subject -> Normalize -> Slugify -> snake_case -> Extension.
    Does NOT use hardcoded keyword mapping dictionaries.
    Does NOT decide project task type (TaskClassifier handles intent classification).
    """

    # Common stop/action filler words to remove during subject extraction
    ACTION_STOP_WORDS = {
        "create", "build", "make", "generate", "write", "develop", "code", "design", "construct",
        "bana", "banao", "banaa", "kar", "karo", "karke", "ke", "do", "please", "ek", "naya", "new", "simple",
        "in", "using", "with", "for", "a", "an", "the", "and", "of", "to", "my", "our", "your",
        "python", "javascript", "js", "cpp", "c++", "java", "html", "css", "script", "program", "code"
    }

    ACTION_PHRASES = [
        "in python", "using python", "with python", "in javascript", "using javascript", "with javascript",
        "create a", "create an", "build a", "build an", "make a", "make an", "generate a", "generate an",
        "write a", "write an", "develop a", "develop an", "code a", "code an",
        "banaa kar", "bana kar", "banaa do", "bana do", "bana ke", "banaa ke", "banao", "bana", "karo", "karke",
        "script for", "program for", "app for", "code for", "system for", "software for"
    ]

    @classmethod
    def generate_filename(cls, task_prompt: str, language: str = "python") -> str:
        """
        Generates a clean snake_case filename from a task prompt.
        """
        if not task_prompt or not task_prompt.strip():
            ext = cls._get_extension(language)
            return f"generated_program{ext}"

        raw_cmd = task_prompt.strip()

        # 1. Check if an explicit filename with extension is provided in prompt (e.g. "write helper.py", "create main.py")
        match = re.search(r'\b([a-zA-Z0-9_\-]+\.(py|js|css|cpp|java|html|json|ts|tsx))\b', raw_cmd, re.IGNORECASE)
        if match:
            return match.group(1)

        # 2. Map extension
        ext = cls._get_extension(language)

        # 3. Normalize & Strip Action Phrases
        normalized = raw_cmd.lower()
        for phrase in cls.ACTION_PHRASES:
            normalized = normalized.replace(phrase, " ")

        # 4. Tokenize & Remove Action Stop Words
        raw_tokens = re.split(r'[^a-zA-Z0-9]+', normalized)
        subject_tokens = [w for w in raw_tokens if w and w not in cls.ACTION_STOP_WORDS]

        # 5. Handle fallback or slugify to snake_case
        if not subject_tokens:
            return f"generated_program{ext}"

        slug = "_".join(subject_tokens)

        # 6. Guard against returning 'main' unless explicitly requested
        if slug == "main" and "main" not in raw_cmd.lower():
            return f"generated_program{ext}"

        return f"{slug}{ext}"

    @staticmethod
    def _get_extension(language: str) -> str:
        lang = (language or "").lower().strip()
        if lang in ["javascript", "js"]:
            return ".js"
        elif lang in ["css", "style"]:
            return ".css"
        elif lang in ["html", "web"]:
            return ".html"
        elif lang in ["cpp", "c++"]:
            return ".cpp"
        elif lang in ["java"]:
            return ".java"
        elif lang in ["json"]:
            return ".json"
        elif lang in ["typescript", "ts"]:
            return ".ts"
        elif lang in ["tsx"]:
            return ".tsx"
        return ".py"
