import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
schema = open(schema_path, encoding='utf-8').read()

old = '    image_2: Optional[str] = None\n    image_3: Optional[str] = None\n    image_4: Optional[str] = None\n    image_5: Optional[str] = None'
new = '    image_2: Optional[str] = None\n    image_3: Optional[str] = None\n    image_4: Optional[str] = None\n    image_5: Optional[str] = None\n    primary_image_index: int = 0\n    time_unit: Optional[str] = "minutes"'

if old in schema:
    schema = schema.replace(old, new)
    open(schema_path, 'w', encoding='utf-8').write(schema)
    print("Done - primary_image_index and time_unit added")
else:
    print("FAIL - finding image_5 line")
    idx = schema.find('image_5')
    print(repr(schema[max(0,idx-50):idx+100]))
