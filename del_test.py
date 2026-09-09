import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

resp = requests.delete(f"{BASE}/api/products/23", headers=headers)
print(f"Delete test product: {resp.status_code}")
