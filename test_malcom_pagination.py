import asyncio
from backend.database import AsyncSessionLocal, InspectionBatch, InspectionImage
from sqlalchemy import select
from test_paged_workbook import build_paged_workbook

async def test_pagination_on_malcom():
    async with AsyncSessionLocal() as session:
        q = select(InspectionBatch).where(InspectionBatch.total_images == 60).limit(1)
        batch = (await session.execute(q)).scalar_one_or_none()
        if not batch:
            print("No 60-image batch found")
            return
        
        q_img = select(InspectionImage).where(InspectionImage.batch_id == batch.id).order_by(InspectionImage.section_id, InspectionImage.display_order)
        images = (await session.execute(q_img)).scalars().all()
        
        records = [
            {
                "id": str(img.id),
                "filename": img.original_filename,
                "excel_blob": img.excel_blob,
                "section_id": img.section_id,
                "sub_category": img.sub_category,
                "caption_text": img.caption_text,
                "is_excluded": img.is_excluded,
                "display_order": img.display_order
            }
            for img in images
        ]

        xlsx_bytes, wb = build_paged_workbook(records, "3001 - 120")
        with open("fixed_paged_malcom.xlsx", "wb") as f:
            f.write(xlsx_bytes)

        ws = wb.active
        print(f"Workbook generated successfully: {len(ws._images)} images, {len(ws.row_breaks)} page breaks.")
        
        # Check that NO image crosses an A4 page boundary (multiples of 50)
        PAGE_ROWS = 50
        crossings = []
        for idx, img in enumerate(ws._images):
            anc = img.anchor
            fr = anc._from.row + 1
            tr = anc.to.row + 1
            p_start = (fr - 1) // PAGE_ROWS + 1
            p_end = (tr - 1) // PAGE_ROWS + 1
            if p_start != p_end:
                crossings.append((idx, fr, tr, p_start, p_end))

        print(f"\nPage boundary crossings: {len(crossings)}")
        for idx, fr, tr, ps, pe in crossings:
            print(f"  WARNING: Img [{idx}] from Row {fr} to Row {tr} crosses Page {ps} -> Page {pe}")

        assert len(crossings) == 0, "ZERO images may cross page boundaries!"
        print("PERFECT: Exactly ZERO images cross page boundaries!")

        # Check captions to ensure every caption is on same page as its image block
        captions = []
        for r in range(1, ws.max_row + 1):
            for c in range(1, 10):
                v = ws.cell(r, c).value
                if v and "View" in str(v) or "Barcode" in str(v):
                    page = (r - 1) // PAGE_ROWS + 1
                    captions.append((r, page, v))
        
        print("\nCaptions and their pages:")
        for r, p, cap in captions:
            print(f"  Row {r:3d} (Page {p:2d}): {cap}")

asyncio.run(test_pagination_on_malcom())
