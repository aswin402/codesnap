# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.4] - 2026-10-10

### Added
- **Multi-Language Snippet Formatting**: Extended the formatter engine beyond Python (`ruff`) to natively support Rust (`rustfmt`), Go (`gofmt`), JavaScript/TypeScript/JSON (`biome` / `prettier`), Bash (`shfmt`), C/C++ (`clang-format`), and HTML/CSS (`prettier` / `biome`).
- **Zero-Dependency Graceful Fallback**: If an external formatter tool is not installed on the system, `codesnap` automatically preserves normalized code without failing or adding latency.
- **Automated GitHub Releases & PyPI Publishing CI**: Added `.github/workflows/release.yml` triggered on `v*` tags to compile wheel and sdist distributions via `uv build`, automatically publish GitHub Releases with release notes, and publish to PyPI.
- **Expanded Formatter Test Suite**: Added 9 new unit tests covering multi-language formatting paths, mock tool executions, and timeout resilience (total 46 tests).

## [2.4.3] - 2026-10-10

### Added
- **One-Liner Install Support**: Made `setup.sh` pipe-friendly for direct `curl -sSL https://raw.githubusercontent.com/aswin402/codesnap/main/setup.sh | bash` installations and added official documentation for `uv tool install`.
- **Automatic Stale Dependency Cleanup**: Enhanced `localupdate.sh` to purge `numpy` from existing virtual environments, immediately reclaiming ~35MB of disk space on upgraded systems.

### Changed
- **Pure-Pillow Image Preprocessing**: Replaced `numpy` with Pillow's C-accelerated `ImageStat.Stat` for background luminance detection and fast 256-entry lookup table (`point LUT`) for image binarization, halving test suite execution time and reducing idle memory consumption.

### Removed
- **Removed `numpy` Dependency**: Dropped `numpy` requirement from `pyproject.toml`, trimming the distribution and virtual environment size by over 35MB.

## [2.4.2] - 2026-10-10

### Added
- **Native Wayland XDG Desktop Portal Capture**: Integrated `org.freedesktop.portal.Screenshot` via `jeepney` pure-Python D-Bus client, bringing seamless interactive screen selection and capture to GNOME 40+ / GNOME 50 (Ubuntu 24.04/26.04) on Wayland without relying on unsupported protocols.
- **Fail-Safe Launcher Logging**: Added automated error and crash diagnostics logging to `~/.cache/codesnap/codesnap.log` when invoked via GNOME custom keyboard shortcut (`Super+Shift+L`) or background desktop launcher.
- **Portal Fallback Cascade**: Implemented robust backend selector prioritizing XDG Desktop Portal on GNOME Wayland, `slurp`/`grim` on wlroots compositors (Sway, Hyprland), and `gnome-screenshot` on legacy X11 sessions.
- **Expanded Test Suite**: Added 13 new unit tests covering D-Bus portal response decoding, URI parsing, user cancellation handling, backend detection, and fallback mechanics.

### Fixed
- **GNOME Wayland Hang & Cancellation**: Resolved issue where GNOME Mutter Wayland sessions aborted screenshot selection or hung in fallback modes due to lack of `zwlr_layer_shell_v1` support in GNOME Shell.

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
- **Fast In-Place Updater Script**: Added `localupdate.sh` to allow users with existing installations to upgrade their local CLI binary, virtual environment, and packages in-place without re-running system package managers.

### Fixed
- **Pillow Filter Crash**: Fixed `ValueError: bad filter size` by updating `MedianFilter(size=2)` to a valid odd integer (`size=3`), resolving an exception that was silently aborting image preprocessing on every run.
- **Character Corruption**: Replaced dangerous line-wide substring replacements (which previously turned numbers like `100` into `1oo` or variables like `col0` into `colo`) with safe, token-level OCR normalization.
- **Cancelation Process Hang**: Fixed issue where pressing `Esc` during screen selection fell through to terminal coordinate input and hung the background desktop process.
- **GNOME Wayland Screen Selection Immediate Cancellation**: Fixed bug where `slurp` failed immediately on GNOME Mutter with `compositor doesn't support zwlr_layer_shell_v1`, causing false `Selection cancelled` notifications. Implemented dual-backend architecture prioritizing `gnome-screenshot -a` on GNOME and `slurp`/`grim` on wlroots compositors (Sway/Hyprland).
- **Missing Dependency Check**: Added check for `tesseract` binary in `check_system_dependencies()` to provide actionable installation instructions if missing.
- **Namespace Import Collision**: Fixed import resolution in root `codesnap.py` so it cleanly proxies to `src/codesnap/cli.py` without package name collision.

### Removed
- Removed bloated and unused dependencies (`scikit-image`, `scipy`, `build-essential`, `libtesseract-dev`) from `setup.sh` and codebase, saving over 100MB of overhead.
- Removed unused and duplicate dictionary keys and no-op replacements in OCR character cleaner.
