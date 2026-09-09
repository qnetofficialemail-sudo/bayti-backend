import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

# Find instagram-content-v2 endpoint and show its structure
idx = content.find('instagram-content-v2')
end_idx = content.find('\n@router', idx+1)
block = content[idx:end_idx] if end_idx > idx else content[idx:idx+5000]

lines = block.splitlines()
for i, line in enumerate(lines):
    print(f"{i+1:4}: {line}")
