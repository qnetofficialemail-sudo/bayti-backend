import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Check Railway DB for push subscriptions
resp = requests.get(f"{BASE}/api/admin/push-subscriptions", headers=headers)
print(f"Status: {resp.status_code}")
print(resp.text[:300])
