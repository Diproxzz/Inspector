import os
import zipfile
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

for proj in projects:
    xlsx_path = os.path.join(SAMPLES_DIR, f"{proj}.xlsx")
    if not os.path.exists(xlsx_path): continue

    with zipfile.ZipFile(xlsx_path) as z:
        sheet_xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
        root = ET.fromstring(sheet_xml)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
        ss_root = ET.fromstring(ss_xml)
        strings = [t.text for t in ss_root.findall('.//main:t', ns)]

        row_caps = []
        for row in root.findall('.//main:row', ns):
            r = int(row.attrib['r'])
            for c in row.findall('main:c', ns):
                val = c.find('main:v', ns)
                if val is not None and c.attrib.get('t') == 's':
                    s_idx = int(val.text)
                    if s_idx < len(strings):
                        txt = strings[s_idx]
                        if txt and any(w in txt for w in ['View', 'Barcode', 'Marks', 'Label']):
                            clean = txt.split('(#')[0].strip()
                            if not row_caps or row_caps[-1][1] != clean:
                                row_caps.append((r, clean))

        print(f"\nSection flow in {proj}:")
        for r, cap in row_caps:
            print(f"  Row {r:3d}: {cap}")
