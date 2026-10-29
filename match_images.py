import zipfile
from PIL import Image
import io
import numpy as np

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.xlsx') as z_xlsx:
    excel_imgs = {}
    for n in z_xlsx.namelist():
        if n.startswith('xl/media/') and n.endswith('.jpeg'):
            data = z_xlsx.read(n)
            excel_imgs[n] = Image.open(io.BytesIO(data))

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.zip') as z_raw:
    raw_imgs = {}
    for n in sorted(z_raw.namelist()):
        if n.lower().endswith(('.jpg', '.jpeg', '.png')):
            data = z_raw.read(n)
            raw_imgs[n] = Image.open(io.BytesIO(data))

# Map each excel image to closest raw image using thumbnail comparison
def get_thumb(img, size=(64, 64)):
    return np.array(img.convert('L').resize(size), dtype=np.float32)

excel_thumbs = {k: get_thumb(v) for k, v in excel_imgs.items()}
raw_thumbs = {k: get_thumb(v) for k, v in raw_imgs.items()}
# Also handle 90, 180, 270 rotations for raw
raw_thumbs_rot = {}
for k, v in raw_imgs.items():
    raw_thumbs_rot[(k, 0)] = get_thumb(v)
    raw_thumbs_rot[(k, 90)] = get_thumb(v.rotate(90, expand=True))
    raw_thumbs_rot[(k, 180)] = get_thumb(v.rotate(180, expand=True))
    raw_thumbs_rot[(k, 270)] = get_thumb(v.rotate(270, expand=True))

matched_raw = set()
for e_name, e_th in sorted(excel_thumbs.items()):
    best_diff = 1e9
    best_match = None
    best_rot = 0
    for (r_name, rot), r_th in raw_thumbs_rot.items():
        diff = np.mean(np.abs(e_th - r_th))
        if diff < best_diff:
            best_diff = diff
            best_match = r_name
            best_rot = rot
    print(f"Excel {e_name} -> Raw {best_match} (diff={best_diff:.2f}, rot={best_rot})")
    matched_raw.add(best_match)

unmatched = set(raw_imgs.keys()) - matched_raw
print("\nUnmatched / Excluded Raw Images:", unmatched)
