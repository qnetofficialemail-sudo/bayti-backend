import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
content = open(schema_path, encoding='utf-8').read()

old = '    image_url: Optional[str]\n    is_available: bool'
new = '''    image_url: Optional[str] = None
    image_2: Optional[str] = None
    image_3: Optional[str] = None
    image_4: Optional[str] = None
    image_5: Optional[str] = None
    primary_image_index: int = 0
    time_unit: Optional[str] = "minutes"
    is_available: bool'''

if old in content:
    content = content.replace(old, new)
    open(schema_path, 'w', encoding='utf-8').write(content)
    print("Done")
else:
    print("FAIL")
    idx = content.find('image_url')
    print(repr(content[max(0,idx-50):idx+100]))
