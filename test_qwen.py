import urllib.request
import json
import base64
import io
from PIL import Image

# Read one test image from zip
import zipfile
with zipfile.ZipFile(r'C:\Users\dipro\Downloads\20261027 TI.zip') as z:
    img_data = z.read('20261027_165504.jpg')

# Resize inference copy to max 1024px as per prompt spec 2.2
img = Image.open(io.BytesIO(img_data))
img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85)
b64_img = base64.b64encode(buf.getvalue()).decode('utf-8')

api_key = os.environ.get("GROQ_API_KEY", "your-groq-api-key")
payload = {
    "model": "qwen/qwen3.8-27b",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Classify this QC inspection image into one of: CAT_01: Shipping Marks View, CAT_02: Export Carton View, CAT_03: Open carton View, CAT_04: Bundle View, CAT_05: Product View, CAT_06: Reference Sample View, CAT_07: Gloves Marking View, CAT_08: Barcode, CAT_09: Leaflet, CAT_10: Inside Label, CAT_11: Rest of images. Return strictly JSON: {\"cat\": string, \"code\": string, \"conf\": float, \"rot\": int}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
        }
    ],
    "temperature": 0.0,
    "max_tokens": 100
}

req = urllib.request.Request(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Antigravity-QC/1.0"
    },
    data=json.dumps(payload).encode('utf-8')
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Groq Qwen-3.8 Response:")
        print(res['choices'][0]['message']['content'])
        print("Usage:", res.get('usage'))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}:", e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
