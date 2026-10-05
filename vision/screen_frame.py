"""
vision/screen_frame.py
Structured ScreenFrame data model for JARVIS Phase 4 Screen Understanding.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

@dataclass
class ScreenFrame:
    frame_id: str = field(default_factory=lambda: f"frame_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    width: int = 1920
    height: int = 1080
    display_id: int = 0
    capture_source: str = "full_screen"  # full_screen, active_window, region
    region: Optional[Tuple[int, int, int, int]] = None  # (left, top, width, height)
    image_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "width": self.width,
            "height": self.height,
            "display_id": self.display_id,
            "capture_source": self.capture_source,
            "region": self.region,
            "image_path": self.image_path,
            "metadata": self.metadata
        }
