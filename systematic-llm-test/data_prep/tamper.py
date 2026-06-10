from PIL import Image


def replace_text_field(image: Image.Image, region: tuple[int, int, int, int], new_text: str) -> Image.Image:
    # TODO: use PIL.ImageDraw or pytesseract + inpainting to replace text in region
    # region = (left, top, right, bottom)
    raise NotImplementedError


def overlay_stamp(
    image: Image.Image,
    stamp: Image.Image,
    position: tuple[int, int],
    opacity: float = 0.8,
) -> Image.Image:
    # TODO: composite stamp onto document with adjustable opacity and position
    raise NotImplementedError


def delete_region(image: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
    # TODO: blank out a region (simulate deletion of text/stamp)
    raise NotImplementedError


def apply_tampering(
    image: Image.Image,
    tamper_type: str,
    **kwargs,
) -> Image.Image:
    ops = {
        "text_replacement": replace_text_field,
        "stamp_overlay": overlay_stamp,
        "deletion": delete_region,
    }
    if tamper_type not in ops:
        raise ValueError(f"Unknown tamper_type: {tamper_type}")
    return ops[tamper_type](image, **kwargs)
