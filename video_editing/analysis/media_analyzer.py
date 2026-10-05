"""
video_editing/analysis/media_analyzer.py
Real Media Analysis Engine using OpenCV and ffprobe.
Extracts duration, resolution, FPS, frame counts, codec details, representative frames,
and deterministic scene candidates.
"""

import os
import cv2
import json
import subprocess
import tempfile
import numpy as np


from video_editing.analysis.audio_analyzer import analyze_audio

_MEDIA_CACHE = {}


def clear_media_cache():
    _MEDIA_CACHE.clear()


def analyze_media(file_path: str) -> dict:
    """
    Extract real media metadata using ffprobe, OpenCV fallback, and audio_analyzer.
    Caches result per absolute file_path to eliminate redundant analysis overhead.
    """
    if not file_path or not os.path.isfile(file_path):
        return {
            "status": "NOT_FOUND",
            "file_path": file_path,
            "duration": 0.0,
            "width": 0,
            "height": 0,
            "resolution": "UNKNOWN",
            "fps": 0.0,
            "frame_count": 0,
            "video_codec": "UNKNOWN",
            "audio_presence": False,
            "audio_duration": "NOT_AVAILABLE",
            "audio_analysis": analyze_audio(file_path)
        }

    abs_path = os.path.abspath(file_path)
    mtime = os.path.getmtime(abs_path)
    cache_key = (abs_path, mtime)
    if cache_key in _MEDIA_CACHE:
        return _MEDIA_CACHE[cache_key]

    ffprobe_meta = _run_ffprobe(abs_path)
    cv_meta = _run_opencv_meta(abs_path)
    audio_meta = analyze_audio(abs_path)

    # Combine metadata streams
    duration = ffprobe_meta.get("duration") or cv_meta.get("duration") or 0.0
    width = ffprobe_meta.get("width") or cv_meta.get("width") or 0
    height = ffprobe_meta.get("height") or cv_meta.get("height") or 0
    fps = ffprobe_meta.get("fps") or cv_meta.get("fps") or 0.0
    frame_count = ffprobe_meta.get("frame_count") or cv_meta.get("frame_count") or 0
    video_codec = ffprobe_meta.get("video_codec") or "UNKNOWN"
    audio_presence = ffprobe_meta.get("audio_presence") or (audio_meta.get("status") == "ANALYZED")
    audio_duration = audio_meta.get("audio_duration") if audio_presence else (ffprobe_meta.get("audio_duration") or "NOT_AVAILABLE")

    resolution = f"{width}x{height}" if width and height else "UNKNOWN"

    res = {
        "status": "ANALYZED",
        "file_path": abs_path,
        "duration": round(float(duration), 2),
        "width": int(width),
        "height": int(height),
        "resolution": resolution,
        "fps": round(float(fps), 2),
        "frame_count": int(frame_count),
        "video_codec": str(video_codec),
        "audio_presence": bool(audio_presence),
        "audio_duration": round(float(audio_duration), 2) if isinstance(audio_duration, (int, float)) else audio_duration,
        "audio_analysis": audio_meta
    }
    _MEDIA_CACHE[cache_key] = res
    return res


def extract_representative_frames(file_path: str, sample_count: int = 5, output_dir: str = None) -> list:
    """
    Safely extract representative frame images (0%, 25%, 50%, 75%, 100%).
    Returns list of dicts: [{'timestamp': float, 'frame_path': str}].
    """
    if not file_path or not os.path.isfile(file_path):
        return []

    if output_dir is None:
        output_dir = os.path.join(tempfile.gettempdir(), "jarvis_frames")
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if total_frames <= 0:
        cap.release()
        return []

    extracted = []
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    sample_count = min(sample_count, 3)
    percentages = [0.0, 0.50, 0.99] if sample_count == 3 else [i / max(1, sample_count - 1) for i in range(sample_count)]

    for idx, pct in enumerate(percentages):
        target_frame = int(pct * (total_frames - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        if ret:
            timestamp = round(target_frame / fps, 2)
            out_filename = f"{base_name}_frame_{idx}_{int(timestamp * 100)}ms.jpg"
            out_path = os.path.join(output_dir, out_filename)
            cv2.imwrite(out_path, frame)
            extracted.append({
                "timestamp": timestamp,
                "frame_index": target_frame,
                "frame_path": out_path
            })

    cap.release()
    return extracted


def detect_scenes(file_path: str, min_scene_len: float = 2.0, threshold: float = 0.35) -> list:
    """
    Deterministic scene candidate detection using frame-difference and HSV histogram differences.
    Returns list of scene dicts:
    [
        {
            "scene_id": "scene_001",
            "start": 0.0,
            "end": 5.2,
            "duration": 5.2,
            "representative_frame": "...",
            "confidence": 0.85
        }
    ]
    """
    meta = analyze_media(file_path)
    duration = meta.get("duration", 0.0)
    if duration <= 0:
        if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
            duration = 5.0
        else:
            return []

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        return _fallback_scenes(duration, min_scene_len)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_step = max(1, int(total_frames / 20)) if total_frames > 20 else 1

    cut_timestamps = [0.0]
    prev_hist = None
    f_idx = 0

    while f_idx < total_frames:
        ret = cap.grab()
        if not ret:
            break
        if f_idx % sample_step == 0:
            ret, frame = cap.retrieve()
            if ret:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
                cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

                if prev_hist is not None:
                    diff = 1.0 - cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    ts = round(f_idx / fps, 2)
                    if diff > threshold and (ts - cut_timestamps[-1]) >= min_scene_len:
                        cut_timestamps.append(ts)

                prev_hist = hist
        f_idx += 1

    cap.release()

    if cut_timestamps[-1] < duration:
        cut_timestamps.append(duration)

    if len(cut_timestamps) < 2:
        return _fallback_scenes(duration, min_scene_len)

    scenes = []
    frames = extract_representative_frames(file_path, sample_count=len(cut_timestamps) - 1)

    for i in range(len(cut_timestamps) - 1):
        s_start = cut_timestamps[i]
        s_end = cut_timestamps[i + 1]
        s_dur = round(s_end - s_start, 2)
        if s_dur <= 0.1:
            continue
        rep_frame = frames[i]["frame_path"] if i < len(frames) else "NOT_AVAILABLE"
        scenes.append({
            "scene_id": f"scene_{i + 1:03d}",
            "start": s_start,
            "end": s_end,
            "duration": s_dur,
            "representative_frame": rep_frame,
            "confidence": 0.85
        })

    return scenes


def _fallback_scenes(duration: float, segment_len: float = 5.0) -> list:
    """Fallback to slice duration into uniform candidate scene chunks."""
    scenes = []
    curr = 0.0
    idx = 1
    while curr < duration:
        nxt = min(duration, round(curr + segment_len, 2))
        dur = round(nxt - curr, 2)
        if dur > 0.1:
            scenes.append({
                "scene_id": f"scene_{idx:03d}",
                "start": curr,
                "end": nxt,
                "duration": dur,
                "representative_frame": "NOT_AVAILABLE",
                "confidence": 0.50
            })
            idx += 1
        curr = nxt
    return scenes


from video_editing.utils.ffprobe_finder import run_ffprobe as _ffprobe_runner


def _run_ffprobe(file_path: str) -> dict:
    try:
        return _ffprobe_runner(file_path)
    except Exception:
        return {}


def _run_opencv_meta(file_path: str) -> dict:
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
            "fps": fps,
            "frame_count": fc,
            "duration": dur
        }
    except Exception:
        return {}
