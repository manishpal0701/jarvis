import os
import shutil
import json
import datetime
from typing import Tuple, Dict, Any
from config import BASE_DIR, DATA_DIR

class TemplateCache:
    """
    Dependency Cache Layer for Turbo Website Builder v2.
    Maintains a pre-warmed React+Vite template cache to eliminate node_modules installation overhead.
    """

    CACHE_DIR = os.path.join(DATA_DIR, "template_cache")

    @classmethod
    def ensure_cache_initialized(cls) -> bool:
        """Initializes pre-warmed template cache in data/template_cache if missing."""
        if not os.path.exists(cls.CACHE_DIR):
            os.makedirs(cls.CACHE_DIR, exist_ok=True)

        package_json_path = os.path.join(cls.CACHE_DIR, "package.json")
        if not os.path.exists(package_json_path):
            from tools.coding.website_project_templates import WebsiteProjectTemplates
            pkg_content = WebsiteProjectTemplates.generate_package_json("Base Template", "template-cache")
            with open(package_json_path, "w", encoding="utf-8") as f:
                f.write(pkg_content)
            with open(os.path.join(cls.CACHE_DIR, "tsconfig.json"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_tsconfig())
            with open(os.path.join(cls.CACHE_DIR, "vite.config.ts"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_vite_config())

        return True

    @classmethod
    def prepare_project_directory(cls, project_dir: str, package_json_content: str = None) -> Tuple[bool, str]:
        """
        Copies cached node_modules and configuration into project_dir.
        Returns (reused_dependencies: bool, status: str).
        """
        cls.ensure_cache_initialized()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        os.makedirs(project_dir, exist_ok=True)

        cached_node_modules = os.path.join(cls.CACHE_DIR, "node_modules")
        target_node_modules = os.path.join(project_dir, "node_modules")

        # Copy cached node_modules if present
        if os.path.exists(cached_node_modules) and not os.path.exists(target_node_modules):
            try:
                shutil.copytree(cached_node_modules, target_node_modules, symlinks=True)
            except Exception as e:
                print(f"[TemplateCache Warning]: Failed to copy node_modules: {e}")

        # Copy lock file and config files
        for f_name in ["package-lock.json", "tsconfig.json", "vite.config.ts"]:
            src_f = os.path.join(cls.CACHE_DIR, f_name)
            dst_f = os.path.join(project_dir, f_name)
            if os.path.exists(src_f) and not os.path.exists(dst_f):
                try:
                    shutil.copy2(src_f, dst_f)
                except Exception:
                    pass

        # Check dependency matching
        dependencies_match = cls._are_dependencies_matching(cls.CACHE_DIR, project_dir, package_json_content)

        if os.path.exists(target_node_modules) and dependencies_match:
            print(f"[TEMPLATE_CACHE_HIT] project_dir=\"{project_dir}\" timestamp={now}", flush=True)
            print(f"[DEPENDENCY_REUSED] project_dir=\"{project_dir}\" timestamp={now}", flush=True)
            return True, "CACHE_HIT"
        else:
            print(f"[TEMPLATE_CACHE_MISS] project_dir=\"{project_dir}\" timestamp={now}", flush=True)
            return False, "CACHE_MISS"

    @classmethod
    def _are_dependencies_matching(cls, cache_dir: str, project_dir: str, new_pkg_json: str = None) -> bool:
        try:
            cache_pkg_path = os.path.join(cache_dir, "package.json")
            if not os.path.exists(cache_pkg_path):
                return False

            with open(cache_pkg_path, "r", encoding="utf-8") as f:
                cache_pkg = json.load(f)

            if new_pkg_json:
                new_pkg = json.loads(new_pkg_json)
            else:
                proj_pkg_path = os.path.join(project_dir, "package.json")
                if not os.path.exists(proj_pkg_path):
                    return True
                with open(proj_pkg_path, "r", encoding="utf-8") as f:
                    new_pkg = json.load(f)

            cache_deps = cache_pkg.get("dependencies", {})
            new_deps = new_pkg.get("dependencies", {})

            # Check if all new required dependencies are present in cache
            for k in new_deps:
                if k not in cache_deps:
                    return False
            return True
        except Exception:
            return False

    @classmethod
    def update_template_cache(cls, source_dir: str):
        """Updates the template cache with installed node_modules from a successful build."""
        try:
            src_nm = os.path.join(source_dir, "node_modules")
            if os.path.exists(src_nm):
                cls.ensure_cache_initialized()
                dst_nm = os.path.join(cls.CACHE_DIR, "node_modules")
                if os.path.exists(dst_nm):
                    shutil.rmtree(dst_nm, ignore_errors=True)
                shutil.copytree(src_nm, dst_nm, symlinks=True)
                # Also sync lock file
                src_lock = os.path.join(source_dir, "package-lock.json")
                if os.path.exists(src_lock):
                    shutil.copy2(src_lock, os.path.join(cls.CACHE_DIR, "package-lock.json"))
        except Exception as e:
            print(f"[TemplateCache Notice]: Cache update notice: {e}")
