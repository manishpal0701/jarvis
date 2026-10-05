import unittest
from speech.response_formatter import ResponseFormatter

class TestTTSSanitizer(unittest.TestCase):
    def test_decorative_lines_removal(self):
        """Verify decorative symbol lines (===, ---, ___, ***) are completely removed."""
        raw_text = (
            "========================\n"
            "Boss, your application is ready.\n"
            "========================"
        )
        cleaned = ResponseFormatter.format_for_speech(raw_text)
        self.assertEqual(cleaned, "Boss, your application is ready.")
        self.assertNotIn("equals", cleaned)

    def test_markdown_headers_and_separators(self):
        """Verify markdown headers (###) and horizontal separators (---) are sanitized."""
        raw_text = (
            "---\n"
            "### App Status\n"
            "***\n"
            "Boss, the application is ready.\n"
            "___"
        )
        cleaned = ResponseFormatter.format_for_speech(raw_text)
        self.assertNotIn("dash", cleaned)
        self.assertNotIn("hash", cleaned)
        self.assertNotIn("asterisk", cleaned)
        self.assertNotIn("underscore", cleaned)
        self.assertIn("App Status", cleaned)
        self.assertIn("Boss, the application is ready.", cleaned)

    def test_meaningful_math_and_hyphenated_terms(self):
        """Verify equations (2 + 2 = 4) and hyphenated words (hello-world) remain intact."""
        math_text = "2 + 2 = 4"
        cleaned_math = ResponseFormatter.format_for_speech(math_text)
        self.assertIn("2 plus 2 equals 4", cleaned_math)

        hyphen_text = "hello-world"
        cleaned_hyphen = ResponseFormatter.format_for_speech(hyphen_text)
        self.assertIn("hello-world", cleaned_hyphen)
        self.assertNotIn("dash", cleaned_hyphen)

    def test_code_blocks_sanitization(self):
        """Verify code blocks and code fences do not produce spoken backticks."""
        raw_code = (
            "```python\n"
            "print('Hello World')\n"
            "```"
        )
        cleaned = ResponseFormatter.format_for_speech(raw_code)
        self.assertNotIn("backtick", cleaned)
        self.assertNotIn("```", cleaned)
        self.assertIn("Code snippet generated.", cleaned)

if __name__ == "__main__":
    unittest.main()
