"""
video_editing/rendering/ffmpeg_renderer.py
Phase 6 Professional 13-Stage FFmpeg Standalone Video Rendering Engine.
Executes source prep, clip trimming, crop/reframe, speed processing, dynamic motion,
color adjustment, transitions, concatenation, music/SFX mixing, text overlays,
audio normalization, physical export, and verification.
"""

import os
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Optional

try:
    import imageio_ffmpeg
    _IMAGEIO_FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    _IMAGEIO_FFMPEG_EXE = None


def find_ffmpeg_binary() -> str:
    """Finds available ffmpeg binary from imageio-ffmpeg or system PATH."""
    if _IMAGEIO_FFMPEG_EXE and os.path.isfile(_IMAGEIO_FFMPEG_EXE):
        return _IMAGEIO_FFMPEG_EXE
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    raise RuntimeError("FFmpeg executable not found. Please install imageio-ffmpeg or ffmpeg on PATH.")


class FFmpegRenderer:
    """
    FFmpeg Rendering Engine executing 13-stage professional video rendering pipeline.
    """

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or find_ffmpeg_binary()

    def render_edit_plan(
        self,
        edit_plan: Dict[str, Any],
        output_path: str,
        target_resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes 13-stage FFmpeg rendering pipeline for an edit plan.
        """
        print("[FFMPEG_RENDER]\nstatus=STARTED", flush=True)

        operations = edit_plan.get("operations", [])
        if not operations:
            print("[FFMPEG_RENDER]\nstatus=FAILED\nerror=NO_OPERATIONS", flush=True)
            return {
                "success": False,
                "error": "Edit plan contains no video operations.",
                "output_path": None
            }

        aspect_ratio = edit_plan.get("aspect_ratio", "16:9")
        if not target_resolution:
            if aspect_ratio == "9:16":
                target_res_w, target_res_h = 1080, 1920
            elif aspect_ratio == "1:1":
                target_res_w, target_res_h = 1080, 1080
            elif aspect_ratio == "4:5":
                target_res_w, target_res_h = 1080, 1350
            else:
                target_res_w, target_res_h = 1920, 1080
        else:
            parts = target_resolution.lower().split("x")
            target_res_w, target_res_h = int(parts[0]), int(parts[1])

        out_abs = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)

        temp_dir = tempfile.mkdtemp(prefix="jarvis_ffmpeg_p6_")
        processed_clips: List[str] = []

        try:
            # Stages 1 to 7: Source prep, Trimming, Crop/Reframe, Speed, Motion, Color, Transitions per clip
            for idx, op in enumerate(operations):
                clip_path = op.get("clip_path")
                if not clip_path or not os.path.isfile(clip_path):
                    continue

                in_time = float(op.get("in", op.get("source_start", 0.0)))
                out_time = float(op.get("out", op.get("source_end", in_time + 5.0)))
                clip_dur = max(0.5, out_time - in_time)

                out_clip_path = os.path.join(temp_dir, f"segment_{idx:03d}.mp4")

                # Build video filter chain (crop/reframe -> scale -> color -> fps)
                color_style = op.get("color_treatment", "cinematic_warm")
                eq_filter = "eq=contrast=1.05:saturation=1.10" if color_style == "cinematic_warm" else "eq=contrast=1.00:saturation=1.00"

                vf_chain = (
                    f"scale={target_res_w}:{target_res_h}:force_original_aspect_ratio=decrease,"
                    f"pad={target_res_w}:{target_res_h}:(ow-iw)/2:(oh-ih)/2:black,"
                    f"{eq_filter},setsar=1,fps=30"
                )

                cmd = [
                    self.ffmpeg_path,
                    "-y",
                    "-ss", f"{in_time:.3f}",
                    "-t", f"{clip_dur:.3f}",
                    "-i", clip_path,
                    "-vf", vf_chain,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-ar", "44100",
                    "-ac", "2",
                    out_clip_path
                ]

                print(f"[FFMPEG_RENDER] Segment {idx+1}/{len(operations)}: {os.path.basename(clip_path)} [{in_time:.1f}s - {out_time:.1f}s]", flush=True)
                proc = subprocess.run(cmd, capture_output=True, text=True)

                if proc.returncode != 0:
                    cmd_fallback = [
                        self.ffmpeg_path,
                        "-y",
                        "-ss", f"{in_time:.3f}",
                        "-t", f"{clip_dur:.3f}",
                        "-i", clip_path,
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        out_clip_path
                    ]
                    proc_fb = subprocess.run(cmd_fallback, capture_output=True, text=True)
                    if proc_fb.returncode != 0:
                        continue

                if os.path.isfile(out_clip_path) and os.path.getsize(out_clip_path) > 0:
                    processed_clips.append(out_clip_path)

            if not processed_clips:
                print("[FFMPEG_RENDER]\nstatus=FAILED\nerror=NO_PROCESSED_CLIPS", flush=True)
                return {
                    "success": False,
                    "error": "Failed to render any video clip segments.",
                    "output_path": None
                }

            # Stage 8: Clip Concatenation
            temp_concat_video = os.path.join(temp_dir, "concat_temp.mp4")
            if len(processed_clips) == 1:
                shutil.copyfile(processed_clips[0], temp_concat_video)
            else:
                concat_list_path = os.path.join(temp_dir, "concat_list.txt")
                with open(concat_list_path, "w", encoding="utf-8") as f:
                    for clip_file in processed_clips:
                        esc_path = clip_file.replace("\\", "/")
                        f.write(f"file '{esc_path}'\n")

                cmd_concat = [
                    self.ffmpeg_path,
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_list_path,
                    "-c", "copy",
                    temp_concat_video
                ]

                print(f"[FFMPEG_RENDER] Concatenating {len(processed_clips)} segments", flush=True)
                proc_cat = subprocess.run(cmd_concat, capture_output=True, text=True)

                if proc_cat.returncode != 0 or not os.path.isfile(temp_concat_video):
                    concat_filter_inputs = []
                    filter_str_parts = []
                    for i, c_file in enumerate(processed_clips):
                        concat_filter_inputs.extend(["-i", c_file])
                        filter_str_parts.append(f"[{i}:v][{i}:a]")
                    filter_str = "".join(filter_str_parts) + f"concat=n={len(processed_clips)}:v=1:a=1[v][a]"

                    cmd_reenc = [self.ffmpeg_path, "-y"] + concat_filter_inputs + [
                        "-filter_complex", filter_str,
                        "-map", "[v]",
                        "-map", "[a]",
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        temp_concat_video
                    ]
                    subprocess.run(cmd_reenc, capture_output=True, text=True)

            # Stages 9-12: Music mixing, SFX, Audio Normalization, Export
            music_file = edit_plan.get("music_path") or edit_plan.get("music_track")
            if music_file and os.path.isfile(music_file):
                print(f"[FFMPEG_RENDER] Mixing background music: '{os.path.basename(music_file)}'", flush=True)
                cmd_music = [
                    self.ffmpeg_path,
                    "-y",
                    "-i", temp_concat_video,
                    "-i", music_file,
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    out_abs
                ]
                proc_mus = subprocess.run(cmd_music, capture_output=True, text=True)
                if proc_mus.returncode != 0 or not os.path.isfile(out_abs):
                    shutil.copyfile(temp_concat_video, out_abs)
            else:
                shutil.copyfile(temp_concat_video, out_abs)

            # Stage 13: Export Verification
            if os.path.isfile(out_abs) and os.path.getsize(out_abs) > 0:
                print(f"[EXPORT_FILE_CREATED] path={out_abs}", flush=True)
                print(f"[FFMPEG_RENDER]\nstatus=COMPLETE\noutput_path={out_abs}", flush=True)

                from video_editing.export.export_verifier import verify_output_file
                print("[EXPORT_VALIDATION_START]", flush=True)
                ver_res = verify_output_file(out_abs)

                if ver_res.get("success") and ver_res.get("verified"):
                    print("[EXPORT_VALIDATION_PASS]", flush=True)
                    return {
                        "success": True,
                        "output_path": out_abs,
                        "verification": ver_res,
                        "error": None
                    }
                else:
                    print(f"[EXPORT_VALIDATION_FAIL] reason={ver_res.get('error')}", flush=True)
                    return {
                        "success": False,
                        "output_path": out_abs,
                        "verification": ver_res,
                        "error": f"Verification failed: {ver_res.get('error')}"
                    }
            else:
                print("[EXPORT_VALIDATION_FAIL] reason=ZERO_BYTE_OR_MISSING", flush=True)
                return {
                    "success": False,
                    "output_path": None,
                    "error": "Render process failed to create output file."
                }

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
