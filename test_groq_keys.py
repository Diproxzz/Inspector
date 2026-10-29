import os
import urllib.request
import urllib.error
import json

raw = os.environ.get("GROQ_API_KEYS", "")
keys = [k.strip() for k in raw.split(",") if k.strip()] or [os.environ.get("GROQ_API_KEY", "your-groq-api-key")]

for idx, k in enumerate(keys, 1):
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/models",
        headers={
            "Authorization": f"Bearer {k}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Key {idx} success! Models count:", len(data.get('data', [])))
            models = [m['id'] for m in data.get('data', [])]
            for m in sorted(models):
                if any(x in m.lower() for x in ['qwen', 'vision', 'vl', 'llama-3.2']):
                    print("  *", m)
            break
    except urllib.error.HTTPError as e:
        print(f"Key {idx} failed with {e.code}: {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Key {idx} error:", e)
