"""Screen region capture backends.

Backend order:
1. XDG Desktop Portal (org.freedesktop.portal.Screenshot) — the supported path on
   GNOME/KDE Wayland. Third-party apps are denied GNOME Shell's private screenshot
   API, so gnome-screenshot and slurp do not work there.
2. slurp + grim — wlroots compositors (Sway, Hyprland, Wayfire).
3. gnome-screenshot -a — X11 sessions only (it hangs in X11-fallback mode on Wayland).
"""

import os
import secrets
import shutil
import subprocess
from urllib.parse import unquote, urlparse

from codesnap.exceptions import (
    CaptureCancelledError,
    CaptureFailedError,
    DependencyMissingError,
)

REQUIRED_SYSTEM_TOOLS = ["grim", "slurp", "gnome-screenshot", "wl-copy", "tesseract"]

PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
PORTAL_TIMEOUT_SECONDS = 120

# Portal Response codes (org.freedesktop.portal.Request::Response)
PORTAL_RESPONSE_SUCCESS = 0
PORTAL_RESPONSE_CANCELLED = 1


def is_x11_session() -> bool:
    """Return True when running under an X11 session."""
    return (os.environ.get("XDG_SESSION_TYPE") or "").lower() == "x11"


def check_system_dependencies() -> None:
    """Verify OCR and clipboard tools exist. Capture backends are probed at capture time."""
    if not shutil.which("tesseract"):
        raise DependencyMissingError(
            "Missing OCR tool: tesseract. Please install it via:\n  sudo apt install tesseract-ocr"
        )

    if not (shutil.which("wl-copy") or shutil.which("xclip")):
        raise DependencyMissingError(
            "Missing clipboard tool. Please install wl-clipboard (or xclip):\n"
            "  sudo apt install wl-clipboard"
        )


def _uri_to_path(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        raise CaptureFailedError(f"Portal returned unsupported URI: {uri}")
    return unquote(parsed.path)


def capture_with_portal(output_path: str) -> bool:
    """Capture via the XDG Desktop Portal interactive screenshot UI.

    Returns False if the portal is unavailable or reports an error, so the caller
    can try another backend. Raises CaptureCancelledError if the user cancels.
    """
    try:
        from jeepney import DBusAddress, MatchRule, message_bus, new_method_call
        from jeepney.io.blocking import Proxy, open_dbus_connection
    except ImportError:
        return False

    try:
        conn = open_dbus_connection(bus="SESSION")
    except Exception:
        return False

    try:
        token = f"codesnap_{secrets.token_hex(8)}"
        sender = conn.unique_name.lstrip(":").replace(".", "_")
        request_path = f"{PORTAL_OBJECT_PATH}/request/{sender}/{token}"

        # Subscribe to the Response signal *before* calling, to avoid a race.
        rule = MatchRule(
            type="signal",
            interface="org.freedesktop.portal.Request",
            member="Response",
            path=request_path,
        )
        Proxy(message_bus, conn).AddMatch(rule)

        portal = DBusAddress(
            PORTAL_OBJECT_PATH,
            bus_name=PORTAL_BUS_NAME,
            interface="org.freedesktop.portal.Screenshot",
        )
        options = {"handle_token": ("s", token), "interactive": ("b", True)}
        call = new_method_call(portal, "Screenshot", "sa{sv}", ("", options))

        with conn.filter(rule) as queue:
            reply = conn.send_and_get_reply(call, timeout=10)
            if reply.header.message_type.name == "error":
                return False
            signal = conn.recv_until_filtered(queue, timeout=PORTAL_TIMEOUT_SECONDS)
    except TimeoutError as e:
        raise CaptureCancelledError("Screen selection timed out.") from e
    except Exception:
        return False
    finally:
        conn.close()

    response, results = signal.body
    if response == PORTAL_RESPONSE_CANCELLED:
        raise CaptureCancelledError("Screen selection cancelled by user.")
    if response != PORTAL_RESPONSE_SUCCESS or "uri" not in results:
        return False

    source = _uri_to_path(results["uri"][1])
    if not os.path.isfile(source):
        return False

    # The portal writes a new file for this request; move it into our temp dir
    # so codesnap does not leave screenshots behind.
    shutil.move(source, output_path)
    return os.path.getsize(output_path) > 0


def capture_with_slurp(output_path: str) -> bool:
    """Capture screen area using slurp + grim (wlroots compositors)."""
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

    # Compositor lacks wlr-layer-shell (e.g. GNOME Mutter): not a user cancel.
    stderr = (slurp_proc.stderr or "").lower()
    if "doesn't support" in stderr or "failed to create layer" in stderr:
        return False

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
    except Exception:
        return False

    return (
        grim_proc.returncode == 0
        and os.path.exists(output_path)
        and os.path.getsize(output_path) > 0
    )


def capture_with_gnome_screenshot(output_path: str) -> bool:
    """Capture screen area using gnome-screenshot -a. Only reliable on X11."""
    if not shutil.which("gnome-screenshot"):
        return False

    try:
        proc = subprocess.run(
            ["gnome-screenshot", "-a", "-f", output_path],
            capture_output=True,
            text=True,
            timeout=PORTAL_TIMEOUT_SECONDS,
            check=False,
        )
    except Exception:
        return False

    if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True
    raise CaptureCancelledError("Screen selection cancelled by user.")


def capture_screen_region(output_path: str) -> None:
    """Capture a user-selected screen region to output_path.

    Raises:
        CaptureCancelledError: If the user cancels the selection.
        CaptureFailedError: If no backend could capture the screen.
    """
    if capture_with_portal(output_path):
        return

    if capture_with_slurp(output_path):
        return

    if is_x11_session() and capture_with_gnome_screenshot(output_path):
        return

    raise CaptureFailedError(
        "Screen capture failed: no working backend. On GNOME/KDE ensure "
        "xdg-desktop-portal is running; on Sway/Hyprland install grim and slurp."
    )
