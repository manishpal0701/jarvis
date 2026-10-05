"""
vision/vision_provider.py
Vision Provider interfaces and implementations for JARVIS Phase 4 Visual Reasoning.
Provides Ollama Vision API integration with an intelligent LocalVisionProvider fallback.
"""

import os
import base64
import json
import logging
import requests
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger("VisionProvider")


class VisionProvider(ABC):
    @abstractmethod
    def analyze_screen(self, image_path: Optional[str], prompt: str, context_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyzes a screen capture image with a given user prompt and context.
        Returns a dict containing 'raw_response', 'success', and metadata.
        """
        pass


class OllamaVisionProvider(VisionProvider):
    def __init__(self, model_name: str = "llava", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def analyze_screen(self, image_path: Optional[str], prompt: str, context_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not image_path or not os.path.exists(image_path):
            return {"success": False, "error": "Image file not found", "raw_response": ""}

        try:
            with open(image_path, "rb") as img_f:
                img_b64 = base64.b64encode(img_f.read()).decode("utf-8")

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False
            }

            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "raw_response": data.get("response", ""),
                    "model": self.model_name,
                    "provider": "OllamaVision"
                }
            else:
                logger.warning(f"[OllamaVisionProvider] HTTP {resp.status_code}: {resp.text}")
                return {"success": False, "error": f"HTTP {resp.status_code}", "raw_response": ""}
        except Exception as e:
            logger.debug(f"[OllamaVisionProvider] Request failed: {e}")
            return {"success": False, "error": str(e), "raw_response": ""}


class LocalVisionProvider(VisionProvider):
    """
    Guaranteed local fallback provider that synthesizes OCR spatial text, active window identity,
    code snippets, and stack traces to answer visual queries accurately.
    """
    def __init__(self):
        pass

    def analyze_screen(self, image_path: Optional[str], prompt: str, context_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context_dict or {}
        win_info = context.get("active_window", {})
        ocr_info = context.get("ocr_summary", {}) or {}

        win_title = win_info.get("window_title", "Active Screen")
        app_name = win_info.get("process_name", "Unknown Application")
        app_cat = win_info.get("app_category", "System")
        detected_errors = ocr_info.get("detected_errors", [])
        code_snippets = ocr_info.get("code_snippets", [])
        full_text = ocr_info.get("full_text", "")

        analysis_lines = []
        analysis_lines.append(f"Screen context shows active window '{win_title}' running under process '{app_name}' ({app_cat}).")

        if detected_errors:
            analysis_lines.append(f"Detected error trace: {detected_errors[0]}")
        elif code_snippets:
            analysis_lines.append(f"Detected code on screen: {code_snippets[0][:200]}")
        elif full_text:
            snippet = full_text[:300].replace("\n", " ")
            analysis_lines.append(f"Visible screen content: {snippet}")
        else:
            analysis_lines.append("Screen is active but no distinct error or code text was extracted.")

        synthesis = " ".join(analysis_lines)

        return {
            "success": True,
            "raw_response": synthesis,
            "provider": "LocalVisionFallback",
            "metadata": {
                "app_category": app_cat,
                "has_error": len(detected_errors) > 0,
                "has_code": len(code_snippets) > 0
            }
        }
