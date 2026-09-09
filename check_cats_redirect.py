import requests

BASE = "https://web-production-63685.up.railway.app"

resp = requests.get(f"{BASE}/api/categories", allow_redirects=False)
print(f"Status: {resp.status_code}")
print(f"Location: {resp.headers.get('location', 'none')}")
