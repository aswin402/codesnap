"""Code formatting for extracted snippets across multiple languages.

Supported formatters (invoked on zero-config fallback):
- Python: ruff (bundled in environment)
- Rust: rustfmt
- Go: gofmt
- JavaScript/TypeScript/JSON: biome or prettier
- Bash: shfmt
- C/C++: clang-format
- HTML/CSS: prettier or biome
"""

import shutil
import subprocess
import sys
from pathlib import Path


def _find_ruff() -> str | None:
    """Locate the ruff executable."""
    venv_ruff = Path(sys.prefix) / "bin" / "ruff"
    if venv_ruff.is_file():
        return str(venv_ruff)
    return shutil.which("ruff")


def _run_formatter(cmd: list[str], code: str) -> str | None:
    """Execute external formatter CLI over stdin and return stdout if successful."""
    try:
        proc = subprocess.run(
            cmd,
            input=code,
            text=True,
            capture_output=True,
            timeout=4,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass
    return None


def _format_python(code: str) -> str:
    ruff_path = _find_ruff()
    if not ruff_path:
        return code
    formatted = _run_formatter([ruff_path, "format", "--stdin-filename", "snippet.py", "-"], code)
    return formatted if formatted is not None else code


def _format_rust(code: str) -> str:
    rustfmt = shutil.which("rustfmt")
    if not rustfmt:
        return code
    formatted = _run_formatter([rustfmt, "--emit", "stdout"], code)
    return formatted if formatted is not None else code


def _format_go(code: str) -> str:
    gofmt = shutil.which("gofmt")
    if not gofmt:
        return code
    formatted = _run_formatter([gofmt], code)
    return formatted if formatted is not None else code


def _format_js_ts(code: str, lang: str) -> str:
    ext = "ts" if "type" in lang else ("json" if lang == "json" else "js")
    biome = shutil.which("biome")
    if biome:
        formatted = _run_formatter([biome, "format", f"--stdin-file-path=snippet.{ext}"], code)
        if formatted:
            return formatted
    prettier = shutil.which("prettier")
    if prettier:
        formatted = _run_formatter([prettier, f"--stdin-filepath=snippet.{ext}"], code)
        if formatted:
            return formatted
    return code


def _format_bash(code: str) -> str:
    shfmt = shutil.which("shfmt")
    if not shfmt:
        return code
    formatted = _run_formatter([shfmt, "-"], code)
    return formatted if formatted is not None else code


def _format_c_cpp(code: str, lang: str) -> str:
    clang_format = shutil.which("clang-format")
    if not clang_format:
        return code
    ext = "cpp" if ("++" in lang or "cpp" in lang) else "c"
    formatted = _run_formatter([clang_format, f"--assume-filename=snippet.{ext}"], code)
    return formatted if formatted is not None else code


def _format_html_css(code: str, lang: str) -> str:
    ext = "html" if lang == "html" else "css"
    prettier = shutil.which("prettier")
    if prettier:
        formatted = _run_formatter([prettier, f"--stdin-filepath=snippet.{ext}"], code)
        if formatted:
            return formatted
    if ext == "css":
        biome = shutil.which("biome")
        if biome:
            formatted = _run_formatter([biome, "format", f"--stdin-file-path=snippet.{ext}"], code)
            if formatted:
                return formatted
    return code


def format_code(code: str, lang: str) -> str:
    """Format code snippet if a supported formatter for the detected language is available."""
    if not code or not lang:
        return code

    lang = lang.lower().strip()
    if lang == "python":
        return _format_python(code)
    if lang == "rust":
        return _format_rust(code)
    if lang == "go":
        return _format_go(code)
    if lang in ("javascript", "typescript", "json"):
        return _format_js_ts(code, lang)
    if lang in ("bash", "sh", "shell"):
        return _format_bash(code)
    if lang in ("c", "cpp", "c++"):
        return _format_c_cpp(code, lang)
    if lang in ("html", "css"):
        return _format_html_css(code, lang)

    return code
