from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw

from codesnap.exceptions import DependencyMissingError
from codesnap.ocr import check_ocr_dependencies, extract_text_from_image


def test_check_ocr_dependencies_success():
    with patch("shutil.which", return_value="/usr/bin/tesseract"):
        # Should not raise
        check_ocr_dependencies()


def test_check_ocr_dependencies_missing():
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyMissingError) as exc_info:
            check_ocr_dependencies()
        assert "Missing OCR tool: tesseract" in str(exc_info.value)


def test_extract_text_from_image_real_ocr(tmp_path):
    img_path = tmp_path / "sample.png"
    img = Image.new("RGB", (400, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "hello codesnap", fill=(0, 0, 0))
    img.save(img_path)

    text = extract_text_from_image(str(img_path))
    assert "codesnap" in text.lower() or "hello" in text.lower()
