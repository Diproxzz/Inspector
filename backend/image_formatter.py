import io
from PIL import Image, ImageOps, ImageDraw

def add_presentation_frame(img: Image.Image, target_size: tuple[int, int] = None, border_color=(170, 185, 200), border_width=2) -> Image.Image:
    """
    Standardizes image for presentation:
    - Never crops or cuts any part of the image: the complete picture is preserved 100%.
    - Expands/resizes the entire picture to fit the format cleanly without cropping.
    - Zero white spaces or letterbox bars added.
    - Subtle slate border so images never stick to cell or table edges.
    """
    if target_size:
        # Full uncropped picture expanded to target format (zero cropped pixels)
        fitted = img.resize(target_size, Image.Resampling.LANCZOS)
    else:
        fitted = img.copy()

    # Draw crisp subtle border around the outer edges
    draw = ImageDraw.Draw(fitted)
    w, h = fitted.size
    for b in range(border_width):
        draw.rectangle([b, b, w - 1 - b, h - 1 - b], outline=border_color)

    return fitted

def create_formatted_excel_image(raw_bytes: bytes, target_size: tuple[int, int] = None) -> bytes:
    """Formats image with presentation border (zero cropping, zero white padding) and encodes as 220 DPI JPEG."""
    with Image.open(io.BytesIO(raw_bytes)) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        framed = add_presentation_frame(img, target_size=target_size)
        
        buf = io.BytesIO()
        framed.save(
            buf,
            format="JPEG",
            quality=92,
            optimize=True,
            subsampling=0,
            dpi=(220, 220)
        )
        return buf.getvalue()
