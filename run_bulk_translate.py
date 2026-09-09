import requests, time

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("Logged in OK")

products = requests.get(f"{BASE}/api/products?limit=200").json()
print(f"Total products: {len(products)}")

for p in products:
    if not p.get("name_ar"):
        print(f"Translating product {p['id']}: {p['name']}")
        resp = requests.patch(f"{BASE}/api/products/{p['id']}/translate", headers=headers)
        print(f"  Status: {resp.status_code} -> {resp.json().get('name_ar', 'error')}")
        time.sleep(1)  # avoid rate limiting
    else:
        print(f"Skip {p['id']} {p['name']} - already has Arabic")

print("Done!")
