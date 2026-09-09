import requests
resp = requests.get("https://web-production-63685.up.railway.app/api/push/vapid-public-key")
print(f"Status: {resp.status_code}")
print(resp.text[:200])
