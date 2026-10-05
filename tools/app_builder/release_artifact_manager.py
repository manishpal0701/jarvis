"""
tools/app_builder/release_artifact_manager.py
Phase 6 — Release Artifact Discovery & Verification Manager.
Physically discovers, calculates SHA-256 checksums, checks size/integrity, and records build artifacts
for generated Flutter + Node.js application workspaces.
"""
import os
import glob
import hashlib
import datetime
import logging
from typing import Dict, Any, List

logger = logging.getLogger("ReleaseArtifactManager")


class ReleaseArtifactManager:
    """
    Physically discovers and validates build artifacts (APKs, AABs, etc.) in application workspaces.
    """

    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculates the SHA-256 hash of a file on disk."""
        if not file_path or not os.path.exists(file_path):
            return ""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as ex:
            logger.error(f"Failed to calculate SHA-256 for '{file_path}': {ex}")
            return ""

    @classmethod
    def discover_artifacts(cls, workspace_path: str) -> List[Dict[str, Any]]:
        """
        Physically searches the workspace directory for output build artifacts (APKs, AABs).
        Returns a list of structured artifact metadata objects.
        """
        abs_workspace = os.path.abspath(workspace_path)
        artifacts = []

        # Standard Flutter build output locations relative to workspace
        search_specs = [
            {
                "type": "APK_DEBUG",
                "rel_pattern": os.path.join("frontend", "build", "app", "outputs", "flutter-apk", "app-debug.apk")
            },
            {
                "type": "APK_RELEASE",
                "rel_pattern": os.path.join("frontend", "build", "app", "outputs", "flutter-apk", "app-release.apk")
            },
            {
                "type": "APK_GENERIC",
                "rel_pattern": os.path.join("frontend", "build", "app", "outputs", "flutter-apk", "*.apk")
            },
            {
                "type": "AAB_RELEASE",
                "rel_pattern": os.path.join("frontend", "build", "app", "outputs", "bundle", "release", "*.aab")
            }
        ]

        seen_paths = set()

        for spec in search_specs:
            pattern = os.path.join(abs_workspace, spec["rel_pattern"])
            matches = glob.glob(pattern)
            for file_path in matches:
                abs_path = os.path.abspath(file_path)
                if abs_path in seen_paths:
                    continue
                seen_paths.add(abs_path)

                exists = os.path.exists(abs_path) and os.path.isfile(abs_path)
                size_bytes = os.path.getsize(abs_path) if exists else 0
                readable = False
                sha256 = ""
                mtime_str = ""

                if exists:
                    try:
                        mtime = os.path.getmtime(abs_path)
                        mtime_str = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).isoformat()
                        with open(abs_path, "rb") as f:
                            f.read(1)
                        readable = True
                    except Exception:
                        readable = False

                    if size_bytes > 0 and readable:
                        sha256 = cls.calculate_sha256(abs_path)

                verified = bool(exists and size_bytes > 0 and readable and sha256)

                # Artifact state categorization
                state = "APK_CREATED"
                if verified:
                    state = "APK_VERIFIED"

                rel_path = os.path.relpath(abs_path, abs_workspace)

                artifacts.append({
                    "type": spec["type"],
                    "path": abs_path,
                    "relative_path": rel_path,
                    "exists": exists,
                    "size_bytes": size_bytes,
                    "readable": readable,
                    "sha256": sha256,
                    "mtime": mtime_str,
                    "verified": verified,
                    "state": state,
                    "device_install_tested": "BLOCKED"  # Default unless device installation explicitly ran
                })

        logger.info(f"Discovered {len(artifacts)} build artifact(s) in workspace '{abs_workspace}'")
        return artifacts
