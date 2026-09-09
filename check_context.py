import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

# Show context around the mockup code
print(repr(content[22100:22500]))
