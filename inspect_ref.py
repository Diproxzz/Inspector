import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.xlsx') as z:
    sheet_xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
    ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
    ss_root = ET.fromstring(ss_xml)
    ns_ss = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    strings = [t.text for t in ss_root.findall('.//main:t', ns_ss)]
    
    sheet_root = ET.fromstring(sheet_xml)
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    print("CELL VALUES:")
    for row in sheet_root.findall('.//main:row', ns):
        r_num = row.attrib['r']
        cells = []
        for c in row.findall('main:c', ns):
            ref = c.attrib['r']
            val = c.find('main:v', ns)
            if val is not None:
                if c.attrib.get('t') == 's':
                    cells.append(f'{ref}="{strings[int(val.text)]}"')
                else:
                    cells.append(f'{ref}={val.text}')
        if cells:
            print(f'Row {r_num}:', ', '.join(cells))

    # Inspect drawing1.xml to see anchors for all 24 images
    print("\nDRAWING ANCHORS:")
    draw_xml = z.read('xl/drawings/drawing1.xml').decode('utf-8')
    d_root = ET.fromstring(draw_xml)
    ns_d = {
        'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }
    
    # Check relationships
    rels_xml = z.read('xl/drawings/_rels/drawing1.xml.rels').decode('utf-8')
    r_root = ET.fromstring(rels_xml)
    r_map = {rel.attrib['Id']: rel.attrib['Target'] for rel in r_root}

    for idx, anchor in enumerate(d_root):
        tag = anchor.tag.split('}')[-1]
        from_el = anchor.find('xdr:from', ns_d)
        to_el = anchor.find('xdr:to', ns_d)
        blip = anchor.find('.//a:blip', ns_d)
        embed_id = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') if blip is not None else None
        target = r_map.get(embed_id, 'None')
        
        f_col = from_el.find('xdr:col', ns_d).text if from_el is not None else '?'
        f_colOff = from_el.find('xdr:colOff', ns_d).text if from_el is not None else '?'
        f_row = from_el.find('xdr:row', ns_d).text if from_el is not None else '?'
        f_rowOff = from_el.find('xdr:rowOff', ns_d).text if from_el is not None else '?'
        
        t_col = to_el.find('xdr:col', ns_d).text if to_el is not None else '?'
        t_colOff = to_el.find('xdr:colOff', ns_d).text if to_el is not None else '?'
        t_row = to_el.find('xdr:row', ns_d).text if to_el is not None else '?'
        t_rowOff = to_el.find('xdr:rowOff', ns_d).text if to_el is not None else '?'
        
        print(f"[{idx}] {tag}: {target} | from(col={f_col}, row={f_row}) to(col={t_col}, row={t_row})")
