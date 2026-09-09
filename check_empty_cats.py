import requests

BASE = "https://web-production-63685.up.railway.app"
cats = requests.get(f"{BASE}/api/categories").json()
products = requests.get(f"{BASE}/api/products?limit=200").json()

# Count products per category
from collections import Counter
cat_counts = Counter(p.get("category", {}).get("id") if p.get("category") else None for p in products)

print("Category product counts:")
for cat in cats:
    count = cat_counts.get(cat["id"], 0)
    status = "EMPTY" if count == 0 else f"{count} products"
    print(f"  {cat['icon']} {cat['name']} (id={cat['id']}): {status}")
