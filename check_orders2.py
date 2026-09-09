import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Admin can also call /my
resp = requests.get(f"{BASE}/api/orders/my", headers=headers)
print(f"Admin /my status: {resp.status_code}")
print(resp.text[:300])

# Also try orders list
resp2 = requests.get(f"{BASE}/api/orders", headers=headers)
print(f"Orders list status: {resp2.status_code}")
