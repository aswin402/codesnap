from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw

from codesnap.exceptions import DependencyMissingError
from codesnap.ocr import (
    _reconstruct_code_from_rapidocr,
    check_ocr_dependencies,
    extract_text_from_image,
    get_available_engines,
    is_rapidocr_available,
    is_tesseract_available,
)


def test_check_ocr_dependencies_tesseract_success():
    with patch("shutil.which", return_value="/usr/bin/tesseract"):
        check_ocr_dependencies("tesseract")


def test_check_ocr_dependencies_missing_tesseract():
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyMissingError) as exc_info:
            check_ocr_dependencies("tesseract")
        assert "Missing OCR tool: tesseract" in str(exc_info.value)


def test_check_ocr_dependencies_missing_rapidocr():
    with patch("codesnap.ocr.is_rapidocr_available", return_value=False):
        with pytest.raises(DependencyMissingError) as exc_info:
            check_ocr_dependencies("rapidocr")
        assert "Missing RapidOCR" in str(exc_info.value)


def test_check_ocr_dependencies_auto_neither_available():
    with patch("codesnap.ocr.is_rapidocr_available", return_value=False):
        with patch("codesnap.ocr.is_tesseract_available", return_value=False):
            with pytest.raises(DependencyMissingError) as exc_info:
                check_ocr_dependencies("auto")
            assert "No OCR engine found" in str(exc_info.value)


def test_get_available_engines():
    with patch("codesnap.ocr.is_rapidocr_available", return_value=True):
        with patch("codesnap.ocr.is_tesseract_available", return_value=True):
            engines = get_available_engines()
            assert "rapidocr" in engines
            assert "tesseract" in engines


def test_is_tesseract_available():
    with patch("shutil.which", return_value="/bin/tesseract"):
        assert is_tesseract_available() is True
    with patch("shutil.which", return_value=None):
        assert is_tesseract_available() is False


def test_is_rapidocr_available():
    with patch("builtins.__import__", side_effect=ImportError("No module")):
        assert is_rapidocr_available() is False


def test_reconstruct_code_from_rapidocr():
    # Mock RapidOCR output: list of [box, text, score]
    mock_boxes = [
        [[[10, 10], [100, 10], [100, 30], [10, 30]], "def hello():", 0.98],
        [[[50, 40], [180, 40], [180, 60], [50, 60]], "return 'world'", 0.95],
    ]
    reconstructed = _reconstruct_code_from_rapidocr(mock_boxes)
    assert "def hello():" in reconstructed
    assert "return 'world'" in reconstructed
    # Check that second line has indentation spaces
    lines = reconstructed.splitlines()
    assert len(lines) == 2
    assert lines[1].startswith(" ")


def test_extract_text_with_mocked_rapidocr(tmp_path):
    img_path = tmp_path / "code.png"
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    img.save(img_path)

    mock_res = [[[[10, 10], [100, 10], [100, 30], [10, 30]], "const x = 42;", 0.99]]

    class MockRapidEngine:
        def __call__(self, img):
            return mock_res, 0.05

    with patch("codesnap.ocr.is_rapidocr_available", return_value=True):
        with patch("codesnap.ocr.extract_with_rapidocr", return_value="const x = 42;"):
            text = extract_text_from_image(str(img_path), engine="rapidocr")
            assert text == "const x = 42;"


def test_extract_text_from_image_real_ocr(tmp_path):
    img_path = tmp_path / "sample.png"
    img = Image.new("RGB", (400, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "hello codesnap", fill=(0, 0, 0))
    img.save(img_path)

    text = extract_text_from_image(str(img_path), engine="tesseract")
    assert "codesnap" in text.lower() or "hello" in text.lower()
