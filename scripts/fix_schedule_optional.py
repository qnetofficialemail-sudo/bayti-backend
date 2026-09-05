import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
content = open(sellers_path, encoding='utf-8').read()

# Find line 13 area and show it
lines = content.split('\n')
print("Lines 12-25:")
for i, line in enumerate(lines[11:25], 12):
    print(f"{i}: {repr(line)}")
