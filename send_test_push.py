import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

resp = requests.post(f"{BASE}/api/push/test", headers=headers)
print(f"Status: {resp.status_code}")
print(resp.text)
