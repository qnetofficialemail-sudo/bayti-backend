import requests

BASE = "https://web-production-63685.up.railway.app"
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get all sellers
sellers = requests.get(f"{BASE}/api/sellers", headers=headers).json()
print("All sellers:")
for s in sellers:
    print(f"  id={s.get('id')} shop={s.get('shop_name')} user_id={s.get('user_id')} approved={s.get('is_approved')}")

# Get all users
users = requests.get(f"{BASE}/api/admin/users", headers=headers).json()
print("\nAll users:")
for u in users:
    print(f"  id={u.get('id')} email={u.get('email')} role={u.get('role')}")
