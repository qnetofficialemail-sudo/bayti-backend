import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

# Remove mockup from sellers
old = '''        # Use mockup for platform topics, None for tips (user will add image manually)
        if use_mockup:
            MOCKUP_BASE = "https://bayti-frontend-three.vercel.app/mockups"
            image_url_s = random_s.choice([f"{MOCKUP_BASE}/mockup_0{i}.png" for i in range(1, 6)])
        else:
            image_url_s = None  # User will add image manually via Gemini'''

new = '''        # No image — user adds manually via Gemini
        image_url_s = None'''

if old in content:
    content = content.replace(old, new)
    print("✅ Removed mockup from sellers")
else:
    print("NOT FOUND")

open(ai_path, 'w', encoding='utf-8').write(content)
