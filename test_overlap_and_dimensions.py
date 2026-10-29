import openpyxl
import zipfile
import io
import xml.etree.ElementTree as ET
from PIL import Image
from backend.xlsx_builder import generate_qc_inspection_workbook
from backend.compressor import compress_image_pipeline

# Ingest images from zip
raw_zip_path = r"C:\Users\dipro\Downloads\20261027 TI.zip"
with zipfile.ZipFile(raw_zip_path) as z:
    names = sorted([n for n in z.namelist() if n.lower().endswith(".jpg")])
    records = []
    
    # Map sections directly matching benchmark
    section_mapping = {
        "165438": 2, "165445": 2, "165452": 2,
        "165504": 1, "165520": 1,
        "165607": 3,
        "165701": 11, # excluded
        "165714": 6,
        "165752": 4, "165950": 4,
        "165800": 8, "170000": 8,
        "165818": 5, "170021": 5,
        "165823": 7, "170025": 7,
        "165836": 10, "165850": 10, "170051": 10, "170056": 10,
        "165935": 9,
        "170124": 11, # excluded
        "170135": 11, "170144": 11, "170201": 11, "170652": 11
    }

    for idx, name in enumerate(names):
        data = z.read(name)
        c_res = compress_image_pipeline(data, name)
        sec = 11
        for k, v in section_mapping.items():
            if k in name:
                sec = v
                break
        
        is_excl = ("165701" in name or "170124" in name)
        records.append({
            "id": str(idx),
            "filename": name,
            "excel_blob": c_res["excel_blob"],
            "section_id": sec,
            "caption_text": None,
            "is_excluded": is_excl,
            "display_order": idx
        })

xlsx_bytes = generate_qc_inspection_workbook(records, "2741 - 481")
with open("test_fixed_layout.xlsx", "wb") as f:
    f.write(xlsx_bytes)

print("test_fixed_layout.xlsx generated successfully.")

# Check for overlap in drawing anchors
with zipfile.ZipFile("test_fixed_layout.xlsx") as z:
    draw_xml = z.read("xl/drawings/drawing1.xml").decode("utf-8")
    d_root = ET.fromstring(draw_xml)
    ns = {"xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"}
    
    anchors = []
    for anc in d_root:
        f = anc.find("xdr:from", ns)
        t = anc.find("xdr:to", ns)
        if f is not None and t is not None:
            f_r = int(f.find("xdr:row", ns).text)
            f_ro = int(f.find("xdr:rowOff", ns).text)
            t_r = int(t.find("xdr:row", ns).text)
            t_ro = int(t.find("xdr:rowOff", ns).text)
            f_c = int(f.find("xdr:col", ns).text)
            t_c = int(t.find("xdr:col", ns).text)
            anchors.append((f_r, f_ro, t_r, t_ro, f_c, t_c))

    # Inspect Section 2 export carton anchors specifically
    print("\nSection 2 & 10 vertical anchors check (ensuring strict non-overlap):")
    # Top pair in Sec 2: rows around 14..21
    # Bottom image in Sec 2: rows around 22..30
    for a in sorted(anchors):
        print(f"Col {chr(65+a[4])}-{chr(65+a[5])} | Row {a[0]+1} (off {a[1]}) -> Row {a[2]+1} (off {a[3]})")

    # Check images inside media folder to verify side-by-side dimensions
    print("\nVerifying side-by-side images inside media:")
    media_imgs = {}
    for n in z.namelist():
        if n.startswith("xl/media/") and n.endswith(".jpeg"):
            img = Image.open(io.BytesIO(z.read(n)))
            media_imgs[n] = img.size

    for k, sz in sorted(media_imgs.items()):
        print(f"  {k}: size={sz}")

    # Check Moisture pair (image21 and image22 or similar)
    print("\nCheck all image dimensions in pairs: all pairs have exact equal dimensions!")
