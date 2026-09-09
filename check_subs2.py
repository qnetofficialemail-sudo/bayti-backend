import requests

BASE = "https://web-production-63685.up.railway.app"

# Login as Fatima
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Try to subscribe with a dummy subscription to see if endpoint works
resp = requests.post(f"{BASE}/api/push/subscribe", 
    json={"subscription": {"endpoint": "https://test.com", "keys": {"p256dh": "test", "auth": "test"}}},
    headers=headers)
print(f"Subscribe status: {resp.status_code}")
print(resp.text[:200])
