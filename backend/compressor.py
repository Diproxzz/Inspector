import io
import hashlib
from PIL import Image, ImageOps, ImageFilter

def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
    """Computes a difference hash (dHash) for fast perceptual duplicate checking."""
    # Resize to (hash_size + 1, hash_size), grayscale
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = list(resized.getdata())
    diff = []
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * (hash_size + 1) + col]
            right = pixels[row * (hash_size + 1) + col + 1]
            diff.append("1" if left > right else "0")
    decimal_val = int("".join(diff), 2)
    return f"{decimal_val:016x}"

def compress_image_pipeline(raw_bytes: bytes, filename: str, is_text_heavy: bool = False):
    """
    Applies visually lossless 220-PPI compression pipeline:
    1. EXIF orientation normalization (exif_transpose).
    2. Master Archival Compressed Copy (LANCZOS, max 1600/2000px, unsharp mask, 4:4:4 subsampling, quality 88).
    3. Excel Print-Ready Copy (scaled to layout slot ~400-660px wide, 220 DPI, quality 88, subsampling 0).
    4. Hashes (SHA-256 and perceptual dHash).
    """
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    
    with Image.open(io.BytesIO(raw_bytes)) as img:
        # Transpose based on EXIF
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        orig_w, orig_h = img.size
        orig_size = len(raw_bytes)
        
        dhash_str = compute_dhash(img)

        # Check orientation: If filename or aspect ratio suggests sideways leaflet (e.g. 165935 is 3157x2298 landscape, but leaflet is portrait), rotate upright
        rot_deg = 0
        if "165935" in filename and orig_w > orig_h:
            img = img.rotate(270, expand=True)
            orig_w, orig_h = img.size
            rot_deg = 270

        # Master Archival Compressed Copy
        max_edge = 2000 if is_text_heavy else 1600
        master = img.copy()
        if max(orig_w, orig_h) > max_edge:
            if orig_w >= orig_h:
                new_w = max_edge
                new_h = int(orig_h * (max_edge / orig_w))
            else:
                new_h = max_edge
                new_w = int(orig_w * (max_edge / orig_h))
            master = master.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Unsharp mask for micro-typography crispness
        master = master.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=3))

        master_buf = io.BytesIO()
        master.save(
            master_buf,
            format="JPEG",
            quality=88,
            optimize=True,
            progressive=True,
            subsampling=0, # 4:4:4 chroma subsampling
            dpi=(220, 220)
        )
        compressed_blob = master_buf.getvalue()
        comp_w, comp_h = master.size
        comp_size = len(compressed_blob)

        # Excel Print-Ready Copy: Scaled to ~600px longest edge for fast XLSX embedding
        excel_max_edge = 720
        excel_copy = img.copy()
        if max(orig_w, orig_h) > excel_max_edge:
            if orig_w >= orig_h:
                ex_w = excel_max_edge
                ex_h = int(orig_h * (excel_max_edge / orig_w))
            else:
                ex_h = excel_max_edge
                ex_w = int(orig_w * (excel_max_edge / orig_h))
            excel_copy = excel_copy.resize((ex_w, ex_h), Image.Resampling.LANCZOS)
        excel_copy = excel_copy.filter(ImageFilter.UnsharpMask(radius=0.6, percent=40, threshold=2))
        
        excel_buf = io.BytesIO()
        excel_copy.save(
            excel_buf,
            format="JPEG",
            quality=88,
            optimize=True,
            subsampling=0,
            dpi=(220, 220)
        )
        excel_blob = excel_buf.getvalue()

        # Inference Copy (max 1024px longest edge, WebP or JPEG quality 85 for token minimization)
        inf_copy = img.copy()
        if max(orig_w, orig_h) > 1024:
            inf_copy.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        inf_buf = io.BytesIO()
        inf_copy.save(inf_buf, format="JPEG", quality=85)
        inference_blob = inf_buf.getvalue()

        return {
            "orig_width": orig_w,
            "orig_height": orig_h,
            "orig_size_bytes": orig_size,
            "comp_width": comp_w,
            "comp_height": comp_h,
            "comp_size_bytes": comp_size,
            "compressed_blob": compressed_blob,
            "excel_blob": excel_blob,
            "inference_blob": inference_blob,
            "sha256_hash": sha256,
            "perceptual_hash": dhash_str,
            "rotation_deg": rot_deg
        }
