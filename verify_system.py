import asyncio
import os
import zipfile
import io
import openpyxl
from backend.database import init_db
from backend.compressor import compress_image_pipeline
from backend.classifier import classifier_service
from backend.xlsx_builder import generate_qc_inspection_workbook

async def run_full_verification():
    print("==========================================================")
    print("RUNNING POST-FIX AUTOMATED VERIFICATION SUITE")
    print("==========================================================")

    await init_db()

    raw_zip_path = r"C:\Users\dipro\Downloads\20261027 TI.zip"
    images_records = []
    
    with zipfile.ZipFile(raw_zip_path) as z:
        names = sorted([n for n in z.namelist() if n.lower().endswith(".jpg")])

        for idx, name in enumerate(names):
            data = z.read(name)
            is_text = any(x in name for x in ["165935", "165504", "165520"])
            c_res = compress_image_pipeline(data, name, is_text_heavy=is_text)

            clf = await classifier_service.classify_single_image(c_res["compressed_blob"], name)
            sec_id = int(clf["cat"].replace("CAT_", "").replace("A", "").replace("B", "").replace("C", ""))
            caption = classifier_service.format_caption(sec_id, clf["cat"], clf.get("article"), clf.get("size"), name)

            rec = {
                "id": str(idx),
                "filename": name,
                "excel_blob": c_res["excel_blob"],
                "section_id": sec_id,
                "sub_category": clf["cat"],
                "caption_text": caption,
                "is_excluded": clf.get("is_excluded", False),
                "display_order": idx
            }
            images_records.append(rec)

    xlsx_bytes = generate_qc_inspection_workbook(images_records, "2741 - 481")
    output_path = r"c:\Users\dipro\OneDrive\Desktop\Code Editor\Inspector\generated_inspection_report.xlsx"
    with open(output_path, "wb") as f:
        f.write(xlsx_bytes)

    # Validate output workbook
    wb = openpyxl.load_workbook(output_path, data_only=False)
    ws = wb.active
    assert ws.title == "Sheet1"
    assert int(ws.page_setup.paperSize) == 9
    assert ws.page_setup.orientation == ws.ORIENTATION_PORTRAIT
    
    # Check captions
    assert ws["C14"].value == "Shipping Marks View"
    
    # Verify Product View and Reference Sample View captions exist
    all_text = {cell.coordinate: cell.value for row in ws.rows for cell in row if cell.value is not None}
    assert any("2741 - 481 - L /11" in str(v) for v in all_text.values()), "Product View Size 11 caption missing"
    assert any("2741 - 481 - L /12" in str(v) for v in all_text.values()), "Product View Size 12 caption missing"
    assert any("Reference Sample View" in str(v) for v in all_text.values()), "Reference Sample caption missing"
    assert any("Inside Label Front and Back View" in str(v) for v in all_text.values()), "Inside Label caption missing"
    assert len(ws._images) == 24, f"Expected 24 images, got {len(ws._images)}"
    assert len(ws.row_breaks) >= 4, "Expected page breaks for A4 keep-together pagination"

    # Verify PDF conversion: EXACTLY ZERO BLANK PAGES
    import win32com.client, fitz
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb_com = excel.Workbooks.Open(output_path)
    pdf_path = output_path.replace(".xlsx", ".pdf")
    wb_com.ActiveSheet.ExportAsFixedFormat(0, pdf_path)
    wb_com.Close(False)
    excel.Quit()

    doc = fitz.open(pdf_path)
    print(f"Exported PDF pages: {len(doc)}")
    for i, page in enumerate(doc):
        imgs = len(page.get_images())
        txt = page.get_text().strip()
        assert (imgs > 0 or len(txt) > 0), f"Page {i+1} is completely blank in PDF conversion!"
    print("PDF verification passed: ZERO blank pages detected!")

    print("All assertions passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_full_verification())
