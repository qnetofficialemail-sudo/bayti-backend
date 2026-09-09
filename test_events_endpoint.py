import urllib.request, urllib.error, json

BASE = "https://web-production-63685.up.railway.app"

# Login
login_data = urllib.parse.urlencode({"username": "admin@homemarket.ae", "password": "admin123"}).encode()
req = urllib.request.Request(f"{BASE}/api/auth/login", data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
import urllib.parse
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]

# Test events endpoint
payload = json.dumps({"type": "events"}).encode()
req = urllib.request.Request(f"{BASE}/api/ai/instagram-content-v2",
    data=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST")
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print("SUCCESS:")
    print(result.get("event"))
    print(result.get("caption")[:200])
except urllib.error.HTTPError as e:
    print("ERROR:", e.code)
    print(e.read().decode()[:500])
