import os
import subprocess
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

class DeploymentMode(Enum):
    LOCAL_PREVIEW = "local_preview"
    PUBLIC_DEPLOYMENT = "public_deployment"

@dataclass
class DeploymentResult:
    success: bool
    mode: str = DeploymentMode.LOCAL_PREVIEW.value
    preview_url: str = ""
    public_url: str = ""
    provider: str = "LocalWebsiteServer"
    message: str = ""
    error: str = ""

class WebsiteDeployer(ABC):
    """
    Abstract interface for website deployment providers (e.g. Netlify, Vercel, GitHub Pages).
    Separates LOCAL_PREVIEW (http://127.0.0.1:<port>) from PUBLIC_DEPLOYMENT (https://...).
    """

    @abstractmethod
    def deploy(self, project_path: str) -> DeploymentResult:
        pass

class LocalPreviewDeployer(WebsiteDeployer):
    """
    Local Preview Deployer.
    Spins up LocalWebsiteServer and opens local browser preview without public upload.
    """
    def deploy(self, project_path: str) -> DeploymentResult:
        from tools.coding.local_website_server import LocalWebsiteServer
        server = LocalWebsiteServer.get_instance()
        url, port = server.start_preview(project_path, open_browser=True)
        return DeploymentResult(
            success=True,
            mode=DeploymentMode.LOCAL_PREVIEW.value,
            preview_url=url,
            provider="LocalWebsiteServer",
            message=f"Local preview ready: {url}"
        )

    @classmethod
    def execute_incremental_build(cls, project_dir: str, modified_files: list = None, timeout: int = 300) -> tuple[bool, str]:
        """
        Incremental Build Gate for Turbo Website Builder v2.
        Checks if project files or dist/ index.html artifact are unchanged.
        If unchanged, skips full compilation; otherwise executes production build.
        """
        import datetime
        import time
        import json
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[INCREMENTAL_BUILD] project_dir=\"{project_dir}\" timestamp={now}", flush=True)

        dist_index = os.path.join(project_dir, "dist", "index.html")
        build_cache_file = os.path.join(project_dir, ".build_cache.json")

        src_dir = os.path.join(project_dir, "src")
        latest_src_mtime = 0.0
        if os.path.exists(src_dir):
            for root, _, files in os.walk(src_dir):
                for file in files:
                    fp = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(fp)
                        if mtime > latest_src_mtime:
                            latest_src_mtime = mtime
                    except Exception:
                        pass

        dist_mtime = os.path.getmtime(dist_index) if os.path.exists(dist_index) else 0.0

        if os.path.exists(dist_index) and dist_mtime >= latest_src_mtime and (not modified_files or len(modified_files) == 0):
            print(f"[BUILD_SKIPPED] dist/ index.html up to date timestamp={now}", flush=True)
            return True, ""

        print(f"[BUILD_REQUIRED] executing production build timestamp={now}", flush=True)
        is_ok, err = cls.execute_production_build(project_dir, timeout=timeout)

        if is_ok:
            try:
                with open(build_cache_file, "w", encoding="utf-8") as f:
                    json.dump({"last_build": time.time(), "latest_src_mtime": latest_src_mtime}, f)
            except Exception:
                pass

        return is_ok, err

    @classmethod
    def execute_production_build(cls, project_dir: str, timeout: int = 300) -> tuple[bool, str]:
        """
        Mandatory Real Production Build Gate.
        Executes 'npm install' and 'npm run build' (or npx vite build)
        and verifies that 'dist/index.html' exists on disk along with compiled assets.
        NEVER fabricates fake output files.
        """
        pkg_json = os.path.join(project_dir, "package.json")
        if not os.path.exists(pkg_json):
            # Vanilla static HTML/CSS/JS project (no npm build required)
            return True, ""

        node_modules = os.path.join(project_dir, "node_modules")
        dist_dir = os.path.join(project_dir, "dist")
        dist_index = os.path.join(dist_dir, "index.html")

        # 1. Execute npm install if node_modules or vite package is missing
        vite_pkg = os.path.join(node_modules, "vite")
        if not os.path.exists(node_modules) or not os.path.exists(vite_pkg):
            print(f"[Production Build Gate]: Running 'npm install' in {project_dir} (timeout={timeout}s)...")
            try:
                res_install = subprocess.run(
                    "npm install --no-audit --no-fund --prefer-offline",
                    cwd=project_dir,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                if res_install.returncode != 0:
                    err_msg = res_install.stderr or res_install.stdout or "npm install returned non-zero exit status."
                    print(f"[Production Build Gate Failure]: npm install failed: {err_msg}")
                    return False, f"npm install failed: {err_msg}"
            except subprocess.TimeoutExpired:
                print(f"[Production Build Gate Failure]: npm install timed out after {timeout} seconds.")
                return False, f"npm install timed out after {timeout} seconds."
            except Exception as e:
                print(f"[Production Build Gate Failure]: Exception during npm install: {e}")
                return False, f"Exception during npm install: {e}"

        # 2. Execute npm run build
        print(f"[Production Build Gate]: Running 'npm run build' in {project_dir} (timeout={timeout}s)...")
        try:
            res_build = subprocess.run(
                "npm run build",
                cwd=project_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if res_build.returncode != 0:
                print(f"[Production Build Gate Warning]: npm run build failed, retrying with 'npx vite build'...")
                res_vite = subprocess.run(
                    "npx vite build",
                    cwd=project_dir,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                if res_vite.returncode != 0:
                    err_msg = res_vite.stderr or res_vite.stdout or res_build.stderr or res_build.stdout
                    print(f"[Production Build Gate Failure]: Build process failed: {err_msg}")
                    return False, f"Production build failed: {err_msg}"
        except subprocess.TimeoutExpired:
            print(f"[Production Build Gate Failure]: npm run build timed out after {timeout} seconds.")
            return False, f"Production build timed out after {timeout} seconds."
        except Exception as e:
            print(f"[Production Build Gate Failure]: Exception during npm run build: {e}")
            return False, f"Exception during production build: {e}"

        # 3. Verify dist/index.html artifact exists
        if not os.path.exists(dist_index):
            print(f"[Production Build Gate Failure]: dist/index.html was not generated by the build tool.")
            return False, "Production build failed: dist/index.html was not created."

        # 4. Verify compiled JS/CSS bundle directory
        dist_assets = os.path.join(dist_dir, "assets")
        if os.path.exists(dist_assets):
            assets = os.listdir(dist_assets)
            print(f"[Production Build Gate SUCCESS]: Production build created dist/index.html and {len(assets)} assets in {dist_assets}.")
        else:
            print(f"[Production Build Gate SUCCESS]: Production build created dist/index.html.")

        return True, ""

class VercelDeployer(WebsiteDeployer):
    """
    Permanent Vercel Website Deployer.
    Deploys active production project to Vercel via Vercel CLI (vercel --prod --yes).
    Enforces Vercel CLI installation and authentication gates before executing deployment.
    """

    @classmethod
    def is_vercel_cli_available(cls) -> bool:
        import shutil
        return shutil.which("vercel") is not None

    @classmethod
    def is_vercel_authenticated(cls) -> bool:
        if not cls.is_vercel_cli_available():
            return False
        try:
            res = subprocess.run(
                "vercel whoami",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return res.returncode == 0 and "Error!" not in res.stdout and "Error!" not in res.stderr
        except Exception:
            return False

    def deploy(self, project_path: str) -> DeploymentResult:
        import re
        import requests

        if not os.path.exists(project_path):
            return DeploymentResult(
                success=False,
                mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                provider="vercel",
                error=f"Project directory '{project_path}' does not exist."
            )

        if not self.is_vercel_cli_available():
            return DeploymentResult(
                success=False,
                mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                provider="vercel",
                error="Vercel CLI (vercel) is not installed on system PATH. Install via 'npm i -g vercel'."
            )

        if not self.is_vercel_authenticated():
            return DeploymentResult(
                success=False,
                mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                provider="vercel",
                message="Boss, website deployment ready hai, but Vercel authentication required hai. Please login once via 'vercel login', then say 'Jarvis, isko host karo'.",
                error="Vercel CLI authentication required."
            )

        print(f"[Vercel Deployer]: Deploying production project in {project_path}...")
        try:
            res = subprocess.run(
                "vercel --prod --yes",
                cwd=project_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=180
            )

            stdout_text = res.stdout or ""
            stderr_text = res.stderr or ""
            combined_output = f"{stdout_text}\n{stderr_text}"

            # Extract Vercel public production URL (e.g. https://bella-tavola.vercel.app)
            url_match = re.search(r'https://[a-zA-Z0-9-]+\.vercel\.app', combined_output)
            if not url_match:
                url_match = re.search(r'https://[a-zA-Z0-9-]+\.vercel\.dev', combined_output)

            if res.returncode == 0 and url_match:
                public_url = url_match.group(0)
                # Verify HTTP response from deployed URL
                try:
                    res_http = requests.get(public_url, timeout=10)
                    if res_http.status_code in (200, 301, 302, 304):
                        return DeploymentResult(
                            success=True,
                            mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                            public_url=public_url,
                            provider="vercel",
                            message=f"Done Boss! Website permanently host ho gayi hai. Live link: {public_url}"
                        )
                except Exception:
                    pass

                return DeploymentResult(
                    success=True,
                    mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                    public_url=public_url,
                    provider="vercel",
                    message=f"Done Boss! Website deployed to Vercel: {public_url}"
                )
            else:
                err_msg = combined_output.strip() or "Vercel CLI deployment failed."
                return DeploymentResult(
                    success=False,
                    mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                    provider="vercel",
                    error=f"Vercel deployment failed: {err_msg}"
                )
        except subprocess.TimeoutExpired:
            return DeploymentResult(
                success=False,
                mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                provider="vercel",
                error="Vercel deployment timed out after 180 seconds."
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                mode=DeploymentMode.PUBLIC_DEPLOYMENT.value,
                provider="vercel",
                error=f"Exception during Vercel deployment: {e}"
            )
