import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
print(f"Login status: {login.status_code}")
data = login.json()
print(f"Token: {'OK' if data.get('access_token') else 'FAILED'}")
token = data.get('access_token')

headers = {"Authorization": f"Bearer {token}"}
profile = requests.get(f"{BASE}/api/sellers/me", headers=headers)
print(f"Seller profile: {profile.status_code}")
print(profile.json())
