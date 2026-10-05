"""
vision/screen_capture.py
On-demand screen capture system for JARVIS Phase 4 Vision.
Supports full-screen capture, region-of-interest (ROI) capture, scaling, and integration with PrivacyFilter.
"""

import os
import time
import uuid
import logging
from typing import Optional, Tuple
from PIL import Image, ImageGrab

from vision.screen_frame import ScreenFrame
from vision.privacy_filter import PrivacyFilter

logger = logging.getLogger("ScreenCapture")


class ScreenCapture:
    def __init__(self, max_dimension: int = 1920):
        self.max_dimension = max_dimension
        self.temp_dir = PrivacyFilter.get_temp_dir()

    def capture_full_screen(self, display_id: int = 0) -> ScreenFrame:
        """
        Captures full primary screen on demand.
        Returns a ScreenFrame dataclass with image_path populated.
        """
        try:
            image = ImageGrab.grab(all_screens=False)
            return self._process_and_save(image, capture_source="full_screen", display_id=display_id)
        except Exception as e:
            logger.error(f"[ScreenCapture] Full screen capture error: {e}")
            return ScreenFrame(capture_source="full_screen", metadata={"error": str(e)})

    def capture_region(self, bbox: Tuple[int, int, int, int], display_id: int = 0) -> ScreenFrame:
        """
        Captures a region of interest defined by bbox (left, top, right, bottom).
        """
        try:
            image = ImageGrab.grab(bbox=bbox)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return self._process_and_save(
                image,
                capture_source="region",
                region=(bbox[0], bbox[1], width, height),
                display_id=display_id
            )
        except Exception as e:
            logger.error(f"[ScreenCapture] Region capture error: {e}")
            return ScreenFrame(capture_source="region", metadata={"error": str(e)})

    def capture_window_rect(self, rect: Tuple[int, int, int, int], display_id: int = 0) -> ScreenFrame:
        """
        Captures a window region defined by (left, top, right, bottom).
        """
        return self.capture_region(bbox=rect, display_id=display_id)

    def _process_and_save(
        self,
        image: Image.Image,
        capture_source: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        display_id: int = 0
    ) -> ScreenFrame:
        orig_w, orig_h = image.size

        # Downscale if larger than max_dimension while preserving aspect ratio
        if max(orig_w, orig_h) > self.max_dimension:
            scale = self.max_dimension / float(max(orig_w, orig_h))
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            new_w, new_h = orig_w, orig_h

        # Save to temp directory
        filename = f"capture_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(self.temp_dir, filename)
        image.save(filepath, format="PNG")

        frame = ScreenFrame(
            width=new_w,
            height=new_h,
            display_id=display_id,
            capture_source=capture_source,
            region=region,
            image_path=filepath,
            metadata={
                "original_width": orig_w,
                "original_height": orig_h,
                "captured_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        return frame
