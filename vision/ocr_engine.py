"""
vision/ocr_engine.py
Spatial text extraction and OCR engine for JARVIS Phase 4 Vision.
Extracts spatial text blocks with coordinate bounding boxes (x, y, w, h), code snippets, and terminal error traces.
Filters all extracted text using PrivacyFilter.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from vision.privacy_filter import PrivacyFilter

logger = logging.getLogger("OCREngine")

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False


@dataclass
class OCRTextBlock:
    text: str
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float = 1.0


@dataclass
class OCRResult:
    full_text: str
    blocks: List[OCRTextBlock] = field(default_factory=list)
    code_snippets: List[str] = field(default_factory=list)
    detected_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_text": self.full_text,
            "block_count": len(self.blocks),
            "code_snippets": self.code_snippets,
            "detected_errors": self.detected_errors
        }


class OCREngine:
    def __init__(self, use_easyocr: bool = False):
        self.privacy_filter = PrivacyFilter.get_instance()
        self.easyocr_reader = None
        if use_easyocr and HAS_EASYOCR:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
            except Exception as e:
                logger.warning(f"[OCREngine] EasyOCR init failed: {e}")

    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extracts spatial text blocks from the image at image_path.
        Applies PrivacyFilter to mask any sensitive credentials or keys.
        """
        if not image_path:
            return OCRResult(full_text="")

        blocks: List[OCRTextBlock] = []
        raw_text = ""

        # Attempt Pytesseract
        if HAS_PYTESSERACT:
            try:
                img = Image.open(image_path)
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                raw_text = pytesseract.image_to_string(img)
                n_boxes = len(data.get("text", []))
                for i in range(n_boxes):
                    txt = data["text"][i].strip()
                    if txt:
                        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                        conf = float(data["conf"][i]) if "conf" in data and data["conf"][i] != "-1" else 0.8
                        blocks.append(OCRTextBlock(text=self.privacy_filter.filter_text(txt), bbox=(x, y, w, h), confidence=conf))
            except Exception as e:
                logger.debug(f"[OCREngine] Pytesseract execution failed: {e}")

        # Attempt EasyOCR if pytesseract produced no text
        if not raw_text.strip() and self.easyocr_reader:
            try:
                results = self.easyocr_reader.readtext(image_path)
                text_parts = []
                for (bbox_pts, txt, conf) in results:
                    txt_clean = self.privacy_filter.filter_text(txt.strip())
                    if txt_clean:
                        text_parts.append(txt_clean)
                        # bbox_pts is [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
                        x1 = int(bbox_pts[0][0])
                        y1 = int(bbox_pts[0][1])
                        w = int(bbox_pts[1][0] - x1)
                        h = int(bbox_pts[2][1] - y1)
                        blocks.append(OCRTextBlock(text=txt_clean, bbox=(x1, y1, max(1, w), max(1, h)), confidence=float(conf)))
                raw_text = "\n".join(text_parts)
            except Exception as e:
                logger.debug(f"[OCREngine] EasyOCR execution failed: {e}")

        clean_full_text = self.privacy_filter.filter_text(raw_text)

        # Detect code snippets & error logs from text
        code_snippets = self._extract_code_snippets(clean_full_text)
        detected_errors = self._extract_detected_errors(clean_full_text)

        return OCRResult(
            full_text=clean_full_text,
            blocks=blocks,
            code_snippets=code_snippets,
            detected_errors=detected_errors
        )

    def _extract_code_snippets(self, text: str) -> List[str]:
        """Extracts potential code snippets from screen text."""
        snippets = []
        lines = text.split("\n")
        code_buffer = []
        code_keywords = {"def ", "class ", "import ", "return ", "function", "const ", "let ", "var ", "void ", "async ", "if (", "for ("}

        for line in lines:
            if any(kw in line for kw in code_keywords) or re.search(r'[{}();=><]', line):
                code_buffer.append(line)
            else:
                if len(code_buffer) >= 2:
                    snippets.append("\n".join(code_buffer))
                code_buffer = []
        if len(code_buffer) >= 2:
            snippets.append("\n".join(code_buffer))
        return snippets

    def _extract_detected_errors(self, text: str) -> List[str]:
        """Extracts stack traces, compile errors, or terminal error logs."""
        errors = []
        error_keywords = [
            "traceback (most recent call last)",
            "syntaxerror:",
            "typeerror:",
            "valueerror:",
            "nameerror:",
            "attributeerror:",
            "importerror:",
            "exception",
            "failed to compile",
            "error:",
            "uncaught error",
            "fatal error",
            "build failed"
        ]

        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in error_keywords):
                # Grab surrounding lines context
                start = max(0, i - 2)
                end = min(len(lines), i + 4)
                errors.append("\n".join(lines[start:end]))

        return errors
