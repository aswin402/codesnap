"""Multi-language detection for extracted code snippets."""

import re

# Weighted regex patterns for language identification
LANGUAGE_PATTERNS: dict[str, list[tuple[str, int]]] = {
    "python": [
        (r"^\s*def\s+[a-zA-Z_]\w*\s*\(.*?\)\s*:", 4),
        (r"^\s*class\s+[a-zA-Z_]\w*(\(.*?\))?:", 3),
        (r"^\s*(from|import)\s+[a-zA-Z_]", 3),
        (r"\bself\b", 2),
        (r"\bprint\(", 2),
        (r"\bNone\b", 1),
        (r"\belif\b", 3),
    ],
    "typescript": [
        (r"\binterface\s+[A-Z]\w*", 5),
        (r"\btype\s+[A-Z]\w*\s*=", 4),
        (r":\s*(string|number|boolean|any|void|unknown|never)\b", 4),
        (r"\bas\s+[A-Z]\w*", 2),
    ],
    "javascript": [
        (r"\b(const|let|var)\s+[a-zA-Z_]", 3),
        (r"=>", 2),
        (r"\bconsole\.(log|error|warn)\(", 3),
        (r"\bfunction\s+[a-zA-Z_]\w*\s*\(", 3),
        (r"\bdocument\.(getElementById|querySelector)", 4),
        (r"\bexport\s+(default|const|function)\b", 3),
    ],
    "rust": [
        (r"\bfn\s+[a-zA-Z_]\w*\s*\(", 4),
        (r"\blet\s+mut\s+", 4),
        (r"\bimpl(\s+<.*?>)?\s+", 4),
        (r"\bprintln!\(", 4),
        (r"->\s*Result<", 4),
        (r"\bOption<", 3),
        (r"\bpub\s+(fn|struct|enum|trait)\b", 4),
    ],
    "go": [
        (r"\bpackage\s+[a-zA-Z_]", 5),
        (r"\bfunc\s+[a-zA-Z_]\w*\s*\(", 4),
        (r"\bfmt\.(Println|Printf|Sprintf)\(", 4),
        (r":=\s*", 3),
        (r"\bimport\s+\(", 3),
    ],
    "bash": [
        (r"^#!\s*/bin/(bash|sh|zsh)", 5),
        (r"\becho\s+[\"']", 3),
        (r"\bexport\s+[A-Z_][A-Z0-9_]*=", 4),
        (r"\b(sudo|apt-get|systemctl|chmod)\b", 3),
        (r"\bif\s+\[\[?.*?\]\]?;\s*then", 4),
    ],
    "sql": [
        (r"\bSELECT\b.*?\bFROM\b", 5),
        (r"\bINSERT\s+INTO\b", 5),
        (r"\bCREATE\s+TABLE\b", 5),
        (r"\bWHERE\b.*?\b(AND|OR|=|>|<|IN|LIKE)\b", 3),
        (r"\bORDER\s+BY\b", 4),
        (r"\bGROUP\s+BY\b", 4),
    ],
    "html": [
        (r"<!DOCTYPE\s+html>", 5),
        (r"<\s*html\b.*?>", 4),
        (r"<\s*(head|body|div|span|p|a|button|input|script|style)\b.*?>", 3),
        (r"<\s*/\s*(div|span|p|a|button|html|body)\s*>", 3),
    ],
    "css": [
        (r"\{\s*[\w\-]+\s*:\s*[^;]+;", 3),
        (r"@(media|keyframes|import)\b", 4),
        (r"\b(margin|padding|background|color|display|flex|grid)\s*:\s*", 3),
    ],
    "java": [
        (r"\bpublic\s+class\s+[A-Z]\w*", 4),
        (r"\bpublic\s+static\s+void\s+main\b", 5),
        (r"\bSystem\.out\.println\(", 4),
    ],
    "c": [
        (r"#include\s+<stdio\.h>", 5),
        (r"\bint\s+main\s*\(\s*(int\s+argc|void)?\s*\)", 4),
        (r"\bprintf\(", 3),
    ],
}


def detect_language(code: str) -> str:
    """Analyze code snippet and return the most likely language."""
    if not code or not code.strip():
        return "text"

    scores: dict[str, int] = {}
    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = 0
        for pattern, weight in patterns:
            matches = len(re.findall(pattern, code, re.MULTILINE | re.IGNORECASE))
            score += matches * weight
        if score > 0:
            scores[lang] = score

    if not scores:
        return "text"

    # TypeScript takes precedence over JavaScript if TS-specific tokens are present
    if scores.get("typescript", 0) > 0 and scores.get("javascript", 0) > 0:
        if scores["typescript"] >= scores["javascript"]:
            return "typescript"

    return max(scores, key=scores.get)
