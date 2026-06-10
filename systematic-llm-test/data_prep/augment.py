from pathlib import Path
from PIL import Image


def rotate(image: Image.Image, degrees: float) -> Image.Image:
    return image.rotate(degrees, expand=True, fillcolor=(255, 255, 255))


def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
    from PIL import ImageEnhance
    return ImageEnhance.Brightness(image).enhance(factor)


def add_noise(image: Image.Image, intensity: float = 0.05) -> Image.Image:
    import numpy as np
    arr = np.array(image, dtype=np.float32)
    noise = np.random.normal(0, intensity * 255, arr.shape)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))


def blur(image: Image.Image, radius: float = 1.5) -> Image.Image:
    from PIL import ImageFilter
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


def tilt(image: Image.Image, skew_factor: float = 0.1) -> Image.Image:
    # TODO: implement perspective transform using OpenCV
    raise NotImplementedError


def apply_scan_degradation(image: Image.Image, quality: str = "low") -> Image.Image:
    # TODO: simulate scanner artifacts — shadow, uneven lighting, compression
    raise NotImplementedError


def augment_image(
    image: Image.Image,
    augment_types: list[str],
) -> Image.Image:
    ops = {
        "rotate": lambda img: rotate(img, degrees=5),
        "brightness": lambda img: adjust_brightness(img, factor=0.85),
        "noise": lambda img: add_noise(img, intensity=0.03),
        "blur": lambda img: blur(img, radius=1.0),
        "tilt": lambda img: tilt(img, skew_factor=0.05),
    }
    for aug in augment_types:
        image = ops[aug](image)
    return image
