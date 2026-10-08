from unittest.mock import MagicMock, patch

import pytest

from codesnap.capture import (
    capture_screen_region,
    capture_with_gnome_screenshot,
    check_system_dependencies,
)
from codesnap.exceptions import CaptureCancelledError, DependencyMissingError


def test_check_system_dependencies_raises_when_missing():
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyMissingError) as exc_info:
            check_system_dependencies()
        assert "Missing" in str(exc_info.value)


def test_check_system_dependencies_passes_with_gnome():
    def mock_which(tool):
        if tool in ("gnome-screenshot", "tesseract", "wl-copy"):
            return f"/usr/bin/{tool}"
        return None

    with patch("shutil.which", side_effect=mock_which):
        check_system_dependencies()


def test_capture_with_gnome_screenshot_success(tmp_path):
    out_img = tmp_path / "snap.png"

    def mock_run(*args, **kwargs):
        out_img.write_bytes(b"image-data")
        res = MagicMock()
        res.returncode = 0
        return res

    with patch("shutil.which", return_value="/usr/bin/gnome-screenshot"):
        with patch("subprocess.run", side_effect=mock_run):
            assert capture_with_gnome_screenshot(str(out_img)) is True


def test_capture_with_gnome_screenshot_cancel(tmp_path):
    out_img = tmp_path / "snap.png"
    # When user cancels, file is not written
    res = MagicMock()
    res.returncode = 1

    with patch("shutil.which", return_value="/usr/bin/gnome-screenshot"):
        with patch("subprocess.run", return_value=res):
            with pytest.raises(CaptureCancelledError):
                capture_with_gnome_screenshot(str(out_img))


def test_capture_slurp_fallback_to_gnome_on_unsupported_protocol(tmp_path):
    out_img = tmp_path / "snap.png"

    # slurp returns protocol error
    slurp_res = MagicMock()
    slurp_res.returncode = 1
    slurp_res.stderr = "compositor doesn't support zwlr_layer_shell_v1"

    # gnome-screenshot creates file
    def mock_run(cmd, *args, **kwargs):
        if cmd[0] == "slurp":
            return slurp_res
        if cmd[0] == "gnome-screenshot":
            out_img.write_bytes(b"image-data")
            res = MagicMock()
            res.returncode = 0
            return res
        return MagicMock()

    with patch("codesnap.capture.is_gnome", return_value=False):
        with patch("shutil.which", return_value="/usr/bin/tool"):
            with patch("subprocess.run", side_effect=mock_run):
                capture_screen_region(str(out_img))
                assert out_img.exists()
