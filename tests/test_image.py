import numpy as np
from PIL import Image

from codesnap.image import is_dark_image, preprocess_image


def test_is_dark_image():
    # Light image
    light = Image.new("L", (100, 100), color=240)
    assert not is_dark_image(light)

    # Dark image
    dark = Image.new("L", (100, 100), color=30)
    assert is_dark_image(dark)


def test_preprocess_image_does_not_crash(tmp_path):
    # Create test image with dark background and white text
    img_path = tmp_path / "test.png"
    arr = np.zeros((200, 400), dtype=np.uint8)
    arr[50:150, 50:350] = 255  # bright block
    img = Image.fromarray(arr)
    img.save(img_path)

    # Preprocessing must succeed and return a valid PIL image
    processed = preprocess_image(str(img_path))
    assert isinstance(processed, Image.Image)
    assert processed.size[0] >= 400
    assert processed.size[1] >= 200
    # Must be grayscale/binary
    assert processed.mode in ("L", "1")
