content = open('main.py', encoding='utf-8').read()

# Find current allow_origins and replace with wildcard approach
import re

old = re.search(r'allow_origins=\[.*?\]', content, re.DOTALL)
if old:
    print("Found:", old.group()[:100])
    content = content.replace(
        old.group(),
        'allow_origins=["*"]'
    )
    open('main.py', 'w', encoding='utf-8').write(content)
    print("CORS updated to allow all origins")
else:
    print("Could not find allow_origins")
