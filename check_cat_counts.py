import requests
resp = requests.get("https://web-production-63685.up.railway.app/api/categories")
import json
data = resp.json()
for cat in data:
    print(f"{cat['name']}: product_count={cat.get('product_count', 'MISSING')}")
