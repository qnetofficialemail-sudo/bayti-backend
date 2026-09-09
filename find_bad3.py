import requests

BASE = "https://web-production-63685.up.railway.app"
products = requests.get(f"{BASE}/api/products?limit=200").json()
for p in products:
    name = p.get("name", "") or ""
    if "I'm not" in name or "I am not" in name or ("?" in name and len(name) > 50):
        print(f"BAD name: id={p['id']} name={name[:100]}")
    desc = p.get("description", "") or ""
    if "I'm not" in desc or "I am not" in desc or ("?" in desc and len(desc) > 100):
        print(f"BAD desc: id={p['id']} name={p['name']} desc={desc[:100]}")
