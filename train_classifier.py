import os
import zipfile
import io
import pickle
import numpy as np
from PIL import Image, ImageOps
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import xml.etree.ElementTree as ET
from feature_extractor import extract_visual_features

SAMPLES_DIR = r"C:\Users\dipro\Downloads\W+R Samples"
projects = [
    "20260730 TI",
    "20260811 Malcom",
    "20260814 TI",
    "20260904 TI",
    "20260910 Ari",
    "20260926 TI",
    "20261027 TI"
]

def get_thumb(img, size=(32, 32)):
    return np.array(img.convert('L').resize(size), dtype=np.float32)

all_X = []
all_y = []
sample_records = [] # (proj, target, cat_id, cat_name)

for proj in projects:
    xlsx_path = os.path.join(SAMPLES_DIR, f"{proj}.xlsx")
    zip_path = os.path.join(SAMPLES_DIR, f"{proj}.zip")
    if not os.path.exists(xlsx_path) or not os.path.exists(zip_path):
        continue

    print(f"\nExtracting samples from {proj}...")
    
    # 1. Parse Excel captions and drawing anchors
    with zipfile.ZipFile(xlsx_path) as z_xlsx:
        sheet_xml = z_xlsx.read('xl/worksheets/sheet1.xml').decode('utf-8')
        root = ET.fromstring(sheet_xml)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        strings = []
        if 'xl/sharedStrings.xml' in z_xlsx.namelist():
            ss_xml = z_xlsx.read('xl/sharedStrings.xml').decode('utf-8')
            ss_root = ET.fromstring(ss_xml)
            strings = [t.text for t in ss_root.findall('.//main:t', ns)]

        # Find captions by row
        captions_by_row = {}
        for row in root.findall('.//main:row', ns):
            r = int(row.attrib['r'])
            for c in row.findall('main:c', ns):
                val = c.find('main:v', ns)
                if val is not None and c.attrib.get('t') == 's':
                    s_idx = int(val.text)
                    if s_idx < len(strings):
                        txt = strings[s_idx]
                        if txt and any(w in txt for w in ['View', 'Barcode', 'Marks', 'Leaflet', 'Label']):
                            captions_by_row[r] = txt.strip()

        # Parse drawings
        draw_xml = z_xlsx.read('xl/drawings/drawing1.xml').decode('utf-8')
        d_root = ET.fromstring(draw_xml)
        ns_d = {
            'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        }
        rels_xml = z_xlsx.read('xl/drawings/_rels/drawing1.xml.rels').decode('utf-8')
        r_root = ET.fromstring(rels_xml)
        r_map = {rel.attrib['Id']: rel.attrib['Target'] for rel in r_root}

        anchors = []
        excel_images = {}
        for anc in d_root:
            blip = anc.find('.//a:blip', ns_d)
            if blip is None: continue
            eid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            target = r_map.get(eid, '').replace('../', 'xl/')
            if not target.endswith(('.jpeg', '.jpg', '.png')):
                continue

            f = anc.find('xdr:from', ns_d)
            t = anc.find('xdr:to', ns_d)
            fr = int(f.find('xdr:row', ns_d).text) + 1
            tr = int(t.find('xdr:row', ns_d).text) + 1
            anchors.append((fr, tr, target))

            if target in z_xlsx.namelist():
                excel_images[target] = Image.open(io.BytesIO(z_xlsx.read(target)))

    anchors.sort()

    # Determine category for each anchor
    caption_rows = sorted(captions_by_row.keys())

    for fr, tr, target in anchors:
        if target not in excel_images:
            continue

        # Find closest caption at or below this image
        assigned_text = "Rest of the images"
        min_dist = 9999
        for cr in caption_rows:
            if cr >= tr and (cr - tr) < min_dist:
                min_dist = cr - tr
                assigned_text = captions_by_row[cr]

        # If image was placed above row 15 (Page 1 top), it's Shipping Marks View
        if fr <= 14 and tr <= 14:
            cat_id = 1
            cat_name = "Shipping Marks View"
        elif "Export Carton" in assigned_text:
            cat_id = 2
            cat_name = "Export Carton View"
        elif "Open carton" in assigned_text:
            cat_id = 3
            cat_name = "Open carton View"
        elif "Bundle" in assigned_text:
            cat_id = 4
            cat_name = "Bundle View"
        elif "Product View" in assigned_text:
            cat_id = 5
            cat_name = "Product View"
        elif "Reference Sample" in assigned_text:
            cat_id = 6
            cat_name = "Reference Sample View"
        elif "Gloves Marking" in assigned_text:
            cat_id = 7
            cat_name = "Gloves Marking View"
        elif "Barcode" in assigned_text:
            cat_id = 8
            cat_name = "Barcode"
        elif "Leaflet" in assigned_text:
            cat_id = 9
            cat_name = "Leaflet (Front & Back View)"
        elif "Inside Label" in assigned_text:
            cat_id = 10
            cat_name = "Inside Label Front and Back View"
        else:
            cat_id = 11
            cat_name = "Rest of the images"

        img = excel_images[target]
        feat = extract_visual_features(img)
        all_X.append(feat)
        all_y.append(cat_id)
        sample_records.append((proj, target, cat_id, cat_name))

X = np.array(all_X)
y = np.array(all_y)

print(f"\n========================================================")
print(f"Total labeled training samples extracted: {len(y)}")
from collections import Counter
counts = Counter(y)
for cat_id in sorted(counts.keys()):
    print(f"  Category {cat_id:2d}: {counts[cat_id]:3d} samples")

# Train Random Forest Classifier
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
clf = RandomForestClassifier(n_estimators=150, max_depth=16, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\nTrained Model Validation Accuracy: {acc * 100:.2f}%")
print(classification_report(y_test, y_pred, zero_division=0))

# Retrain on 100% of the dataset
final_model = RandomForestClassifier(n_estimators=200, max_depth=18, random_state=42)
final_model.fit(X, y)

output_model_path = r"c:\Users\dipro\OneDrive\Desktop\Code Editor\Inspector\backend\trained_classifier.pkl"
with open(output_model_path, "wb") as f:
    pickle.dump({
        "model": final_model,
        "classes": final_model.classes_,
        "feature_dim": X.shape[1],
        "training_samples_count": len(y)
    }, f)

print(f"Final trained model successfully saved to {output_model_path}")
