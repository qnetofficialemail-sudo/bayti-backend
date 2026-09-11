import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers", "ai.py")
content = open(ai_path, encoding="utf-8").read()

idx = content.find('content_type == "sellers"')
end = content.find('elif content_type == "events"', idx)
print(content[idx:end])
