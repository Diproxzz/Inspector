import os
import zipfile
import xml.etree.ElementTree as ET

SAMPLES_DIR = r"C:\Users\dipro\Downloads\W+R Samples"
proj = "20260811 Malcom"

with zipfile.ZipFile(os.path.join(SAMPLES_DIR, f"{proj}.xlsx")) as z:
    sheet_xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
    root = ET.fromstring(sheet_xml)
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    
    ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
    ss_root = ET.fromstring(ss_xml)
    strings = [t.text for t in ss_root.findall('.//main:t', ns)]

    print(f"=== ALL ROWS WITH STRINGS IN {proj} ===")
    for row in root.findall('.//main:row', ns):
        r = int(row.attrib['r'])
        for c in row.findall('main:c', ns):
            val = c.find('main:v', ns)
            if val is not None and c.attrib.get('t') == 's':
                s_idx = int(val.text)
                if s_idx < len(strings):
                    print(f"Row {r:3d} ({c.attrib['r']}): {strings[s_idx]}")

    # Inspect drawing anchors
    draw_xml = z.read('xl/drawings/drawing1.xml').decode('utf-8')
    d_root = ET.fromstring(draw_xml)
    ns_d = {
        'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
    }
    rels_xml = z.read('xl/drawings/_rels/drawing1.xml.rels').decode('utf-8')
    r_root = ET.fromstring(rels_xml)
    r_map = {rel.attrib['Id']: rel.attrib['Target'] for rel in r_root}

    print(f"\n=== DRAWING ANCHORS IN {proj} ===")
    anchors = []
    for anc in d_root:
        blip = anc.find('.//a:blip', ns_d)
        if blip is None: continue
        eid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
        target = r_map.get(eid, '').replace('../', 'xl/')
        f = anc.find('xdr:from', ns_d)
        t = anc.find('xdr:to', ns_d)
        fr = int(f.find('xdr:row', ns_d).text) + 1
        tr = int(t.find('xdr:row', ns_d).text) + 1
        fc = int(f.find('xdr:col', ns_d).text)
        anchors.append((fr, tr, fc, target))

    anchors.sort()
    for fr, tr, fc, target in anchors:
        print(f"Row {fr:3d}->{tr:3d} (Col {fc}) : {target}")
