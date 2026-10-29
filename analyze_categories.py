import os
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image
import io
import json

SAMPLES_DIR = r"C:\Users\dipro\Downloads\W+R Samples"
projects = [
    "20260730 TI",
    "20260811 Malcom",
    "20260814 TI",
    "20260904 TI",
    "20260910 Ari",
    "20260926 TI"
]

category_stats = {}

for proj in projects:
    xlsx_path = os.path.join(SAMPLES_DIR, f"{proj}.xlsx")
    if not os.path.exists(xlsx_path):
        continue

    with zipfile.ZipFile(xlsx_path) as z:
        ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
        root = ET.fromstring(ss_xml)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for t in root.findall('.//main:t', ns):
            txt = t.text.strip() if t.text else ""
            if "View" in txt or "Barcode" in txt or "Leaflet" in txt or "Marks" in txt or "Label" in txt:
                cat_key = txt.split("(#")[0].strip()
                category_stats[cat_key] = category_stats.get(cat_key, 0) + 1

print("Distinct Section Categories Across All 6 Projects:")
for cat, count in sorted(category_stats.items(), key=lambda x: -x[1]):
    print(f"  {count:3d} occurrences : {cat}")
