"""Code formatting for extracted snippets using Ruff."""

import shutil
import subprocess
import sys
from pathlib import Path


def _find_ruff() -> str | None:
    """Locate the ruff executable."""
    # Check current python environment
    venv_ruff = Path(sys.prefix) / "bin" / "ruff"
    if venv_ruff.is_file():
        return str(venv_ruff)

    # Check system PATH
    return shutil.which("ruff")


def format_code(code: str, lang: str) -> str:
    """Format code snippet if a supported fast formatter (ruff) is available."""
    if not code or lang != "python":
        return code

    ruff_path = _find_ruff()
    if not ruff_path:
        return code

    try:
        proc = subprocess.run(
            [ruff_path, "format", "--stdin-filename", "snippet.py", "-"],
            input=code,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass

    return code
