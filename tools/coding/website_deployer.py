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

        # 1. Execute npm install if node_modules is missing
        if not os.path.exists(node_modules):
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
