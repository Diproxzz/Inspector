import os
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image
import io
import json
import numpy as np

SAMPLES_DIR = r"C:\Users\dipro\Downloads\W+R Samples"
projects = [
    "20260730 TI",
    "20260811 Malcom",
    "20260814 TI",
    "20260904 TI",
    "20260910 Ari",
    "20260926 TI"
]

def get_thumb(img, size=(48, 48)):
    return np.array(img.convert('L').resize(size), dtype=np.float32)

all_labeled_samples = [] # list of {project, section_name, caption, raw_filename, excel_image}

for proj in projects:
    xlsx_path = os.path.join(SAMPLES_DIR, f"{proj}.xlsx")
    zip_path = os.path.join(SAMPLES_DIR, f"{proj}.zip")
    if not os.path.exists(xlsx_path) or not os.path.exists(zip_path):
        continue

    print(f"\nProcessing project: {proj}...")
    
    with zipfile.ZipFile(xlsx_path) as z_xlsx:
        sheet_xml = z_xlsx.read('xl/worksheets/sheet1.xml').decode('utf-8')
        root = ET.fromstring(sheet_xml)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        strings = []
        if 'xl/sharedStrings.xml' in z_xlsx.namelist():
            ss_xml = z_xlsx.read('xl/sharedStrings.xml').decode('utf-8')
            ss_root = ET.fromstring(ss_xml)
            strings = [t.text for t in ss_root.findall('.//main:t', ns)]

        # Get captions by row
        captions_by_row = {}
        for row in root.findall('.//main:row', ns):
            r_num = int(row.attrib['r'])
            for c in row.findall('main:c', ns):
                val = c.find('main:v', ns)
                if val is not None and c.attrib.get('t') == 's':
                    s_idx = int(val.text)
                    if s_idx < len(strings):
                        txt = strings[s_idx]
                        if txt and txt.strip():
                            captions_by_row[r_num] = txt.strip()

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

        excel_anchors = []
        for anc in d_root:
            blip = anc.find('.//a:blip', ns_d)
            if blip is None:
                continue
            embed_id = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            target = r_map.get(embed_id, '').replace('../', 'xl/')
            
            f_el = anc.find('xdr:from', ns_d)
            t_el = anc.find('xdr:to', ns_d)
            if f_el is not None and t_el is not None:
                f_r = int(f_el.find('xdr:row', ns_d).text) + 1
                t_r = int(t_el.find('xdr:row', ns_d).text) + 1
                f_c = int(f_el.find('xdr:col', ns_d).text)
                excel_anchors.append((f_r, t_r, f_c, target))

        excel_anchors.sort()

        # Find closest caption below each image
        caption_rows = sorted(captions_by_row.keys())
        excel_image_labels = {} # target -> caption
        for f_r, t_r, f_c, target in excel_anchors:
            # find first caption at or below t_r
            assigned_cap = "Rest of the images"
            for cr in caption_rows:
                if cr >= t_r and (cr - t_r) <= 15:
                    assigned_cap = captions_by_row[cr]
                    break
                elif cr >= f_r and (cr - f_r) <= 15:
                    assigned_cap = captions_by_row[cr]
                    break
            excel_image_labels[target] = assigned_cap

    print(f"  Mapped {len(excel_image_labels)} images to captions in {proj}")
    
    # Count distribution of captions
    from collections import Counter
    cap_counts = Counter(excel_image_labels.values())
    for cap, cnt in cap_counts.most_common(10):
        print(f"    {cnt:3d}x : {cap}")

print("\nFinished initial caption extraction.")
