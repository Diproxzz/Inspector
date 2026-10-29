import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile(r'C:\Users\dipro\Downloads\W+R Samples\20260730 TI.xlsx') as z:
    # Print all text strings
    ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
    ss_root = ET.fromstring(ss_xml)
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    strings = [t.text for t in ss_root.findall('.//main:t', ns)]
    print(f"Total unique strings in 20260730 TI: {len(strings)}")
    for s in strings:
        if any(w in s for w in ['View', 'View (', 'Marks', 'Product', 'Reference', 'Barcode', 'Carton', 'Bundle', 'Inside', 'Leaflet', 'Gloves']):
            print("  -", s)

    # Check for EMF or image files
    emf_files = [n for n in z.namelist() if n.lower().endswith('.emf')]
    print("EMF files count:", len(emf_files))
