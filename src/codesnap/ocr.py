"""Optical Character Recognition pipeline supporting Tesseract and RapidOCR (ONNX)."""

import shutil

from codesnap.exceptions import DependencyMissingError, OCRError
from codesnap.image import preprocess_image


def is_rapidocr_available() -> bool:
    """Check if rapidocr_onnxruntime is installed and importable."""
    try:
        import rapidocr_onnxruntime  # noqa: F401

        return True
    except ImportError:
        return False


def is_tesseract_available() -> bool:
    """Check if tesseract binary exists in system PATH."""
    return bool(shutil.which("tesseract"))


def get_available_engines() -> list[str]:
    """Return list of detected OCR engines on current system."""
    engines = []
    if is_rapidocr_available():
        engines.append("rapidocr")
    if is_tesseract_available():
        engines.append("tesseract")
    return engines


def check_ocr_dependencies(engine: str = "auto") -> None:
    """Verify that required OCR engine dependencies are satisfied."""
    eng = engine.lower().strip()
    if eng == "rapidocr":
        if not is_rapidocr_available():
            raise DependencyMissingError(
                "Missing RapidOCR: please install via: pip install rapidocr-onnxruntime"
            )
        return

    if eng == "tesseract":
        if not is_tesseract_available():
            raise DependencyMissingError(
                "Missing OCR tool: tesseract\nPlease install it via: sudo apt install tesseract-ocr"
            )
        return

    # Auto engine: at least one must be available
    if not is_rapidocr_available() and not is_tesseract_available():
        raise DependencyMissingError(
            "No OCR engine found!\nPlease install Tesseract (sudo apt install tesseract-ocr) "
            "or RapidOCR (pip install rapidocr-onnxruntime)"
        )


def _reconstruct_code_from_rapidocr(results: list) -> str:
    """Reconstruct code lines with indentation from RapidOCR bounding box coordinates."""
    if not results:
        return ""

    valid_items = [item for item in results if len(item) >= 2 and str(item[1]).strip()]
    if not valid_items:
        return ""

    # Extract coordinates: item[0] is 4-point polygon [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    boxes_with_coords = []
    for item in valid_items:
        box = item[0]
        text = str(item[1]).strip()
        min_x = min(pt[0] for pt in box)
        min_y = min(pt[1] for pt in box)
        max_y = max(pt[1] for pt in box)
        h = max_y - min_y
        boxes_with_coords.append((min_y, min_x, h, text))

    boxes_with_coords.sort(key=lambda b: (b[0], b[1]))

    # Cluster words/boxes into horizontal lines
    lines: list[list[tuple[float, float, str]]] = []
    for min_y, min_x, h, text in boxes_with_coords:
        if not lines:
            lines.append([(min_y, min_x, text)])
            continue

        last_line_y = lines[-1][0][0]
        line_threshold = max(h * 0.55, 8.0)
        if abs(min_y - last_line_y) < line_threshold:
            lines[-1].append((min_y, min_x, text))
        else:
            lines.append([(min_y, min_x, text)])

    # Determine left-margin baseline across entire crop
    all_lefts = [min_x for _, min_x, _, _ in boxes_with_coords]
    min_page_x = min(all_lefts) if all_lefts else 0.0

    # Estimate average character width for accurate leading space indentation
    char_widths = []
    for item in valid_items:
        box = item[0]
        text = str(item[1]).strip()
        width = max(pt[0] for pt in box) - min(pt[0] for pt in box)
        if len(text) > 3 and width > 0:
            char_widths.append(width / len(text))
    avg_char_w = (sum(char_widths) / len(char_widths)) if char_widths else 8.0

    rendered_lines = []
    for line in lines:
        line.sort(key=lambda w: w[1])
        first_x = line[0][1]
        indent_spaces = max(0, int(round((first_x - min_page_x) / avg_char_w)))
        line_content = " ".join(w[2] for w in line)
        rendered_lines.append((" " * indent_spaces) + line_content)

    return "\n".join(rendered_lines)


def extract_with_rapidocr(img_path: str, high_quality: bool = False) -> str:
    """Execute OCR using RapidOCR (ONNX Runtime)."""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as e:
        raise DependencyMissingError(
            "RapidOCR is not installed.\nInstall it via: pip install rapidocr-onnxruntime"
        ) from e

    try:
        processed_img = preprocess_image(img_path, high_quality=high_quality)
        engine = RapidOCR()
        result, _ = engine(processed_img)
        if not result:
            return ""
        return _reconstruct_code_from_rapidocr(result)
    except Exception as e:
        raise OCRError(f"RapidOCR execution failed: {e}") from e


def extract_with_tesseract(img_path: str, high_quality: bool = False) -> str:
    """Execute OCR using Tesseract engine with code-optimized PSM 6."""
    if not is_tesseract_available():
        raise DependencyMissingError(
            "Missing OCR tool: tesseract\nPlease install it via: sudo apt install tesseract-ocr"
        )

    try:
        import pytesseract

        processed_img = preprocess_image(img_path, high_quality=high_quality)
    except Exception as e:
        raise OCRError(f"Image preprocessing failed: {e}") from e

    # PSM 6: Single uniform block of monospaced code
    try:
        text = pytesseract.image_to_string(processed_img, config="--oem 3 --psm 6", lang="eng")
        if text and text.strip():
            return text
    except Exception:
        pass

    # Fallback to PSM 3 (auto page segmentation)
    try:
        text = pytesseract.image_to_string(processed_img, lang="eng")
        return text or ""
    except Exception as e:
        raise OCRError(f"Tesseract OCR execution failed: {e}") from e


def extract_text_from_image(img_path: str, high_quality: bool = False, engine: str = "auto") -> str:
    """Extract code text from image using selected engine ('auto', 'rapidocr', 'tesseract')."""
    eng = engine.lower().strip()

    if eng == "rapidocr":
        return extract_with_rapidocr(img_path, high_quality=high_quality)

    if eng == "tesseract":
        return extract_with_tesseract(img_path, high_quality=high_quality)

    # Auto engine: Prefer RapidOCR if installed, fallback seamlessly to Tesseract
    if is_rapidocr_available():
        try:
            text = extract_with_rapidocr(img_path, high_quality=high_quality)
            if text and text.strip():
                return text
        except Exception:
            pass

    return extract_with_tesseract(img_path, high_quality=high_quality)
