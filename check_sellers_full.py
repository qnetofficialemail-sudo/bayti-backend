import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

# Find sellers section in v2 endpoint
idx = content.find('instagram-content-v2')
sellers_start = content.find('content_type == "sellers"', idx)
events_start = content.find('content_type == "events"', sellers_start)

sellers_block = content[sellers_start:events_start]
print(repr(sellers_block[-800:]))  # Show end of sellers block
