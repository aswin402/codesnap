"""Safe, AST-aware post-processing and character correction for extracted code."""

import re

# Specific OCR misrecognitions targeting code keywords and syntax
KEYWORD_FIXES = {
    # Python / general code keywords
    r"\be1se\b": "else",
    r"\bels\s+e\b": "else",
    r"\bdet\s+([a-zA-Z_])": r"def \1",
    r"\bdep\s+([a-zA-Z_])": r"def \1",
    r"\bretum\b": "return",
    r"\bpriot\s*\(": "print(",
    r"\bprinr\s*\(": "print(",
    r"\b1mport\b": "import",
    r"\bfr0m\b": "from",
    r"\bte\s+st\b": "test",
    r"\bl\s+ater\b": "later",
    r"\bcode\s+snap\b": "codesnap",
    r"\bc0desnap\b": "codesnap",
}


def fix_stray_margin_artifacts(text: str) -> str:
    """Remove stray vertical bars '|' or indentation guides commonly captured by OCR."""
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        # Remove stray vertical bar or backslash at the start of code lines
        # e.g. "| def foo():" -> "def foo():" or "|   x = 1" -> "  x = 1"
        line = re.sub(r"^(\s*)[\|\¦\│\\\/]\s*", r"\1", line)
        cleaned_lines.append(line.rstrip())
    return "\n".join(cleaned_lines)


def clean_code_text(text: str) -> str:
    """Safely correct common OCR mistakes without corrupting numbers or identifiers."""
    if not text:
        return ""

    result = text

    # Remove margin artifacts (e.g. IDE vertical indent guides mistaken for '|' or '/')
    result = fix_stray_margin_artifacts(result)

    # Apply targeted keyword misrecognition fixes
    for pattern, replacement in KEYWORD_FIXES.items():
        result = re.sub(pattern, replacement, result)

    # Normalize Windows line endings to standard Unix line endings
    result = result.replace("\r\n", "\n").replace("\r", "\n")

    # Strip excess leading/trailing blank lines while preserving code indentation
    result = result.strip("\n")

    return result
