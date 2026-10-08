"""Desktop capture backend: GNOME Shell and wlroots (Wayland) screen selection."""

import os
import shutil
import subprocess

from codesnap.exceptions import (
    CaptureCancelledError,
    CaptureFailedError,
    DependencyMissingError,
)

REQUIRED_SYSTEM_TOOLS = ["gnome-screenshot", "grim", "slurp", "wl-copy", "tesseract"]


def is_gnome() -> bool:
    """Check if the current desktop environment is GNOME."""
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP") or "").lower()
    session = (os.environ.get("DESKTOP_SESSION") or "").lower()
    return "gnome" in desktop or "gnome" in session or "ubuntu" in desktop


def check_system_dependencies() -> None:
    """Verify that required screen capture, OCR, and clipboard tools exist in PATH."""
    has_capture_tool = bool(shutil.which("gnome-screenshot")) or bool(
        shutil.which("slurp") and shutil.which("grim")
    )
    if not has_capture_tool:
        raise DependencyMissingError(
            "Missing screen capture tool. Please install gnome-screenshot (for GNOME) "
            "or slurp & grim (for Sway/Hyprland):\n"
            "  sudo apt install gnome-screenshot  # or: sudo apt install grim slurp"
        )

    if not shutil.which("tesseract"):
        raise DependencyMissingError(
            "Missing OCR tool: tesseract. Please install it via:\n"
            "  sudo apt install tesseract-ocr"
        )

    if not (shutil.which("wl-copy") or shutil.which("xclip")):
        raise DependencyMissingError(
            "Missing clipboard tool. Please install wl-clipboard (or xclip):\n"
            "  sudo apt install wl-clipboard"
        )


def capture_with_gnome_screenshot(output_path: str) -> bool:
    """Capture screen area using gnome-screenshot -a (standard for GNOME Wayland/X11)."""
    if not shutil.which("gnome-screenshot"):
        return False

    try:
        proc = subprocess.run(
            ["gnome-screenshot", "-a", "-f", output_path],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if (
            proc.returncode == 0
            and os.path.exists(output_path)
            and os.path.getsize(output_path) > 0
        ):
            return True
        # If user pressed Esc or cancelled, no file is written
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise CaptureCancelledError("Screen selection cancelled by user.")
    except CaptureCancelledError:
        raise
    except Exception:
        return False

    return False


def capture_with_slurp(output_path: str) -> bool:
    """Capture screen area using slurp + grim (standard for wlroots compositors)."""
    if not (shutil.which("slurp") and shutil.which("grim")):
        return False

    try:
        slurp_proc = subprocess.run(
            ["slurp"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except Exception:
        return False

    # Detect compositor protocol error (e.g. GNOME Mutter unsupported layer-shell)
    stderr = (slurp_proc.stderr or "").lower()
    if "doesn't support" in stderr or "failed to create layer" in stderr:
        return False

    # User cancelled selection (e.g. pressed Escape)
    if slurp_proc.returncode != 0 or not slurp_proc.stdout.strip():
        raise CaptureCancelledError("Screen selection cancelled by user.")

    geometry = slurp_proc.stdout.strip()

    try:
        grim_proc = subprocess.run(
            ["grim", "-g", geometry, output_path],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return (
            grim_proc.returncode == 0
            and os.path.exists(output_path)
            and os.path.getsize(output_path) > 0
        )
    except Exception:
        return False


def capture_screen_region(output_path: str) -> None:
    """Capture screen region using the optimal capture backend for the active environment.

    Raises:
        CaptureCancelledError: If user cancels area selection (e.g. Esc).
        CaptureFailedError: If area capture fails.
    """
    check_system_dependencies()

    # On GNOME, prioritize gnome-screenshot because slurp lacks layer-shell support on Mutter
    if is_gnome() and shutil.which("gnome-screenshot"):
        if capture_with_gnome_screenshot(output_path):
            return

    # Try slurp + grim (Sway, Hyprland, Wayfire, etc.)
    if shutil.which("slurp") and shutil.which("grim"):
        if capture_with_slurp(output_path):
            return

    # Fallback to gnome-screenshot if slurp was unsupported on this session
    if shutil.which("gnome-screenshot"):
        if capture_with_gnome_screenshot(output_path):
            return

    raise CaptureFailedError(
        "Screen capture failed. Ensure gnome-screenshot or slurp+grim is installed."
    )
