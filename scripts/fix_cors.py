content = open('main.py', encoding='utf-8').read()

old = 'allow_origins=["http://localhost:3000", "http://localhost:3001"]'
new = 'allow_origins=["http://localhost:3000", "http://localhost:3001", "https://bayti-frontend-vercel.vercel.app", "https://*.vercel.app"]'

if old in content:
    content = content.replace(old, new)
    open('main.py', 'w', encoding='utf-8').write(content)
    print("CORS updated successfully")
else:
    # Try to find what's there
    import re
    match = re.search(r'allow_origins=\[.*?\]', content)
    if match:
        print("Found:", match.group())
    else:
        print("Could not find allow_origins in main.py")
