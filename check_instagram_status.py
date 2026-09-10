import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
ai_path = os.path.join(BACKEND, "routers/ai.py")
content = open(ai_path, encoding='utf-8').read()

# Find v2 endpoint
idx = content.find('instagram-content-v2')
end_idx = content.find('\n@router', idx+1)
if end_idx == -1:
    end_idx = len(content)
v2 = content[idx:end_idx]

# Check 1: image generation still present?
has_dalle = 'gpt-image-1' in v2
has_mockup = 'MOCKUP_BASE' in v2
has_image_none = 'image_url = None' in v2

print("=== Instagram Content v2 Status ===")
print(f"DALL-E image generation: {'⚠️ YES (still generating images)' if has_dalle else '✅ NO'}")
print(f"Mockup usage: {'⚠️ YES' if has_mockup else '✅ NO'}")
print(f"image_url = None present: {'✅ YES' if has_image_none else '❌ NO'}")

# Check 2: events section - does it use web search?
has_web_search = 'web_search_20250305' in v2
has_rss = 'rss' in v2.lower() or 'gulfnews' in v2
print(f"\nEvents section:")
print(f"  Web search tool: {'✅ YES' if has_web_search else '❌ NO (still using RSS?)'}")
print(f"  RSS fetch: {'⚠️ YES (old method)' if has_rss else '✅ NO'}")

# Show image-related lines
print("\n=== Image-related lines in v2 ===")
for i, line in enumerate(v2.splitlines()):
    if any(k in line for k in ['image_url', 'gpt-image', 'MOCKUP', 'openai_key']):
        print(f"  {i:3}: {line.strip()}")
