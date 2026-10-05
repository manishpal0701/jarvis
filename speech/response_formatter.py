import re

class ResponseFormatter:
    @staticmethod
    def format_for_speech(text: str) -> str:
        """
        Converts technical/console/markdown text into natural conversational spoken text.
        Strips decorative formatting (lines of =====, -----, _____, *****, ###, etc.)
        while preserving meaningful symbols, equations (2 + 2 = 4), and terms (hello-world).
        """
        if not text:
            return ""

        # 1. Pre-process code blocks & code fences
        # Replace complete ```...``` code blocks with clean summary
        spoken_text = re.sub(r'```[\s\S]*?```', ' Code snippet generated. ', text)
        # Remove any leftover standalone code fence lines like ```python or ```
        spoken_text = re.sub(r'^\s*```[a-zA-Z0-9_-]*\s*$', '', spoken_text, flags=re.MULTILINE)
        # Remove inline backticks `...`
        spoken_text = re.sub(r'`([^`]+)`', r'\1', spoken_text)
        spoken_text = spoken_text.replace('`', '')

        # 2. Filter out decorative divider lines & standalone symbol lines
        clean_lines = []
        for line in spoken_text.split('\n'):
            line_str = line.strip()
            if not line_str:
                continue
            # Check if line is purely decorative formatting (symbols only, no alphanumeric characters)
            if not re.search(r'[a-zA-Z0-9]', line_str):
                continue
            
            # Remove leading markdown header markers (e.g. ### Header -> Header)
            line_str = re.sub(r'^\s*#{1,6}\s+', '', line_str)
            # Remove standalone leading bullet/list markers
            line_str = re.sub(r'^\s*[\-\*\+]\s+', '', line_str)
            line_str = re.sub(r'^\s*\d+\.\s+', '', line_str)
            # Remove blockquote markers
            line_str = re.sub(r'^\s*>\s*', '', line_str)

            line_str = line_str.strip()
            if line_str and re.search(r'[a-zA-Z0-9]', line_str):
                clean_lines.append(line_str)

        if not clean_lines:
            return ""

        # Join clean lines into a single coherent text stream with natural sentence boundary punctuation
        formatted_paragraphs = []
        for line in clean_lines:
            if line[-1] not in '.!?:;,':
                formatted_paragraphs.append(line + '.')
            else:
                formatted_paragraphs.append(line)
        spoken_text = " ".join(formatted_paragraphs)

        # 3. Clean markdown formatting marks within text
        # Remove bold/italics/strikethrough (*, **, _, __, ~~)
        spoken_text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', spoken_text)
        spoken_text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', spoken_text)
        spoken_text = re.sub(r'~{1,2}([^~]+)~{1,2}', r'\1', spoken_text)
        # Remove URLs
        spoken_text = re.sub(r'https?://\S+', 'the link', spoken_text)

        # 4. Collapse multi-character symbol repetitions inside non-decorative text
        # e.g. "foo === bar" -> "foo bar", "status -- ok" -> "status ok"
        spoken_text = re.sub(r'={2,}', ' ', spoken_text)
        spoken_text = re.sub(r'-{2,}', ' ', spoken_text)
        spoken_text = re.sub(r'_{2,}', ' ', spoken_text)
        spoken_text = re.sub(r'\*{2,}', ' ', spoken_text)
        spoken_text = re.sub(r'#{2,}', ' ', spoken_text)
        spoken_text = re.sub(r'~{2,}', ' ', spoken_text)

        # 5. Meaningful symbol & abbreviation replacements
        replacements = {
            "%": " percent",
            "$": " dollars",
            "&": " and",
            "@": " at",
            "=": " equals ",
            "+": " plus ",
            "approx.": "approximately",
            "approx": "approximately",
            "vs": "versus",
            "min": "minutes",
            "sec": "seconds",
            "hr": "hours",
            "temp": "temperature",
            "vol": "volume",
            "qty": "quantity",
            "info": "information",
            "config": "configuration",
            "err": "error",
            "msg": "message",
        }

        for sym, word in replacements.items():
            if sym.isalpha():
                spoken_text = re.sub(rf'\b{sym}\b', word, spoken_text, flags=re.IGNORECASE)
            else:
                spoken_text = spoken_text.replace(sym, word)

        # 6. Final cleanup of emojis, whitespace and orphan symbols
        try:
            from conversation.intelligence.response_validator import ResponseValidator
            spoken_text = ResponseValidator().strip_emojis_for_tts(spoken_text)
        except Exception:
            spoken_text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27BF\u2300-\u23FF\u2B00-\u2BFF\u200D\uFE0F\uFE0E]', '', spoken_text)

        spoken_text = re.sub(r'[\*\#`_~]', '', spoken_text)
        spoken_text = re.sub(r'\s+', ' ', spoken_text).strip()

        return spoken_text

