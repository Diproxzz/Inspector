import asyncio
from backend.database import AsyncSessionLocal, InspectionBatch, InspectionImage
from backend.classifier import classifier_service, resolve_section
from sqlalchemy import select

async def fix_and_reclassify_db():
    async with AsyncSessionLocal() as session:
        # Get all batches
        q_b = select(InspectionBatch)
        batches = (await session.execute(q_b)).scalars().all()
        print(f"Found {len(batches)} batches in database.")

        for b in batches:
            print(f"\nProcessing batch {b.id} ({b.batch_name})...")
            q_img = select(InspectionImage).where(InspectionImage.batch_id == b.id).order_by(InspectionImage.display_order)
            imgs = (await session.execute(q_img)).scalars().all()

            counts = {}
            for img in imgs:
                res = await classifier_service.classify_single_image(img.compressed_blob, img.original_filename)
                sec_id, cat_code, sec_name = resolve_section(res.get("cat"))
                
                caption = classifier_service.format_caption(
                    sec_id, cat_code, res.get("article"), res.get("size"), img.original_filename
                )

                img.section_id = sec_id
                img.sub_category = cat_code
                img.caption_text = caption
                img.confidence_score = res.get("conf", 0.95)
                img.classifier_used = res.get("tier", "trained-ml-model")
                img.is_excluded = res.get("is_excluded", False)
                if res.get("rot"):
                    img.rotation_deg = res["rot"]

                counts[sec_id] = counts.get(sec_id, 0) + 1

            b.status = "READY"
            b.processed_images = len(imgs)
            await session.commit()
            print(f"  Batch {b.id} reclassified: Section counts = {dict(sorted(counts.items()))}")

if __name__ == "__main__":
    asyncio.run(fix_and_reclassify_db())
