import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("Logged in OK")

mappings = [
    (1, 2),   # Fatima's Kitchen -> fatima@homemarket.ae
    (5, 12),  # Noor Scents -> noor@bayti.ae
    (6, 13),  # Layla Accessories -> layla@bayti.ae
    (7, 14),  # Mariam Modest -> mariam@bayti.ae
]

for seller_id, user_id in mappings:
    resp = requests.patch(f"{BASE}/api/admin/sellers/{seller_id}/link-user/{user_id}", headers=headers)
    print(f"Seller {seller_id} -> User {user_id}: {resp.status_code} {resp.json()}")

print("Done!")
