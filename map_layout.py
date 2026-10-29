import zipfile
import xml.etree.ElementTree as ET

# Load mapping from match_images logic
from match_images import raw_imgs, excel_imgs, excel_thumbs, raw_thumbs_rot
import numpy as np

excel_to_raw = {}
for e_name, e_th in sorted(excel_thumbs.items()):
    best_diff = 1e9
    best_match = None
    for (r_name, rot), r_th in raw_thumbs_rot.items():
        diff = np.mean(np.abs(e_th - r_th))
        if diff < best_diff:
            best_diff = diff
            best_match = r_name
    excel_to_raw[e_name] = best_match

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.xlsx') as z:
    draw_xml = z.read('xl/drawings/drawing1.xml').decode('utf-8')
    d_root = ET.fromstring(draw_xml)
    ns_d = {
        'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }
    rels_xml = z.read('xl/drawings/_rels/drawing1.xml.rels').decode('utf-8')
    r_root = ET.fromstring(rels_xml)
    r_map = {rel.attrib['Id']: rel.attrib['Target'] for rel in r_root}

    anchors_info = []
    for anchor in d_root:
        from_el = anchor.find('xdr:from', ns_d)
        to_el = anchor.find('xdr:to', ns_d)
        blip = anchor.find('.//a:blip', ns_d)
        if blip is None:
            continue
        embed_id = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
        target = r_map.get(embed_id, '')
        e_key = target.replace('../', 'xl/')
        
        f_col = int(from_el.find('xdr:col', ns_d).text)
        f_row = int(from_el.find('xdr:row', ns_d).text)
        t_col = int(to_el.find('xdr:col', ns_d).text)
        t_row = int(to_el.find('xdr:row', ns_d).text)
        
        raw_name = excel_to_raw.get(e_key, e_key)
        anchors_info.append((f_row, f_col, t_row, t_col, e_key, raw_name))

    anchors_info.sort()
    for f_row, f_col, t_row, t_col, e_key, raw_name in anchors_info:
        print(f"Row {f_row+1:3d} Col {chr(65+f_col)} -> Row {t_row+1:3d} Col {chr(65+t_col)} : {e_key} ({raw_name})")
