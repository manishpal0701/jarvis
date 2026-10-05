"""
video_editing/export/export_schema.py
Strict Export Configuration Schema & Path Safety Validator for Phase 4.
Validates formats, codecs, resolutions, frame rates, and enforces absolute output path safety.
"""

import os
import re

ALLOWED_FORMATS = {"mp4"}
ALLOWED_CODECS = {"h264"}


def validate_export_config(config_dict: dict) -> tuple[bool, dict]:
    """
    Validate an export configuration dict.
    Returns (is_valid, response_dict).
    """
    if not isinstance(config_dict, dict):
        return False, _err("INVALID_FORMAT", "Export configuration must be a JSON object.")

    # Top-level required keys
    req_keys = ["format", "codec", "resolution", "fps", "output_path"]
    for k in req_keys:
        if k not in config_dict:
            return False, _err("MISSING_FIELD", f"Export config missing required field '{k}'.")

    # Format check
    fmt = str(config_dict.get("format", "")).lower()
    if fmt not in ALLOWED_FORMATS:
        return False, _err("INVALID_FORMAT", f"Export format '{fmt}' is not supported. Must be 'mp4'.")

    # Codec check
    codec = str(config_dict.get("codec", "")).lower()
    if codec not in ALLOWED_CODECS:
        return False, _err("INVALID_CODEC", f"Export codec '{codec}' is not supported. Must be 'h264'.")

    # Resolution check (WIDTHxHEIGHT)
    res_str = str(config_dict.get("resolution", ""))
    res_match = re.match(r"^(\d+)x(\d+)$", res_str)
    if not res_match:
        return False, _err("INVALID_RESOLUTION", f"resolution must be in 'WIDTHxHEIGHT' format, got '{res_str}'.")
    width, height = int(res_match.group(1)), int(res_match.group(2))
    if width <= 0 or height <= 0:
        return False, _err("INVALID_RESOLUTION", f"Width and height must be > 0, got {width}x{height}.")

    # FPS check
    fps = config_dict.get("fps")
    if not isinstance(fps, (int, float)) or fps <= 0:
        return False, _err("INVALID_FPS", f"fps must be a positive number, got {fps}.")

    # Output Path Safety Checks
    out_path = config_dict.get("output_path")
    valid_path, path_err = validate_output_path(out_path, format_ext=fmt, overwrite=config_dict.get("overwrite", False))
    if not valid_path:
        return False, path_err

    return True, {"success": True, "error": None}


def validate_output_path(out_path: str, format_ext: str = "mp4", overwrite: bool = False) -> tuple[bool, dict]:
    """
    Strict path safety validator. Rejects relative paths, path traversal, and invalid extensions.
    """
    if not out_path or not isinstance(out_path, str):
        return False, _err("INVALID_OUTPUT_PATH", "output_path must be a non-empty string.")

    norm_path = os.path.normpath(out_path)

    # Check absolute path requirement
    if not os.path.isabs(norm_path) and not re.match(r"^[a-zA-Z]:[\\/]", out_path):
        return False, _err("RELATIVE_PATH_REJECTED", f"output_path must be an absolute path: '{out_path}'.")

    # Check path traversal attempts (.. in original path)
    if ".." in out_path.replace("\\", "/").split("/"):
        return False, _err("PATH_TRAVERSAL_REJECTED", f"Path traversal ('..') is strictly rejected: '{out_path}'.")

    # Extension check
    expected_ext = f".{format_ext.lower()}"
    if not norm_path.lower().endswith(expected_ext):
        return False, _err("INVALID_EXTENSION", f"output_path extension must match '.{format_ext}', got '{out_path}'.")

    # Overwrite check
    if not overwrite and os.path.isfile(norm_path):
        return False, _err("FILE_ALREADY_EXISTS", f"Output file already exists: '{norm_path}'. Pass overwrite=True to replace.")

    # Parent directory check/creation
    parent_dir = os.path.dirname(norm_path)
    if parent_dir and not os.path.isdir(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception as e:
            return False, _err("CANNOT_CREATE_DIRECTORY", f"Could not create parent directory '{parent_dir}': {e}")

    return True, {"success": True, "error": None}


def _err(code: str, message: str) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
