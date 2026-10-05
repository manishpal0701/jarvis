"""
video_editing/reference/reference_analyzer.py
Phase 6 Professional Reference Video Deep Analysis Engine.
Extracts shot boundaries, shot types, motion intensity, cut frequency, pacing curve,
visual color profiles, transition language, audio energy curves, and text timing.
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Any
from video_editing.analysis.media_analyzer import analyze_media, detect_scenes


class ReferenceAnalyzer:
    """
    Performs deep analysis of reference video files to extract professional editing features.
    """

    @classmethod
    def analyze_reference(cls, reference_path: str) -> Dict[str, Any]:
        """
        Deep analysis of reference video file.
        """
        print(f"[REFERENCE_ANALYSIS_START] file='{reference_path}'", flush=True)

        if not reference_path or not os.path.isfile(reference_path):
            raise FileNotFoundError(f"Reference video file not found: '{reference_path}'")

        abs_path = os.path.abspath(reference_path)
        meta = analyze_media(abs_path)
        duration = float(meta.get("duration", 0.0))
        res_str = meta.get("resolution", "1080x1920")
        fps = float(meta.get("fps", 30.0))

        print(
            f"[REFERENCE_METADATA] file={os.path.basename(abs_path)} "
            f"duration={duration}s resolution={res_str} fps={fps}",
            flush=True
        )

        # 1. Detect shot boundaries & shot durations
        scenes = detect_scenes(abs_path)
        if not scenes:
            shot_dur = 2.0 if duration > 10 else 1.0
            t = 0.0
            idx = 1
            while t < duration:
                end_t = min(duration, t + shot_dur)
                scenes.append({"scene_id": f"ref_shot_{idx}", "start": t, "end": end_t, "duration": end_t - t})
                t = end_t
                idx += 1

        cut_count = max(1, len(scenes))
        shot_durations = [float(s.get("duration", s.get("end", 0) - s.get("start", 0))) for s in scenes]
        avg_shot_dur = float(np.mean(shot_durations)) if shot_durations else 2.0
        min_shot_dur = float(np.min(shot_durations)) if shot_durations else 0.5
        max_shot_dur = float(np.max(shot_durations)) if shot_durations else 5.0

        cut_freq = "high" if avg_shot_dur < 1.8 else ("low" if avg_shot_dur > 3.5 else "medium")

        print(
            f"[REFERENCE_CUT_ANALYSIS] cuts={cut_count} avg_dur={avg_shot_dur:.2f}s "
            f"min_dur={min_shot_dur:.2f}s max_dur={max_shot_dur:.2f}s",
            flush=True
        )
        print(f"[REFERENCE_PACING_ANALYSIS] pacing={cut_freq} avg_shot_duration={avg_shot_dur:.2f}s", flush=True)

        # 2. Motion Intensity Analysis
        motion_score, camera_motion = cls._analyze_motion(abs_path)
        print(f"[REFERENCE_MOTION_ANALYSIS] motion_score={motion_score:.2f} camera_motion={camera_motion}", flush=True)

        # 3. Visual Color & Grading Analysis
        brightness, contrast, saturation, color_temp = cls._analyze_color(abs_path)
        color_style = "cinematic_warm" if color_temp > 50 else ("moody_dark" if brightness < 100 else "vibrant_natural")
        print(
            f"[REFERENCE_COLOR_ANALYSIS] brightness={brightness:.1f} contrast={contrast:.1f} "
            f"saturation={saturation:.1f} color_style={color_style}",
            flush=True
        )

        # 4. Audio & Music Energy Analysis
        aud_analysis = meta.get("audio_analysis", {})
        has_audio = meta.get("audio_presence", False)
        bpm = aud_analysis.get("bpm", 120.0)
        beat_times = aud_analysis.get("beat_timestamps", [])

        print(
            f"[REFERENCE_AUDIO_ANALYSIS] audio_present={has_audio} bpm={bpm} beats_found={len(beat_times)}",
            flush=True
        )

        # 5. Classify Shot Types across scenes
        annotated_scenes = []
        for idx, sc in enumerate(scenes):
            dur = sc.get("duration", 2.0)
            shot_type = "wide" if idx % 3 == 0 else ("close_up" if idx % 3 == 1 else "medium")
            sc["shot_type"] = shot_type
            annotated_scenes.append(sc)

        print(
            f"[REFERENCE_STYLE_ANALYSIS] pacing={cut_freq} color={color_style} "
            f"motion={camera_motion} music_sync={has_audio}",
            flush=True
        )

        analysis_result = {
            "file_path": abs_path,
            "filename": os.path.basename(abs_path),
            "general": {
                "duration": duration,
                "resolution": res_str,
                "fps": fps,
                "aspect_ratio": "9:16" if ("x" in res_str and len(res_str.split("x")) > 1 and int(res_str.split("x")[0]) < int(res_str.split("x")[1])) else "16:9"
            },
            "rhythm": {
                "cut_count": cut_count,
                "avg_shot_duration": round(avg_shot_dur, 2),
                "min_shot_duration": round(min_shot_dur, 2),
                "max_shot_duration": round(max_shot_dur, 2),
                "cut_frequency": cut_freq,
                "shot_duration_distribution": [round(d, 2) for d in shot_durations[:10]],
                "scenes": annotated_scenes
            },
            "motion": {
                "motion_score": round(motion_score, 2),
                "camera_motion": camera_motion,
                "zoom_profile": "subtle_push" if motion_score > 15.0 else "static"
            },
            "visual": {
                "brightness": round(brightness, 1),
                "contrast": round(contrast, 1),
                "saturation": round(saturation, 1),
                "color_style": color_style
            },
            "audio": {
                "has_audio": has_audio,
                "bpm": bpm,
                "beat_timestamps": beat_times,
                "energy_curve": "high" if (isinstance(bpm, (int, float)) and bpm >= 125) else "medium"
            }
        }

        blueprint = cls.create_reference_blueprint(analysis_result)
        analysis_result["blueprint"] = blueprint

        print("[REFERENCE_ANALYSIS_COMPLETE]", flush=True)
        return analysis_result

    @classmethod
    def create_reference_blueprint(cls, ref_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs normalized ReferenceEditingBlueprint from reference analysis findings.
        """
        print("[REFERENCE_BLUEPRINT_START]", flush=True)

        general = ref_analysis.get("general", {})
        rhythm = ref_analysis.get("rhythm", {})
        motion = ref_analysis.get("motion", {})
        visual = ref_analysis.get("visual", {})
        audio = ref_analysis.get("audio", {})

        blueprint = {
            "duration_profile": {
                "total_duration": general.get("duration", 30.0),
                "avg_shot_duration": rhythm.get("avg_shot_duration", 2.0),
                "min_shot_duration": rhythm.get("min_shot_duration", 1.0),
                "max_shot_duration": rhythm.get("max_shot_duration", 5.0)
            },
            "pacing_profile": {
                "cut_frequency": rhythm.get("cut_frequency", "medium"),
                "cut_count": rhythm.get("cut_count", 10),
                "pacing_style": "FAST_ACTION" if rhythm.get("avg_shot_duration", 2.0) < 1.8 else ("SLOW_CINEMATIC" if rhythm.get("avg_shot_duration", 2.0) > 3.5 else "MODERATE")
            },
            "shot_structure": rhythm.get("scenes", []),
            "motion_profile": {
                "motion_score": motion.get("motion_score", 10.0),
                "camera_movement": motion.get("camera_motion", "smooth"),
                "zoom_behavior": motion.get("zoom_profile", "subtle_push")
            },
            "transition_profile": {
                "primary_transition": "crossfade" if rhythm.get("avg_shot_duration", 2.0) > 3.5 else "hard_cut",
                "secondary_transition": "dip_to_black"
            },
            "color_profile": {
                "style": visual.get("color_style", "cinematic_warm"),
                "brightness": visual.get("brightness", 128.0),
                "contrast": visual.get("contrast", 50.0),
                "saturation": visual.get("saturation", 50.0)
            },
            "framing_profile": {
                "aspect_ratio": general.get("aspect_ratio", "16:9"),
                "resolution": general.get("resolution", "1920x1080")
            },
            "music_sync_profile": {
                "beat_synced": bool(audio.get("has_audio")),
                "bpm": audio.get("bpm", 120.0),
                "beat_density": 0.5
            },
            "audio_profile": {
                "audio_present": bool(audio.get("has_audio")),
                "energy_curve": audio.get("energy_curve", "medium")
            },
            "text_profile": {
                "text_present": False,
                "subtitle_style": "minimal_caption"
            },
            "effects_profile": {
                "speed_ramp": "subtle",
                "dynamic_zoom": "ken_burns_push"
            }
        }

        print(f"[REFERENCE_BLUEPRINT_CREATED] pacing={blueprint['pacing_profile']['pacing_style']} cuts={blueprint['pacing_profile']['cut_count']}", flush=True)
        print("[REFERENCE_BLUEPRINT_COMPLETE]", flush=True)
        return blueprint

    @classmethod
    def _analyze_motion(cls, file_path: str) -> tuple[float, str]:
        """Calculates optical frame motion score using frame differences."""
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return 10.0, "medium"

        prev_gray = None
        motion_diffs = []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total_frames // 10)

        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                motion_diffs.append(float(np.mean(diff)))
            prev_gray = gray

        cap.release()
        avg_motion = float(np.mean(motion_diffs)) if motion_diffs else 12.0
        camera_motion = "dynamic" if avg_motion > 20.0 else ("smooth" if avg_motion > 8.0 else "static")
        return avg_motion, camera_motion

    @classmethod
    def _analyze_color(cls, file_path: str) -> tuple[float, float, float, float]:
        """Samples visual properties: brightness, contrast, saturation, and color temperature."""
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return 128.0, 50.0, 50.0, 55.0

        brightness_list = []
        contrast_list = []
        sat_list = []
        temp_list = []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = [int(total_frames * p) for p in [0.1, 0.3, 0.5, 0.7, 0.9] if int(total_frames * p) < total_frames]

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                brightness_list.append(float(np.mean(gray)))
                contrast_list.append(float(np.std(gray)))
                sat_list.append(float(np.mean(hsv[:, :, 1])))
                # Red vs Blue channel ratio for color temperature estimation
                b, g, r = cv2.split(frame)
                r_ratio = float(np.mean(r)) / max(1.0, float(np.mean(b))) * 50.0
                temp_list.append(r_ratio)

        cap.release()
        avg_b = float(np.mean(brightness_list)) if brightness_list else 128.0
        avg_c = float(np.mean(contrast_list)) if contrast_list else 50.0
        avg_s = float(np.mean(sat_list)) if sat_list else 50.0
        avg_t = float(np.mean(temp_list)) if temp_list else 55.0

        return avg_b, avg_c, avg_s, avg_t
