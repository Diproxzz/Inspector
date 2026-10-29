import os
import zipfile
import io
import pickle
import numpy as np
from PIL import Image, ImageOps, ImageStat
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import xml.etree.ElementTree as ET

SAMPLES_DIR = r"C:\Users\dipro\Downloads\W+R Samples"
projects = [
    "20260730 TI",
    "20260811 Malcom",
    "20260814 TI",
    "20260904 TI",
    "20260910 Ari",
    "20260926 TI"
]

CATEGORY_CODES = {
    "Shipping Marks View": 1,
    "Export Carton View": 2,
    "Export Carton Stack View": 2,
    "Open carton View": 3,
    "Bundle View": 4,
    "Product View": 5,
    "Reference Sample View": 6,
    "Gloves Marking View": 7,
    "Barcode": 8,
    "Leaflet (Front & Back View)": 9,
    "Leaflet": 9,
    "Inside Label Front and Back View": 10,
    "Rest of the images": 11
}

def extract_visual_features(img: Image.Image) -> np.ndarray:
    """
    Extracts a rich, compact 72-dimensional visual feature vector:
    - Aspect ratio and log dimensions
    - Color moments (mean, std, skewness in RGB and HSV)
    - Grayscale spatial 4x4 block intensity distribution (16 values)
    - Edge & texture frequency (horizontal and vertical gradients)
    - High-contrast text density
    - Saturation & brightness histograms
    """
    img = ImageOps.exif_transpose(img)
    w, h = img.size
    aspect = w / max(1, h)
    
    # Resize for uniform feature computation
    small = img.convert("RGB").resize((128, 128), Image.Resampling.BILINEAR)
    gray = small.convert("L")
    
    arr_rgb = np.array(small, dtype=np.float32) / 255.0
    arr_gray = np.array(gray, dtype=np.float32) / 255.0
    
    # 1. Geometry features (3)
    geom = [aspect, np.log(w + 1), np.log(h + 1)]
    
    # 2. Color moments (RGB mean & std: 6)
    rgb_means = arr_rgb.mean(axis=(0, 1)).tolist()
    rgb_stds = arr_rgb.std(axis=(0, 1)).tolist()
    
    # 3. HSV characteristics (Hue, Saturation, Value: 6)
    hsv = small.convert("HSV")
    arr_hsv = np.array(hsv, dtype=np.float32) / 255.0
    hsv_means = arr_hsv.mean(axis=(0, 1)).tolist()
    hsv_stds = arr_hsv.std(axis=(0, 1)).tolist()
    
    # 4. Spatial 4x4 grid intensities (16)
    grid_means = []
    for r in range(4):
        for c in range(4):
            block = arr_gray[r*32:(r+1)*32, c*32:(c+1)*32]
            grid_means.append(float(block.mean()))
            
    # 5. Gradients / Edges (high frequency micro-text / barcodes: 8)
    dx = np.abs(np.diff(arr_gray, axis=1))
    dy = np.abs(np.diff(arr_gray, axis=0))
    edge_x_mean = float(dx.mean())
    edge_x_std = float(dx.std())
    edge_y_mean = float(dy.mean())
    edge_y_std = float(dy.std())
    high_freq_ratio = float((dx > 0.15).mean())
    
    # 6. Color histogram bins (16 bins)
    hist_r, _ = np.histogram(arr_rgb[:, :, 0], bins=8, range=(0, 1))
    hist_b, _ = np.histogram(arr_rgb[:, :, 2], bins=8, range=(0, 1))
    hist_features = (hist_r / hist_r.sum()).tolist() + (hist_b / hist_b.sum()).tolist()

    # 7. Whiteness / background ratio (e.g. white labels, paper leaflets, cardboard)
    white_mask = (arr_rgb[:, :, 0] > 0.75) & (arr_rgb[:, :, 1] > 0.75) & (arr_rgb[:, :, 2] > 0.75)
    brown_mask = (arr_rgb[:, :, 0] > 0.45) & (arr_rgb[:, :, 1] > 0.3) & (arr_rgb[:, :, 2] < 0.25)
    white_ratio = float(white_mask.mean())
    brown_ratio = float(brown_mask.mean())

    features = (
        geom +
        rgb_means + rgb_stds +
        hsv_means + hsv_stds +
        grid_means +
        [edge_x_mean, edge_x_std, edge_y_mean, edge_y_std, high_freq_ratio, white_ratio, brown_ratio] +
        hist_features
    )
    return np.array(features, dtype=np.float32)

print("Visual feature extractor defined (dimension:", len(extract_visual_features(Image.new("RGB", (100, 100)))) , ")")
