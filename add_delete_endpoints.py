import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Add delete endpoints to backend admin router ──
admin_path = os.path.join(BACKEND, 'routers', 'admin.py')
content = open(admin_path, encoding='utf-8').read()

# Find the end of the file and add delete endpoints
# First check what's at the end
print("Last 500 chars of admin.py:")
print(content[-500:])
