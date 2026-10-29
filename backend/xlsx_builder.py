import io
from typing import List, Dict, Any
import openpyxl
from openpyxl.worksheet.pagebreak import Break
from openpyxl.styles import Font, Alignment
from openpyxl.drawing.image import Image as OpenPyXLImage
from openpyxl.drawing.spreadsheet_drawing import TwoCellAnchor, AnchorMarker
from backend.image_formatter import create_formatted_excel_image

CALIBRI_11 = Font(name="Calibri", size=11, bold=False, color="000000")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=False)

def apply_caption_style(ws, cell_or_range: str, text: str):
    """Sets caption text, font, and alignment on cell or merged range."""
    if ":" in cell_or_range:
        ws.merge_cells(cell_or_range)
        top_left = cell_or_range.split(":")[0]
        cell = ws[top_left]
    else:
        cell = ws[cell_or_range]
    cell.value = text
    cell.font = CALIBRI_11
    cell.alignment = ALIGN_CENTER

def add_two_cell_image(ws, image_bytes: bytes, f_col: int, f_row: int, t_col: int, t_row: int,
                       f_colOff: int = 20000, f_rowOff: int = 20000, t_colOff: int = 0, t_rowOff: int = 0):
    """Embeds an image into worksheet using TwoCellAnchor without spilling into Column J."""
    img_buf = io.BytesIO(image_bytes)
    img_buf.seek(0)
    xl_img = OpenPyXLImage(img_buf)
    _from = AnchorMarker(col=f_col, colOff=max(0, f_colOff), row=f_row, rowOff=max(0, f_rowOff))
    to = AnchorMarker(col=t_col, colOff=max(0, t_colOff), row=t_row, rowOff=max(0, t_rowOff))
    xl_img.anchor = TwoCellAnchor(editAs="twoCell", _from=_from, to=to)
    ws.add_image(xl_img)

SECTION_NAMES = {
    1: "Shipping Marks View",
    2: "Export Carton View",
    3: "Open carton View",
    4: "Bundle View",
    5: "Product View",
    6: "Reference Sample View",
    7: "Gloves Marking View",
    8: "Barcode",
    9: "Leaflet (Front & Back View)",
    10: "Inside Label Front and Back View",
    11: "Rest of the images"
}

SECTION_SPECS = {
    1: {"target_size": (600, 440), "rows": 12},
    2: {"target_size": (600, 380), "rows": 10},
    3: {"target_size": (600, 380), "rows": 10},
    4: {"target_size": (480, 580), "rows": 15},
    5: {"target_size": (480, 520), "rows": 13},
    6: {"target_size": (480, 600), "rows": 16},
    7: {"target_size": (520, 520), "rows": 13},
    8: {"target_size": (600, 340), "rows": 9},
    9: {"target_size": (560, 600), "rows": 16},
    10: {"target_size": (540, 520), "rows": 13},
    11: {"target_size": (540, 500), "rows": 12},
}

