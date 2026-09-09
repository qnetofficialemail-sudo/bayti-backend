import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Unsubscribe first to clear old subscriptions
resp = requests.delete(f"{BASE}/api/push/unsubscribe", headers=headers)
print(f"Unsubscribe: {resp.status_code} {resp.text}")
