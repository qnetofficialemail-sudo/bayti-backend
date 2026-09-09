import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

profile = requests.get(f"{BASE}/api/sellers/me", headers=headers)
print(f"Status: {profile.status_code}")
print(profile.json())
