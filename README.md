# codesnap

[![CI](https://github.com/aswin402/codesnap/actions/workflows/ci.yml/badge.svg)](https://github.com/aswin402/codesnap/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/aswin402/codesnap)](https://github.com/aswin402/codesnap/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: >=3.10](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Offline code extractor for Ubuntu (Wayland / GNOME). Press a hotkey, draw a box around
any code on screen — YouTube video, tutorial, PDF, IDE screenshot — and the cleaned, formatted
code is instantly placed on your clipboard.

## Features

- **Instant Capture**: Crosshair selection via `slurp` and `grim` (Wayland native).
- **Dark Mode Auto-Detection**: Automatically detects dark IDE themes and inverts polarity for maximum OCR clarity.
- **Accurate Code OCR**: Tesseract engine optimized for uniform code blocks (`--psm 6`).
- **Safe Character Normalization**: Repairs OCR confusion (`det` $\rightarrow$ `def`, stray margin pipes) without corrupting numbers or identifiers like `utf8` or `col0`.
- **Lightning-Fast Formatting**: Automatically formats Python code using **Ruff** (written in Rust).
- **11+ Supported Languages**: Auto-detects Python, JavaScript, TypeScript, Bash, Rust, Go, C, C++, Java, SQL, HTML, and CSS.
- **Offline & Private**: Zero external network requests; runs 100% locally.

## Requirements

- Ubuntu 23.04+ (Wayland / GNOME)
- Python 3.10+
- `uv` (installed automatically by setup script if missing)

## Install

```bash
git clone <this-repo>
cd codesnap
chmod +x setup.sh
./setup.sh
```

Verify the installation:
```bash
codesnap --version
```

## Usage

1. Press **Super + Shift + L**
2. Your cursor becomes a crosshair — click and drag to select the code region (press **Esc** anytime to cancel).
3. Release — codesnap extracts, cleans, and formats the code.
4. A desktop notification confirms: `Python • 12 lines copied`
5. Paste anywhere with **Ctrl+V**

### Advanced Options

```bash
# Review and edit OCR output in $EDITOR before copying
codesnap --interactive

# Enhanced preprocessing for low-resolution or fuzzy screenshots
codesnap --high-quality

# Extract code directly from an existing image file
codesnap /path/to/screenshot.png

# Save extracted code directly to a file
codesnap /path/to/screenshot.png -o output.py

# Print extracted code directly to stdout (useful for pipes)
codesnap /path/to/screenshot.png -c

# Override language auto-detection
codesnap /path/to/screenshot.png -l rust

# Show diagnostic info and system tool health
codesnap --version
```

## How it works

```
Super+Shift+L
     │
     ▼
slurp  ──→  select screen region (Esc cancels cleanly)
     │
     ▼
grim   ──→  screenshot region  →  temporary PNG
     │
     ▼
image  ──→  detect dark mode, invert, upscale, contrast & denoise
     │
     ▼
tesseract ─→ OCR uniform text block (--psm 6)
     │
     ▼
cleaner ──→ fix OCR artifacts (stray margin pipes, split keywords)
     │
     ▼
detect ──→  identify language (Python, TS, JS, Rust, Go, Bash, etc.)
     │
     ▼
format ──→  fast Ruff formatting for Python (passthrough for others)
     │
     ▼
wl-copy ──→ clipboard
     │
     ▼
notify ───→ desktop notification
```

## Project Architecture

```
codesnap/
├── pyproject.toml        — modern build metadata & dependency manifest
├── codesnap.py           — backward-compatible CLI entrypoint
├── setup.sh              — installation & hotkey registration script
├── src/codesnap/
│   ├── __init__.py       — package metadata
│   ├── cli.py            — CLI entrypoint & pipeline orchestration
│   ├── capture.py        — Wayland screen selection & capture
│   ├── image.py          — preprocessing & dark theme polarity inversion
│   ├── ocr.py            — Tesseract OCR pipeline & fallbacks
│   ├── cleaner.py        — AST/token safe character correction
│   ├── languages.py      — multi-language detection patterns
│   ├── formatters.py     — fast Ruff code formatter integration
│   ├── clipboard.py      — wl-copy / xclip & notification handlers
│   └── exceptions.py     — typed exceptions
└── tests/
    ├── test_capture.py
    ├── test_cleaner.py
    ├── test_cli.py
    ├── test_formatters.py
    ├── test_image.py
    └── test_languages.py
```

## Development & Testing

Run tests and linting with `uv` and `ruff`:

```bash
# Run unit test suite
uv run pytest

# Run linting
uv run ruff check .

# Run code formatter
uv run ruff format .
```

## Changelog

See [CHANGELOG.md](file:///home/aswin/programming/vscode/myProjects/codesnap/CHANGELOG.md) for version history, bug fixes, and feature notes.

## Uninstall

```bash
rm -rf ~/.local/share/codesnap
rm ~/.local/bin/codesnap
```

Then remove the shortcut in **Settings → Keyboard → Custom Shortcuts**.

### vibe coded by Aswin