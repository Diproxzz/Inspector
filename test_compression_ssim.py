import zipfile
import io
import numpy as np
from PIL import Image
from backend.compressor import compress_image_pipeline

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.zip') as z:
    raw_data = z.read('20261027_165504.jpg')

res = compress_image_pipeline(raw_data, '20261027_165504.jpg')
print(f"Original size: {res['orig_size_bytes']} bytes ({res['orig_width']}x{res['orig_height']})")
print(f"Compressed size: {res['comp_size_bytes']} bytes ({res['comp_width']}x{res['comp_height']})")
print(f"Compression reduction: {100.0 * (1.0 - res['comp_size_bytes'] / res['orig_size_bytes']):.1f}%")
print(f"Excel blob size: {len(res['excel_blob'])} bytes")

# Simple SSIM estimation
img_orig = Image.open(io.BytesIO(raw_data)).resize((res['comp_width'], res['comp_height']))
img_comp = Image.open(io.BytesIO(res['compressed_blob']))

arr_orig = np.array(img_orig.convert('L'), dtype=np.float64)
arr_comp = np.array(img_comp.convert('L'), dtype=np.float64)

# SSIM standard formula
c1 = (0.01 * 255) ** 2
c2 = (0.03 * 255) ** 2
mu1 = np.mean(arr_orig)
mu2 = np.mean(arr_comp)
sigma1_sq = np.var(arr_orig)
sigma2_sq = np.var(arr_comp)
sigma12 = np.cov(arr_orig.flatten(), arr_comp.flatten())[0, 1]

ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / ((mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2))
print(f"Computed SSIM: {ssim:.4f} (Requirement >= 0.97: {'PASS' if ssim >= 0.97 else 'FAIL'})")
