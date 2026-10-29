import os
import urllib.request
import json

api_key = os.environ.get("GROQ_API_KEY", "your-groq-api-key")
url = "https://api.groq.com/openai/v1/models"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        models = [m['id'] for m in data.get('data', [])]
        print("Available Groq Models:")
        for m in sorted(models):
            if any(x in m.lower() for x in ['qwen', 'vision', 'vl', 'llama-3.2']):
                print("  *", m)
            else:
                print("   ", m)
except Exception as e:
    print("Error querying Groq:", e)
