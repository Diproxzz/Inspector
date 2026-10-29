import urllib.request
import json
from collections import Counter

with urllib.request.urlopen('http://localhost:8000/api/batches') as resp:
    batches = json.loads(resp.read().decode('utf-8'))['batches']
    print(f"Total Batches in Database: {len(batches)}")
    for b in batches:
        bid = b['id']
        with urllib.request.urlopen(f'http://localhost:8000/api/batch/{bid}') as b_resp:
            b_data = json.loads(b_resp.read().decode('utf-8'))
            sec_counts = Counter([img['section_id'] for img in b_data['images']])
            print(f"Batch {bid[:8]} ({b['batch_name']}): {len(b_data['images'])} imgs -> Sections: {dict(sorted(sec_counts.items()))}")
