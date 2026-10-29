import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\W+R Samples\20260730 TI.xlsx') as z:
    sheet_xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
    root = ET.fromstring(sheet_xml)
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    
    ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
    ss_root = ET.fromstring(ss_xml)
    strings = [t.text for t in ss_root.findall('.//main:t', ns)]

    print("ALL CELL TEXT AND ROWS IN 20260730 TI:")
    for row in root.findall('.//main:row', ns):
        r_num = int(row.attrib['r'])
        for c in row.findall('main:c', ns):
            val = c.find('main:v', ns)
            if val is not None:
                if c.attrib.get('t') == 's':
                    s_idx = int(val.text)
                    if s_idx < len(strings):
                        print(f"Row {r_num:3d} ({c.attrib['r']}): {strings[s_idx]}")
                else:
                    print(f"Row {r_num:3d} ({c.attrib['r']}): {val.text}")
