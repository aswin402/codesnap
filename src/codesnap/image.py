"""Image preprocessing routines for improved OCR accuracy."""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def is_dark_image(img: Image.Image) -> bool:
    """Determine whether an image has a predominantly dark background."""
    gray = img.convert("L")
    arr = np.array(gray)
    # Check corners and borders where background usually resides
    h, w = arr.shape
    border_pixels = np.concatenate(
        [
            arr[0, :],
            arr[-1, :],
            arr[:, 0],
            arr[:, -1],
        ]
    )
    border_mean = float(np.mean(border_pixels))
    overall_mean = float(np.mean(arr))
    # If border or overall brightness is low, it is dark mode
    return border_mean < 128 or overall_mean < 110


def preprocess_image(img_path: str, high_quality: bool = False) -> Image.Image:
    """Preprocess image for optimal Tesseract OCR extraction.

    - Converts to grayscale.
    - Detects dark mode and auto-inverts (Tesseract works best with dark text on light background).
    - Upscales small snippets to ensure sufficient stroke density.
    - Enhances contrast and sharpness.
    - Applies safe median noise filtering (size=3, odd integer).
    - Thresholds image to clean binarized output.
    """
    try:
        img = Image.open(img_path)
    except Exception:
        # If opening fails, return empty fallback
        return Image.new("L", (100, 100), color=255)

    gray = img.convert("L")

    # Invert dark-mode code snippets
    if is_dark_image(gray):
        gray = ImageOps.invert(gray)

    # Upscale if low resolution
    width, height = gray.size
    min_w = 1200 if high_quality else 1000
    min_h = 350 if high_quality else 300
    if width < min_w or height < min_h:
        scale_factor = max(min_w / max(width, 1), min_h / max(height, 1))
        new_size = (int(width * scale_factor), int(height * scale_factor))
        gray = gray.resize(new_size, Image.Resampling.LANCZOS)

    # Contrast and sharpness enhancement
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = ImageEnhance.Sharpness(gray).enhance(2.0)

    # Binarize with threshold
    arr = np.array(gray)
    threshold = float(np.mean(arr) * 0.88)
    binary = arr > threshold
    out_img = Image.fromarray((binary * 255).astype(np.uint8))

    # Remove small salt-and-pepper noise using valid odd filter size (size=3)
    out_img = out_img.filter(ImageFilter.MedianFilter(size=3))

    return out_img
