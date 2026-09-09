import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Check Railway logs by checking if pywebpush is installed
resp = requests.get(f"{BASE}/api/push/vapid-public-key")
print(f"VAPID key available: {resp.status_code}")

# Try placing a test order to trigger push
# First get a product
products = requests.get(f"{BASE}/api/products?limit=5").json()
print(f"Products: {[p['name'] for p in products[:3]]}")
