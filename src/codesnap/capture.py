"""Wayland and GNOME screen selection and capture utilities."""

import os
import shutil
import subprocess

from codesnap.exceptions import (
    CaptureCancelledError,
    CaptureFailedError,
    DependencyMissingError,
)

REQUIRED_SYSTEM_TOOLS = ["grim", "slurp", "wl-copy", "tesseract"]


def check_system_dependencies() -> None:
    """Verify all external system binaries exist in PATH."""
    missing = [tool for tool in REQUIRED_SYSTEM_TOOLS if not shutil.which(tool)]
    if missing:
        raise DependencyMissingError(
            f"Missing required tools: {', '.join(missing)}\n"
            "Please install them via: sudo apt install grim slurp wl-clipboard tesseract-ocr"
        )


def capture_screen_region(output_path: str) -> None:
    """Trigger interactive screen region selection and capture to output_path.

    Raises:
        CaptureCancelledError: If the user presses Esc or cancels selection.
        CaptureFailedError: If the screenshot capture command fails.
    """
    check_system_dependencies()

    # Step 1: Run slurp for interactive area selection
    try:
        slurp_proc = subprocess.run(
            ["slurp"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except Exception as e:
        raise CaptureFailedError(f"Failed to invoke slurp: {e}") from e

    # User cancelled (e.g. pressed Escape or clicked outside)
    if slurp_proc.returncode != 0 or not slurp_proc.stdout.strip():
        raise CaptureCancelledError("Screen selection cancelled by user.")

    geometry = slurp_proc.stdout.strip()

    # Step 2: Capture region with grim
    try:
        grim_proc = subprocess.run(
            ["grim", "-g", geometry, output_path],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as e:
        raise CaptureFailedError(f"Failed to invoke grim: {e}") from e

    if (
        grim_proc.returncode != 0
        or not os.path.exists(output_path)
        or os.path.getsize(output_path) == 0
    ):
        raise CaptureFailedError("Failed to save screenshot image.")
