from unittest.mock import MagicMock, patch

import pytest

from codesnap import capture
from codesnap.capture import (
    capture_screen_region,
    capture_with_gnome_screenshot,
    capture_with_slurp,
    check_system_dependencies,
)
from codesnap.exceptions import (
    CaptureCancelledError,
    CaptureFailedError,
    DependencyMissingError,
)


def test_check_system_dependencies_raises_when_missing():
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyMissingError) as exc_info:
            check_system_dependencies()
        assert "Missing" in str(exc_info.value)


def test_check_system_dependencies_passes_with_ocr_and_clipboard():
    def mock_which(tool):
        return f"/usr/bin/{tool}" if tool in ("tesseract", "wl-copy") else None

    with patch("shutil.which", side_effect=mock_which):
        check_system_dependencies()


def test_capture_prefers_portal(tmp_path):
    out_img = tmp_path / "snap.png"
    with patch.object(capture, "capture_with_portal", return_value=True) as portal:
        with patch.object(capture, "capture_with_slurp") as slurp:
            capture_screen_region(str(out_img))
    portal.assert_called_once()
    slurp.assert_not_called()


def test_capture_portal_cancel_propagates(tmp_path):
    with patch.object(
        capture, "capture_with_portal", side_effect=CaptureCancelledError("cancelled")
    ):
        with pytest.raises(CaptureCancelledError):
            capture_screen_region(str(tmp_path / "snap.png"))


def test_capture_falls_back_to_slurp_when_portal_unavailable(tmp_path):
    with patch.object(capture, "capture_with_portal", return_value=False):
        with patch.object(capture, "capture_with_slurp", return_value=True) as slurp:
            capture_screen_region(str(tmp_path / "snap.png"))
    slurp.assert_called_once()


def test_gnome_screenshot_not_used_on_wayland(tmp_path):
    with patch.object(capture, "capture_with_portal", return_value=False):
        with patch.object(capture, "capture_with_slurp", return_value=False):
            with patch.object(capture, "is_x11_session", return_value=False):
                with patch.object(capture, "capture_with_gnome_screenshot") as gs:
                    with pytest.raises(CaptureFailedError):
                        capture_screen_region(str(tmp_path / "snap.png"))
    gs.assert_not_called()


def test_gnome_screenshot_used_on_x11(tmp_path):
    with patch.object(capture, "capture_with_portal", return_value=False):
        with patch.object(capture, "capture_with_slurp", return_value=False):
            with patch.object(capture, "is_x11_session", return_value=True):
                with patch.object(
                    capture, "capture_with_gnome_screenshot", return_value=True
                ) as gs:
                    capture_screen_region(str(tmp_path / "snap.png"))
    gs.assert_called_once()


def test_slurp_unsupported_compositor_is_not_a_cancel(tmp_path):
    slurp_res = MagicMock(returncode=1, stdout="")
    slurp_res.stderr = "compositor doesn't support zwlr_layer_shell_v1"
    with patch("shutil.which", return_value="/usr/bin/tool"):
        with patch("subprocess.run", return_value=slurp_res):
            assert capture_with_slurp(str(tmp_path / "snap.png")) is False


def test_slurp_user_cancel_raises(tmp_path):
    slurp_res = MagicMock(returncode=1, stdout="", stderr="")
    with patch("shutil.which", return_value="/usr/bin/tool"):
        with patch("subprocess.run", return_value=slurp_res):
            with pytest.raises(CaptureCancelledError):
                capture_with_slurp(str(tmp_path / "snap.png"))


def test_gnome_screenshot_success(tmp_path):
    out_img = tmp_path / "snap.png"

    def mock_run(*args, **kwargs):
        out_img.write_bytes(b"image-data")
        return MagicMock(returncode=0)

    with patch("shutil.which", return_value="/usr/bin/gnome-screenshot"):
        with patch("subprocess.run", side_effect=mock_run):
            assert capture_with_gnome_screenshot(str(out_img)) is True


def test_uri_to_path_decodes_file_uri():
    path = capture._uri_to_path("file:///home/user/Pictures/Screenshot%20from%20now.png")
    assert path == "/home/user/Pictures/Screenshot from now.png"


def test_uri_to_path_rejects_non_file_uri():
    with pytest.raises(CaptureFailedError):
        capture._uri_to_path("https://example.com/x.png")
