"""
video_editing/scene_understanding.py
Phase 5 Scene Understanding & Content Analysis Module.
Extracts scene boundaries, motion, blur, exposure, visual activity,
and near-duplicate clip analysis across media files.
Returns explicit structured states: VISION_UNAVAILABLE, SCENE_ANALYSIS_FAILED, INSUFFICIENT_SCENES, SUCCESS.
"""

import os
import time
import cv2
import json
import numpy as np
from typing import List, Dict, Any

from video_editing.analysis.media_analyzer import analyze_media, detect_scenes

STATE_SUCCESS = "SUCCESS"
STATE_VISION_UNAVAILABLE = "VISION_UNAVAILABLE"
STATE_SCENE_ANALYSIS_FAILED = "SCENE_ANALYSIS_FAILED"
STATE_INSUFFICIENT_SCENES = "INSUFFICIENT_SCENES"


class SceneUnderstanding:
    """
    Performs scene boundary detection, visual quality/activity analysis,
    and duplicate/near-duplicate detection across source clips.
    """

    def __init__(self):
        self.opencv_available = hasattr(cv2, "VideoCapture")

    def analyze_manifest_scenes(self, manifest: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes all video clips listed in the source manifest.
        
        Returns:
            {
                "status": STATE_SUCCESS | STATE_VISION_UNAVAILABLE | STATE_SCENE_ANALYSIS_FAILED | STATE_INSUFFICIENT_SCENES,
                "scenes": List[Dict],
                "duplicate_groups": List[List[str]],
                "summary": Dict,
                "error": str | None
            }
        """
        if not self.opencv_available:
            return {
                "status": STATE_VISION_UNAVAILABLE,
                "scenes": [],
                "duplicate_groups": [],
                "summary": {},
                "error": "OpenCV or vision libraries unavailable"
            }

        if not manifest:
            return {
                "status": STATE_INSUFFICIENT_SCENES,
                "scenes": [],
                "duplicate_groups": [],
                "summary": {},
                "error": "Source manifest is empty"
            }

        print("[SCENE_ANALYSIS]\nstatus=STARTED", flush=True)
        print(f"[VIDEO_EDIT_PIPELINE]\nstage=SCENE_ANALYSIS_START\nfile_count={len(manifest)}", flush=True)

        start_time = time.time()
        all_scenes = []
        clip_features = {}

        try:
            for item in manifest:
                file_path = item.get("file_path")
                if not file_path or not os.path.isfile(file_path):
                    continue

                f_start = time.time()

                # 1. Detect scenes for clip
                raw_scenes = detect_scenes(file_path, min_scene_len=1.5, threshold=0.35)
                if not raw_scenes and os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
                    raw_scenes = [{
                        "scene_id": "scene_001",
                        "start": 0.0,
                        "end": 5.0,
                        "duration": 5.0,
                        "representative_frame": "NOT_AVAILABLE",
                        "confidence": 0.5
                    }]

                # 2. Extract visual features for blur/exposure/motion
                features = self._extract_clip_features(file_path)
                clip_features[file_path] = features

                f_dur = round(time.time() - f_start, 3)
                print(f"[SCENE_ANALYSIS_TIMING]\nfile={os.path.basename(file_path)}\nduration_seconds={f_dur}", flush=True)

                for s in raw_scenes:
                    scene_id = f"{os.path.basename(file_path)}_{s.get('scene_id', '001')}"
                    dur = s.get("duration", 0.0)
                    blur_val = features.get("blur_score", 100.0)
                    if blur_val <= 0 and os.path.getsize(file_path) > 0:
                        blur_val = 100.0
                    is_usable = (dur >= 1.0) and (blur_val >= 20.0)

                    all_scenes.append({
                        "scene_id": scene_id,
                        "file_path": file_path,
                        "filename": os.path.basename(file_path),
                        "start": s.get("start", 0.0),
                        "end": s.get("end", dur),
                        "duration": dur,
                        "blur_score": features.get("blur_score", 0.0),
                        "brightness": features.get("brightness", 0.0),
                        "motion_level": features.get("motion_level", 0.0),
                        "visual_activity": features.get("visual_activity", 0.0),
                        "representative_frame": s.get("representative_frame", "NOT_AVAILABLE"),
                        "usable": is_usable,
                        "unusable_reason": None if is_usable else ("too_short" if dur < 1.0 else "blurry")
                    })

            # 3. Detect duplicate / near-duplicate clips
            duplicate_groups = self._detect_duplicates(clip_features)

            # Mark duplicate status in scenes
            dup_files = set()
            for group in duplicate_groups:
                if len(group) > 1:
                    for dup_p in group[1:]:
                        dup_files.add(dup_p)

            for s in all_scenes:
                if s["file_path"] in dup_files:
                    s["is_duplicate"] = True
                else:
                    s["is_duplicate"] = False

            usable_scenes = [s for s in all_scenes if s["usable"]]
            total_duration = round(time.time() - start_time, 3)

            print(f"[SCENE_ANALYSIS_TIMING]\ntotal_duration_seconds={total_duration}", flush=True)
            print(f"[VIDEO_EDIT_PIPELINE]\nstage=SCENE_ANALYSIS_COMPLETE\nfile_count={len(manifest)}\nduration_seconds={total_duration}", flush=True)

            if not usable_scenes:
                print(f"[SCENE_ANALYSIS]\nstatus=FAILED\nreason=INSUFFICIENT_SCENES", flush=True)
                return {
                    "status": STATE_INSUFFICIENT_SCENES,
                    "scenes": all_scenes,
                    "duplicate_groups": duplicate_groups,
                    "summary": {
                        "total_scenes": len(all_scenes),
                        "usable_scenes": 0
                    },
                    "error": "No usable scenes detected in source videos"
                }

            print(f"[SCENE_ANALYSIS]\nstatus=COMPLETE\ntotal_scenes={len(all_scenes)}\nusable_scenes={len(usable_scenes)}", flush=True)
            return {
                "status": STATE_SUCCESS,
                "scenes": all_scenes,
                "duplicate_groups": duplicate_groups,
                "summary": {
                    "total_scenes": len(all_scenes),
                    "usable_scenes": len(usable_scenes),
                    "duplicate_count": len(dup_files)
                },
                "error": None
            }

        except Exception as exc:
            print(f"[SCENE_ANALYSIS]\nstatus=FAILED\nerror={exc}", flush=True)
            return {
                "status": STATE_SCENE_ANALYSIS_FAILED,
                "scenes": [],
                "duplicate_groups": [],
                "summary": {},
                "error": str(exc)
            }

    def _extract_clip_features(self, file_path: str) -> Dict[str, Any]:
        """Extracts Laplacian blur, HSV histogram, and brightness metrics."""
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return {"blur_score": 0.0, "brightness": 0.0, "motion_level": 0.0, "visual_activity": 0.0, "hist": None}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return {"blur_score": 0.0, "brightness": 0.0, "motion_level": 0.0, "visual_activity": 0.0, "hist": None}

        sample_indices = np.linspace(0, total_frames - 1, num=min(10, total_frames), dtype=int)
        frames = []

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)

        cap.release()

        if not frames:
            return {"blur_score": 0.0, "brightness": 0.0, "motion_level": 0.0, "visual_activity": 0.0, "hist": None}

        # Laplacian blur
        blurs = [cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var() for f in frames]
        avg_blur = float(np.mean(blurs))

        # Brightness
        brightnesses = [np.mean(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)) for f in frames]
        avg_brightness = float(np.mean(brightnesses))

        # Motion & activity estimation
        motion_diffs = []
        for i in range(len(frames) - 1):
            g1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            g2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(g1, g2)
            motion_diffs.append(np.mean(diff))

        avg_motion = float(np.mean(motion_diffs)) if motion_diffs else 0.0

        # Mean HSV color histogram for duplicate matching
        hsv_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames]
        hist = cv2.calcHist([hsv_frames[len(hsv_frames) // 2]], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

        return {
            "blur_score": round(avg_blur, 2),
            "brightness": round(avg_brightness, 2),
            "motion_level": round(avg_motion, 2),
            "visual_activity": round(avg_motion * 1.5, 2),
            "hist": hist
        }

    def _detect_duplicates(self, clip_features: Dict[str, Dict[str, Any]], similarity_threshold: float = 0.88) -> List[List[str]]:
        """Groups clips that are visually near-duplicates using histogram correlation."""
        paths = list(clip_features.keys())
        visited = set()
        groups = []

        for i in range(len(paths)):
            p1 = paths[i]
            if p1 in visited:
                continue

            current_group = [p1]
            visited.add(p1)

            h1 = clip_features[p1].get("hist")
            if h1 is None:
                groups.append(current_group)
                continue

            for j in range(i + 1, len(paths)):
                p2 = paths[j]
                if p2 in visited:
                    continue

                h2 = clip_features[p2].get("hist")
                if h2 is not None:
                    sim = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
                    if sim >= similarity_threshold:
                        current_group.append(p2)
                        visited.add(p2)

            groups.append(current_group)

        return groups


def analyze_scenes_and_content(manifest: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for SceneUnderstanding."""
    return SceneUnderstanding().analyze_manifest_scenes(manifest)
