import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"

# Check existing structure
for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env']]
    level = root.replace(BACKEND, '').count(os.sep)
    indent = '  ' * level
    folder = os.path.basename(root)
    print(f"{indent}{folder}/")
    for f in files:
        print(f"{indent}  {f}")