def generate_qc_inspection_workbook(images_records: List[Dict[str, Any]], batch_reference_code: str = "2741 - 481") -> bytes:
    """
    Builds a 100% editable A4 portrait .xlsx inspection report:
    1. Zero blank pages on PDF export: compact pagination with manual row breaks placed at exact content boundaries.
    2. Zero artificial white spaces inside images: zooms in/out (ImageOps.fit) to fill dimensions smoothly.
    3. 2 images in the same row whenever two or more products exist in a classification.
    4. Only Product View and Reference Sample View have captions under individual products. All others have a single collective label centered below the section.
    5. Clean presentation borders so images never stick to cell or table edges.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    # A4 Portrait Page Setup
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.5
    ws.page_margins.top = 0.6
    ws.page_margins.bottom = 0.6
    ws.page_margins.header = 0.3
    ws.page_margins.footer = 0.3

    # Set column widths strictly for columns A through I (no horizontal page overflow)
    for col in ["A", "B", "C", "D", "E", "F", "G", "H", "I"]:
        ws.column_dimensions[col].width = 9.2

    # Group images by section_id (1..11)
    sections_data: Dict[int, List[Dict[str, Any]]] = {s: [] for s in range(1, 12)}
    for r in images_records:
        if not r.get("is_excluded", False):
            s_id = r.get("section_id", 11)
            sections_data[s_id].append(r)

    for s_id in sections_data:
        sections_data[s_id].sort(key=lambda x: x.get("display_order", 0))

    PAGE_BUDGET = 42
    current_page_rows = 0
    current_row = 1

    def ensure_page_capacity(rows_needed: int):
        nonlocal current_page_rows, current_row
        if current_page_rows > 0 and (current_page_rows + rows_needed) > PAGE_BUDGET:
            # Place manual page break at exact boundary to prevent blank pages
            ws.row_breaks.append(Break(id=current_row - 1))
            current_page_rows = 0

    # Iterate through sections in sequential order 1 to 11
    for s_id in range(1, 12):
        imgs = sections_data.get(s_id, [])
        if not imgs:
            continue

        sec_name = SECTION_NAMES[s_id]
        spec = SECTION_SPECS[s_id]
        img_rows = spec["rows"]
        target_sz = spec["target_size"]

        if s_id == 5:
            # Product View: Individual captions per product pair (Size 11, Size 12)
            idx = 0
            while idx < len(imgs):
                ensure_page_capacity(img_rows + 4)
                img1 = imgs[idx]
                b1 = create_formatted_excel_image(img1["excel_blob"], target_size=target_sz)
                add_two_cell_image(ws, b1, f_col=0, f_row=current_row - 1, t_col=4, t_row=current_row + img_rows - 1,
                                   f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                cap1 = img1.get("caption_text") or f"Product View (# {batch_reference_code} - L /11)"
                
                if idx + 1 < len(imgs):
                    img2 = imgs[idx + 1]
                    b2 = create_formatted_excel_image(img2["excel_blob"], target_size=target_sz)
                    add_two_cell_image(ws, b2, f_col=4, f_row=current_row - 1, t_col=8, t_row=current_row + img_rows - 1,
                                       f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                    cap2 = img2.get("caption_text") or f"Product View (# {batch_reference_code} - L /12)"
                    idx += 2
                else:
                    cap2 = None
                    idx += 1
                
                current_row += img_rows
                current_page_rows += img_rows

                # Individual captions under products
                apply_caption_style(ws, f"A{current_row}:D{current_row}", cap1)
                if cap2:
                    apply_caption_style(ws, f"F{current_row}:I{current_row}", cap2)
                current_row += 2
                current_page_rows += 2

        elif s_id == 6:
            # Reference Sample View: 2 images per row whenever 2 or more exist, like the other classifications
            idx = 0
            total_sec_imgs = len(imgs)
            while idx < total_sec_imgs:
                remaining = total_sec_imgs - idx
                if remaining >= 2:
                    ensure_page_capacity(img_rows + 4)
                    img1 = imgs[idx]
                    img2 = imgs[idx + 1]
                    b1 = create_formatted_excel_image(img1["excel_blob"], target_size=target_sz)
                    b2 = create_formatted_excel_image(img2["excel_blob"], target_size=target_sz)
                    add_two_cell_image(ws, b1, f_col=0, f_row=current_row - 1, t_col=4, t_row=current_row + img_rows - 1,
                                       f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                    add_two_cell_image(ws, b2, f_col=4, f_row=current_row - 1, t_col=8, t_row=current_row + img_rows - 1,
                                       f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                    cap1 = img1.get("caption_text") or f"Reference Sample View (# {batch_reference_code} )"
                    cap2 = img2.get("caption_text") or f"Reference Sample View (# {batch_reference_code} )"
                    idx += 2
                    current_row += img_rows
                    current_page_rows += img_rows

                    # Individual captions under products
                    apply_caption_style(ws, f"A{current_row}:D{current_row}", cap1)
                    apply_caption_style(ws, f"F{current_row}:I{current_row}", cap2)
                    current_row += 2
                    current_page_rows += 2
                else:
                    # Single odd image: center in columns C..G
                    ensure_page_capacity(img_rows + 4)
                    img1 = imgs[idx]
                    b1 = create_formatted_excel_image(img1["excel_blob"], target_size=target_sz)
                    add_two_cell_image(ws, b1, f_col=2, f_row=current_row - 1, t_col=6, t_row=current_row + img_rows - 1,
                                       f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                    idx += 1
                    current_row += img_rows
                    current_page_rows += img_rows

                    cap = img1.get("caption_text") or f"Reference Sample View (# {batch_reference_code} )"
                    apply_caption_style(ws, f"C{current_row}:G{current_row}", cap)
                    current_row += 2
                    current_page_rows += 2

        else:
            # ALL OTHER SECTIONS:
            # 1. Two images per row whenever 2 or more products are present!
            # 2. Single collective label centered under the section!
            idx = 0
            total_sec_imgs = len(imgs)
            
            while idx < total_sec_imgs:
                remaining = total_sec_imgs - idx
                if remaining >= 2:
                    ensure_page_capacity(img_rows + (3 if remaining == 2 else 1))
                    img1 = imgs[idx]
                    img2 = imgs[idx + 1]
                    b1 = create_formatted_excel_image(img1["excel_blob"], target_size=target_sz)
                    b2 = create_formatted_excel_image(img2["excel_blob"], target_size=target_sz)
                    add_two_cell_image(ws, b1, f_col=0, f_row=current_row - 1, t_col=4, t_row=current_row + img_rows - 1,
                                       f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                    add_two_cell_image(ws, b2, f_col=4, f_row=current_row - 1, t_col=8, t_row=current_row + img_rows - 1,
                                       f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                    idx += 2
                    current_row += img_rows
                    current_page_rows += img_rows
                else:
                    # Odd single image: center in columns C..G
                    ensure_page_capacity(img_rows + 3)
                    img1 = imgs[idx]
                    b1 = create_formatted_excel_image(img1["excel_blob"], target_size=target_sz)
                    add_two_cell_image(ws, b1, f_col=2, f_row=current_row - 1, t_col=6, t_row=current_row + img_rows - 1,
                                       f_colOff=20000, f_rowOff=20000, t_colOff=0, t_rowOff=0)
                    idx += 1
                    current_row += img_rows
                    current_page_rows += img_rows
                
                # If there are more image rows in this section, add 1 row spacer
                if idx < total_sec_imgs:
                    current_row += 1
                    current_page_rows += 1

            # Collective label centered below the section
            current_row += 1
            current_page_rows += 1
            apply_caption_style(ws, f"C{current_row}:G{current_row}", sec_name)
            current_row += 2
            current_page_rows += 2

    # Set Print Area strictly to columns A..I
    ws.print_area = f"A1:I{current_row}"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
