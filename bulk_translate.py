import requests

BASE = "https://web-production-63685.up.railway.app"
ANTHROPIC_KEY = open("../.env", encoding="utf-8").read() if False else None

# Login as admin
login = requests.post(f"{BASE}/api/auth/login", data={"username": "admin@homemarket.ae", "password": "admin123"})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("Logged in OK")

# Get all products
products = requests.get(f"{BASE}/api/products?limit=200").json()
print(f"Total products: {len(products)}")

import os
api_key = "PUT_YOUR_KEY_HERE"

def translate(text, to_lang):
    if not text: return ""
    lang = "Arabic" if to_lang == "ar" else "English"
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300,
                  "messages": [{"role": "user", "content": f"Translate to {lang}. Return ONLY the translation, no quotes or explanation:\n\n{text}"}]},
            timeout=15,
        )
        return resp.json().get("content", [{}])[0].get("text", "").strip()
    except Exception as e:
        print(f"  Error: {e}")
        return ""

for p in products:
    if not p.get("name_ar"):
        print(f"Translating: {p['name']}")
        name_ar = translate(p["name"], "ar")
        desc_ar = translate(p.get("description", ""), "ar") if p.get("description") else ""
        print(f"  -> {name_ar}")
