from unittest.mock import MagicMock, patch

import pytest

from codesnap.capture import capture_screen_region, check_system_dependencies
from codesnap.exceptions import CaptureCancelledError, DependencyMissingError


def test_check_system_dependencies_raises_when_missing():
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyMissingError) as exc_info:
            check_system_dependencies()
        assert "Missing required tools" in str(exc_info.value)


def test_capture_screen_region_handles_cancel():
    # When user cancels slurp (returncode 1), CaptureCancelledError should be raised
    mock_slurp = MagicMock()
    mock_slurp.returncode = 1
    mock_slurp.stdout = ""

    with patch("shutil.which", return_value="/usr/bin/slurp"):
        with patch("subprocess.run", return_value=mock_slurp):
            with pytest.raises(CaptureCancelledError):
                capture_screen_region("/tmp/fake.png")
