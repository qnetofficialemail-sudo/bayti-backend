import requests
resp = requests.get("https://web-production-63685.up.railway.app/api/sellers")
import json
data = resp.json()
if data:
    print(json.dumps(data[0], indent=2, ensure_ascii=False))
