"""
video_editing/utils/ffprobe_finder.py
Reliable ffprobe/ffmpeg Executable Discovery & Stream Metadata Extraction.
Locates installed ffprobe/ffmpeg binary across system PATH, imageio_ffmpeg,
venv, env vars, and standard installation directories.
Raises clear, actionable errors when binaries are missing.
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Optional, Dict, Any

_CACHED_FFPROBE_PATH: Optional[str] = None


def find_ffprobe_executable() -> Optional[str]:
    """
    Locates an installed ffprobe (or ffmpeg fallback) executable.
    Caches and returns the absolute executable path, or None if not found.
    """
    global _CACHED_FFPROBE_PATH
    if _CACHED_FFPROBE_PATH and os.path.isfile(_CACHED_FFPROBE_PATH):
        return _CACHED_FFPROBE_PATH

    # 1. Check environment variable FFPROBE_PATH
    env_path = os.environ.get("FFPROBE_PATH")
    if env_path and os.path.isfile(env_path):
        _CACHED_FFPROBE_PATH = os.path.abspath(env_path)
        return _CACHED_FFPROBE_PATH

    # 2. Check config.py if defined
    try:
        import config
        cfg_path = getattr(config, "FFPROBE_PATH", None)
        if cfg_path and os.path.isfile(cfg_path):
            _CACHED_FFPROBE_PATH = os.path.abspath(cfg_path)
            return _CACHED_FFPROBE_PATH
    except Exception:
        pass

    # 3. Check system PATH via shutil.which
    which_ffprobe = shutil.which("ffprobe")
    if which_ffprobe and os.path.isfile(which_ffprobe):
        _CACHED_FFPROBE_PATH = os.path.abspath(which_ffprobe)
        return _CACHED_FFPROBE_PATH

    # 4. Check imageio_ffmpeg package binaries
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
            bin_dir = os.path.dirname(ffmpeg_exe)
            # Check for ffprobe alongside ffmpeg
            for candidate_name in ["ffprobe.exe", "ffprobe"]:
                candidate = os.path.join(bin_dir, candidate_name)
                if os.path.isfile(candidate):
                    _CACHED_FFPROBE_PATH = os.path.abspath(candidate)
                    return _CACHED_FFPROBE_PATH
            # Return ffmpeg as fallback executable
            _CACHED_FFPROBE_PATH = os.path.abspath(ffmpeg_exe)
            return _CACHED_FFPROBE_PATH
    except Exception:
        pass

    # 5. Check venv and python executable directory
    exe_dir = os.path.dirname(sys.executable)
    for candidate in [
        os.path.join(exe_dir, "ffprobe.exe"),
        os.path.join(exe_dir, "ffmpeg.exe"),
        os.path.join(exe_dir, "Scripts", "ffprobe.exe"),
        os.path.join(exe_dir, "Scripts", "ffmpeg.exe"),
    ]:
        if os.path.isfile(candidate):
            _CACHED_FFPROBE_PATH = os.path.abspath(candidate)
            return _CACHED_FFPROBE_PATH

    # 6. Common Windows system installation paths
    user_home = os.path.expanduser("~")
    common_paths = [
        r"C:\ffmpeg\bin\ffprobe.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffprobe.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        os.path.join(user_home, "AppData", "Local", "Microsoft", "WinGet", "Packages"),
        os.path.join(user_home, "scoop", "apps", "ffmpeg", "current", "bin", "ffprobe.exe"),
    ]

    for item in common_paths:
        if os.path.isfile(item):
            _CACHED_FFPROBE_PATH = os.path.abspath(item)
            return _CACHED_FFPROBE_PATH
        elif os.path.isdir(item):
            # Scan directory recursively for ffprobe.exe
            for root, _, files in os.walk(item):
                for f in files:
                    if f.lower() in ("ffprobe.exe", "ffprobe", "ffmpeg.exe", "ffmpeg"):
                        _CACHED_FFPROBE_PATH = os.path.abspath(os.path.join(root, f))
                        return _CACHED_FFPROBE_PATH

    return None


def run_ffprobe(file_path: str) -> Dict[str, Any]:
    """
    Executes discovered ffprobe/ffmpeg binary against specified media file_path.
    Returns structured metadata dictionary.
    Raises RuntimeError if binary cannot be located.
    """
    executable = find_ffprobe_executable()
    if not executable:
        raise RuntimeError(
            "FFPROBE_NOT_FOUND: 'ffprobe' or 'ffmpeg' executable is not installed or not found in system PATH. "
            "Please install ffmpeg/ffprobe or configure FFPROBE_PATH."
        )

    norm_path = os.path.normpath(file_path)
    out: Dict[str, Any] = {"has_video": False, "has_audio": False}

    is_ffmpeg = "ffmpeg" in os.path.basename(executable).lower() and "ffprobe" not in os.path.basename(executable).lower()

    if not is_ffmpeg:
        # Use ffprobe JSON output
        cmd = [executable, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", norm_path]
        try:
            res = subprocess.check_output(cmd, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).decode("utf-8")
            data = json.loads(res)
            fmt = data.get("format", {})
            out["duration"] = float(fmt.get("duration", 0.0))

            for stream in data.get("streams", []):
                codec_type = stream.get("codec_type")
                if codec_type == "video" and not out["has_video"]:
                    out["has_video"] = True
                    out["width"] = int(stream.get("width", 0))
                    out["height"] = int(stream.get("height", 0))
                    out["video_codec"] = stream.get("codec_name", "UNKNOWN")
                    out["frame_count"] = int(stream.get("nb_frames", 0)) if stream.get("nb_frames") else 0
                    r_fps = stream.get("r_frame_rate", "30/1")
                    if "/" in r_fps:
                        num, den = r_fps.split("/")
                        out["fps"] = float(num) / float(den) if float(den) > 0 else 30.0
                    else:
                        out["fps"] = float(r_fps)
                elif codec_type == "audio":
                    out["has_audio"] = True
                    out["audio_duration"] = float(stream.get("duration", fmt.get("duration", 0.0)))
            return out
        except Exception as exc:
            print(f"[FFPROBE_WARNING] ffprobe execution failed: {exc}", flush=True)
            return out
    else:
        # Fallback to ffmpeg -hide_banner -i output parsing
        cmd = [executable, "-hide_banner", "-i", norm_path]
        try:
            p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            _, stderr_data = p.communicate()
            err_text = stderr_data.decode("utf-8", errors="ignore")

            # Extract duration
            import re
            dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", err_text)
            if dur_match:
                hours, mins, secs = dur_match.groups()
                out["duration"] = float(hours) * 3600 + float(mins) * 60 + float(secs)

            # Extract resolution
            res_match = re.search(r"(\d{3,5})x(\d{3,5})", err_text)
            if res_match:
                out["has_video"] = True
                out["width"] = int(res_match.group(1))
                out["height"] = int(res_match.group(2))

            if "Audio:" in err_text:
                out["has_audio"] = True

            return out
        except Exception as exc:
            print(f"[FFMPEG_WARNING] ffmpeg execution failed: {exc}", flush=True)
            return out
