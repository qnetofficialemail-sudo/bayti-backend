import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

# Check if the fix is in place
idx = content.find('content_type == "sellers"')
while idx >= 0:
    print(f"\nat {idx}:")
    print(repr(content[idx:idx+200]))
    idx = content.find('content_type == "sellers"', idx+1)
