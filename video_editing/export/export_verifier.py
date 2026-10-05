"""
video_editing/export/export_verifier.py
ffprobe Output File Verifier for Phase 4 Render Pipeline.
Independently verifies that the exported video file exists, is non-zero, readable,
has valid video/audio streams, non-zero duration, and matching resolution.
"""

import os
import json
import subprocess
import cv2
from video_editing.utils.ffprobe_finder import run_ffprobe as _ffprobe_runner


def verify_output_file(output_path: str, expected_config: dict = None) -> dict:
    """
    Independently inspects and verifies the rendered video file.
    Returns structured verification result dict.
    """
    if not output_path or not isinstance(output_path, str):
        return _err("INVALID_PATH", "output_path must be a non-empty string.")

    norm_path = os.path.normpath(output_path)

    # 1. Check file existence
    if not os.path.isfile(norm_path):
        return _err("OUTPUT_NOT_FOUND", f"Export output file does not exist: '{norm_path}'.")

    # 2. Check file size > 0
    try:
        file_size = os.path.getsize(norm_path)
        if file_size <= 0:
            return _err("ZERO_BYTE_OUTPUT", f"Export output file is 0 bytes: '{norm_path}'.")
    except Exception as exc:
        return _err("FILE_ACCESS_ERROR", f"Could not read output file size: {exc}")

    # 3. Check file readability
    try:
        with open(norm_path, "rb") as f:
            header = f.read(16)
            if not header:
                return _err("UNREADABLE_FILE", f"Could not read header from file: '{norm_path}'.")
    except Exception as exc:
        return _err("UNREADABLE_FILE", f"Could not open file for reading: {exc}")

    # 4. ffprobe & OpenCV stream analysis
    try:
        ff_meta = _ffprobe_runner(norm_path)
    except Exception as exc:
        return _err("FFPROBE_ERROR", f"ffprobe verification failed: {exc}")
    cv_meta = _run_opencv(norm_path)
    cv_meta = _run_opencv(norm_path)

    duration = ff_meta.get("duration") or cv_meta.get("duration") or 0.0
    width = ff_meta.get("width") or cv_meta.get("width") or 0
    height = ff_meta.get("height") or cv_meta.get("height") or 0
    has_video = ff_meta.get("has_video") or (width > 0 and height > 0)
    has_audio = ff_meta.get("has_audio", False)
    v_codec = ff_meta.get("video_codec", "UNKNOWN")

    # 5. Check duration > 0
    if duration <= 0:
        return _err("INVALID_DURATION", f"Export output file duration is zero or negative: {duration}s.")

    # 6. Check video stream presence
    if not has_video:
        return _err("MISSING_VIDEO_STREAM", "Export output file contains no valid video stream.")

    # 7. Check expected resolution matching if config provided
    if expected_config and "resolution" in expected_config:
        exp_res = expected_config["resolution"]
        actual_res = f"{width}x{height}"
        if exp_res and actual_res != "0x0" and exp_res != actual_res:
            return _err("RESOLUTION_MISMATCH", f"Output resolution '{actual_res}' does not match expected '{exp_res}'.")

    # 8. Check audio stream if audio_enabled is True in config
    if expected_config and expected_config.get("audio_enabled") is True:
        if not has_audio:
            return _err("MISSING_AUDIO_STREAM", "Export output file is missing required audio stream.")

    return {
        "success": True,
        "verified": True,
        "path": norm_path,
        "file_size_bytes": file_size,
        "duration": round(float(duration), 2),
        "video": {
            "width": int(width),
            "height": int(height),
            "resolution": f"{width}x{height}",
            "codec": str(v_codec)
        },
        "audio": bool(has_audio),
        "error": None
    }


def _run_ffprobe(file_path: str) -> dict:
    try:
        return _ffprobe_runner(file_path)
    except Exception:
        return {}


def _run_opencv(file_path: str) -> dict:
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return {}
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        dur = fc / fps if fps > 0 else 0.0
        cap.release()
        return {
            "width": w,
            "height": h,
            "duration": dur,
            "has_video": (w > 0 and h > 0)
        }
    except Exception:
        return {}


def _err(code: str, message: str) -> dict:
    return {
        "success": False,
        "verified": False,
        "error": {
            "code": code,
            "message": message
        }
    }
