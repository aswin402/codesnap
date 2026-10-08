"""Optical Character Recognition pipeline using Tesseract."""

import pytesseract

from codesnap.exceptions import OCRError
from codesnap.image import preprocess_image


def extract_text_from_image(img_path: str, high_quality: bool = False) -> str:
    """Preprocess image and execute OCR using optimal Tesseract configuration."""
    try:
        processed_img = preprocess_image(img_path, high_quality=high_quality)
    except Exception as e:
        raise OCRError(f"Image preprocessing failed: {e}") from e

    # PSM 6: Assume a single uniform block of text (ideal for code blocks)
    try:
        text = pytesseract.image_to_string(processed_img, config="--oem 3 --psm 6", lang="eng")
        if text and text.strip():
            return text
    except Exception:
        pass

    # Fallback to default PSM 3 (fully automatic page segmentation)
    try:
        text = pytesseract.image_to_string(processed_img, lang="eng")
        return text or ""
    except Exception as e:
        raise OCRError(f"OCR execution failed: {e}") from e
