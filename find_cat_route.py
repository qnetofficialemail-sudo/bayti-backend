import os, re

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"

for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'scripts']]
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        content = open(fpath, encoding='utf-8', errors='ignore').read()
        if 'categor' in content.lower() and ('patch' in content.lower() or 'put' in content.lower()):
            hits = [i for i, l in enumerate(content.splitlines()) 
                    if 'categor' in l.lower() and ('@' in l or 'router' in l or 'patch' in l.lower() or 'put' in l.lower())]
            if hits:
                lines = content.splitlines()
                print(f"\n=== {fname} ===")
                for h in hits[:10]:
                    print(f"  {h+1}: {lines[h].strip()}")
