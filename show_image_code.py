import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

# Find all image_url assignments in v2 endpoint
idx = content.find('instagram-content-v2')
v2_block = content[idx:]

# Find all occurrences of image generation
for keyword in ['image_url', 'openai_key', 'gpt-image-1', 'MOCKUP_BASE']:
    positions = []
    pos = v2_block.find(keyword)
    while pos >= 0 and len(positions) < 5:
        positions.append(pos)
        pos = v2_block.find(keyword, pos+1)
    if positions:
        print(f"\n=== '{keyword}' found at positions: {positions[:3]} ===")
        for p in positions[:2]:
            print(repr(v2_block[p:p+100]))
