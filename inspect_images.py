import zipfile
import hashlib
from PIL import Image
import io

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.xlsx') as z_xlsx:
    excel_imgs = {}
    for n in z_xlsx.namelist():
        if n.startswith('xl/media/') and n.endswith('.jpeg'):
            data = z_xlsx.read(n)
            excel_imgs[n] = data

print(f"Loaded {len(excel_imgs)} images from excel.")

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.zip') as z_raw:
    raw_imgs = {}
    for n in sorted(z_raw.namelist()):
        if n.lower().endswith(('.jpg', '.jpeg', '.png')):
            raw_imgs[n] = z_raw.read(n)

print(f"Loaded {len(raw_imgs)} images from zip.")

# Let's inspect each raw image size and EXIF
for name, data in raw_imgs.items():
    img = Image.open(io.BytesIO(data))
    print(f"{name}: size={img.size}, format={img.format}, bytes={len(data)}")
