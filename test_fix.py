import requests

BASE = "https://web-production-63685.up.railway.app"

resp = requests.get(f"{BASE}/api/products?seller_id=7", allow_redirects=False)
print(f"Status: {resp.status_code}")
print(f"Location: {resp.headers.get('location', 'none')}")
print(f"Products count if 200: {len(resp.json()) if resp.status_code == 200 else 'N/A'}")
