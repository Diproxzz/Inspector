import os
import zipfile
import xml.etree.ElementTree as ET
import openpyxl
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

print("Analyzing ground truth sample projects...")

for proj in projects:
    xlsx_path = os.path.join(SAMPLES_DIR, f"{proj}.xlsx")
    zip_path = os.path.join(SAMPLES_DIR, f"{proj}.zip")
    
    if not os.path.exists(xlsx_path) or not os.path.exists(zip_path):
        print(f"Skipping {proj}: files missing")
        continue

    # Inspect xlsx sheet text and drawings
    with zipfile.ZipFile(xlsx_path) as z_xlsx:
        sheet_xml = z_xlsx.read('xl/worksheets/sheet1.xml').decode('utf-8')
        root = ET.fromstring(sheet_xml)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        # Shared strings
        strings = []
        if 'xl/sharedStrings.xml' in z_xlsx.namelist():
            ss_xml = z_xlsx.read('xl/sharedStrings.xml').decode('utf-8')
            ss_root = ET.fromstring(ss_xml)
            strings = [t.text for t in ss_root.findall('.//main:t', ns)]

        # Find captions and their rows
        captions = []
        for row in root.findall('.//main:row', ns):
            r_num = int(row.attrib['r'])
            for c in row.findall('main:c', ns):
                val = c.find('main:v', ns)
                if val is not None and c.attrib.get('t') == 's':
                    str_idx = int(val.text)
                    if str_idx < len(strings):
                        text = strings[str_idx]
                        if text and text.strip():
                            captions.append((r_num, c.attrib['r'], text.strip()))

        # Inspect drawings and image count
        draw_imgs = [n for n in z_xlsx.namelist() if n.startswith('xl/media/')]

    with zipfile.ZipFile(zip_path) as z_raw:
        raw_imgs = [n for n in z_raw.namelist() if n.lower().endswith(('.jpg', '.jpeg', '.png')) and not n.startswith('__MACOSX')]

    print(f"\n==========================================")
    print(f"Project: {proj}")
    print(f"  Raw Images in ZIP: {len(raw_imgs)}")
    print(f"  Embedded Images in XLSX: {len(draw_imgs)}")
    print(f"  Captions Found ({len(captions)}):")
    for r_num, cell_ref, text in captions[:15]:
        print(f"    Row {r_num:3d} ({cell_ref}): {text}")
    if len(captions) > 15:
        print(f"    ... and {len(captions)-15} more captions")
