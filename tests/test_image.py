from PIL import Image, ImageDraw

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
    img = Image.new("L", (400, 200), color=0)
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 150], fill=255)
    img.save(img_path)

    # Preprocessing must succeed and return a valid PIL image
    processed = preprocess_image(str(img_path))
    assert isinstance(processed, Image.Image)
    assert processed.size[0] >= 400
    assert processed.size[1] >= 200
    # Must be grayscale/binary
    assert processed.mode in ("L", "1")
