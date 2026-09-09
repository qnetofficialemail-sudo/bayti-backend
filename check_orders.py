import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

resp = requests.get(f"{BASE}/api/orders/my", headers=headers, allow_redirects=False)
print(f"Status: {resp.status_code}")
print(f"Location: {resp.headers.get('location', 'none')}")
print(resp.text[:200])
