import requests, json

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "fatima@homemarket.ae", "password": "seller123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

resp = requests.get(f"{BASE}/api/orders/my", headers=headers)
orders = resp.json()
if orders:
    print(json.dumps(orders[0], indent=2, ensure_ascii=False))
