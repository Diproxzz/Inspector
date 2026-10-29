import os
import zipfile
import io
from PIL import Image
from backend.classifier import classifier_service
import asyncio

async def test_sample_project(proj_name="20260811 Malcom"):
    zip_path = os.path.join(r"C:\Users\dipro\Downloads\W+R Samples", f"{proj_name}.zip")
    with zipfile.ZipFile(zip_path) as z:
        names = sorted([n for n in z.namelist() if n.lower().endswith(('.jpg', '.jpeg', '.png')) and not n.startswith('__')])
        print(f"Testing {len(names)} images from {proj_name}...")
        
        counts = {}
        for idx, name in enumerate(names[:25]): # test first 25
            data = z.read(name)
            res = await classifier_service.classify_single_image(data, os.path.basename(name))
            cat = res["cat"]
            counts[cat] = counts.get(cat, 0) + 1
            print(f"  [{idx+1:2d}] {os.path.basename(name)} -> {cat} ({res['tier']}, conf: {res['conf']:.2f})")
            
        print("\nCategory Distribution for sample:")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v} images")

if __name__ == "__main__":
    asyncio.run(test_sample_project())
