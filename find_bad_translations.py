import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Find products with error messages in name_ar
products = requests.get(f"{BASE}/api/products?limit=200").json()
for p in products:
    name_ar = p.get("name_ar", "") or ""
    if "?" in name_ar or "I'm not" in name_ar or "I am not" in name_ar or len(name_ar) > 100:
        print(f"BAD: id={p['id']} name={p['name']} name_ar={name_ar[:80]}")
