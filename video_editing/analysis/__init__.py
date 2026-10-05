"""
video_editing/analysis package
Media Analysis Engine for Jarvis AI Video Editor
"""
from video_editing.analysis.media_analyzer import (
    analyze_media,
    extract_representative_frames,
    detect_scenes
)

__all__ = [
    "analyze_media",
    "extract_representative_frames",
    "detect_scenes"
]
