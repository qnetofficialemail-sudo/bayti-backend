import requests

BASE = "https://web-production-63685.up.railway.app"
products = requests.get(f"{BASE}/api/products?limit=200").json()
for p in products:
    desc_ar = p.get("description_ar", "") or ""
    name_ar = p.get("name_ar", "") or ""
    bad = False
    for field in [name_ar, desc_ar]:
        if "?" in field and len(field) > 50:
            bad = True
        if "I'm not" in field or "I am not" in field:
            bad = True
    if bad:
        print(f"BAD: id={p['id']} name={p['name']}")
        print(f"  name_ar: {name_ar[:60]}")
        print(f"  desc_ar: {desc_ar[:80]}")
