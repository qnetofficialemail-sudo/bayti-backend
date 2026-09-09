import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# First unsubscribe to clear old ones
requests.delete(f"{BASE}/api/push/unsubscribe", headers=headers)
print("Cleared old subscriptions")

# Now check the vapid key
resp = requests.get(f"{BASE}/api/push/vapid-public-key")
print(f"VAPID key: {resp.json()['public_key'][:30]}...")
