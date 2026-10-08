"""Clipboard management and desktop notifications."""

import shutil
import subprocess

from codesnap.exceptions import CodesnapError


def copy_to_clipboard(text: str) -> None:
    """Copy text to Wayland clipboard using wl-copy, falling back to xclip."""
    if shutil.which("wl-copy"):
        try:
            subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
            return
        except Exception as e:
            raise CodesnapError(f"Failed to copy to clipboard with wl-copy: {e}") from e

    if shutil.which("xclip"):
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode("utf-8"),
                check=True,
            )
            return
        except Exception as e:
            raise CodesnapError(f"Failed to copy to clipboard with xclip: {e}") from e

    raise CodesnapError("No clipboard tool found. Please install wl-clipboard (or xclip).")


def send_notification(title: str, body: str, icon: str = "dialog-information") -> None:
    """Display a desktop notification via notify-send."""
    if not shutil.which("notify-send"):
        return

    try:
        subprocess.run(
            ["notify-send", "-i", icon, "-t", "4000", title, body],
            check=False,
            capture_output=True,
        )
    except Exception:
        pass
