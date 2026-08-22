import os

class PathValidator:
    """
    Validates file destination paths to prevent path traversal attempts (../, ../../, system paths)
    and ensure all generated code remains strictly inside the designated workspace boundary.
    """

    @staticmethod
    def validate_and_resolve(project_dir: str, relative_path: str) -> str:
        """
        Normalizes and resolves project_dir and relative_path to an absolute path.
        Verifies destination path is inside project_dir. Raises ValueError on path traversal.
        """
        if not project_dir:
            project_dir = os.getcwd()

        project_dir_abs = os.path.abspath(os.path.normpath(project_dir))
        full_path_abs = os.path.abspath(os.path.normpath(os.path.join(project_dir_abs, relative_path)))

        # Check if full_path_abs is equal to or subpath of project_dir_abs
        try:
            common = os.path.commonpath([project_dir_abs, full_path_abs])
            if common != project_dir_abs:
                raise ValueError(
                    f"Path Traversal Violation: Destination '{full_path_abs}' is outside workspace boundary '{project_dir_abs}'"
                )
        except Exception as e:
            if not isinstance(e, ValueError):
                raise ValueError(f"Invalid path traversal attempt for path '{relative_path}': {e}") from e
            raise

        return full_path_abs
