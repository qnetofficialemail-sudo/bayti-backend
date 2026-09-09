import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

idx = content.find('@router.post("/instagram-content-v2")')
end_idx = content.find('\n@router', idx+1)
if end_idx == -1:
    end_idx = len(content)

v2 = content[idx:end_idx]
print(f"Length: {len(v2)} chars")

# Save to file for inspection
with open("v2_endpoint.txt", "w", encoding="utf-8") as f:
    f.write(v2)
print("Saved to v2_endpoint.txt")
