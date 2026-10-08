# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.1] - 2026-10-08

### Added
- **Modular Architecture**: Restructured the 510-line monolithic script into clean, reusable modules under `src/codesnap/` (`image`, `cleaner`, `ocr`, `languages`, `formatters`, `capture`, `clipboard`, `cli`, and `exceptions`).
- **Modern Packaging with `uv`**: Configured `pyproject.toml` with `hatchling` build system, clean dependency declarations, and CLI script entrypoint (`codesnap`).
- **Fast Code Formatting with Ruff**: Integrated Rust-based `ruff format` to auto-format extracted Python snippets before copying them to clipboard.
- **Dark Mode Auto-Detection**: Implemented automatic background polarity detection and auto-inversion in `src/codesnap/image.py` so code captured from dark IDE themes is recognized with high accuracy by Tesseract.
- **Expanded Multi-Language Support**: Added high-precision token pattern detection for 11 languages (Python, JavaScript, TypeScript, Bash, Rust, Go, SQL, HTML, CSS, C, and Java).
- **Direct Image File Extraction & Output Routing**: Added optional file path argument (`codesnap [image_path]`), file output flag (`-o`/`--output`), stdout flag (`-c`/`--stdout`), language override (`-l`/`--lang`), and `--no-clipboard`.
- **Comprehensive Test Suite**: Added 24 automated unit tests across `tests/` covering image preprocessing, character correction, language detection, snippet formatting, CLI arguments, file output, and capture error handling.
- **GitHub Actions CI Workflow**: Added automated continuous integration pipeline (`.github/workflows/ci.yml`) running Ruff linting, formatting checks, pytest test suite, and distribution package builds on push and pull requests.

### Fixed
- **Pillow Filter Crash**: Fixed `ValueError: bad filter size` by updating `MedianFilter(size=2)` to a valid odd integer (`size=3`), resolving an exception that was silently aborting image preprocessing on every run.
- **Character Corruption**: Replaced dangerous line-wide substring replacements (which previously turned numbers like `100` into `1oo` or variables like `col0` into `colo`) with safe, token-level OCR normalization.
- **Cancelation Process Hang**: Fixed issue where pressing `Esc` during screen selection fell through to terminal coordinate input and hung the background desktop process.
- **Missing Dependency Check**: Added check for `tesseract` binary in `check_system_dependencies()` to provide actionable installation instructions if missing.
- **Namespace Import Collision**: Fixed import resolution in root `codesnap.py` so it cleanly proxies to `src/codesnap/cli.py` without package name collision.

### Removed
- Removed bloated and unused dependencies (`scikit-image`, `scipy`, `build-essential`, `libtesseract-dev`) from `setup.sh` and codebase, saving over 100MB of overhead.
- Removed unused and duplicate dictionary keys and no-op replacements in OCR character cleaner.
