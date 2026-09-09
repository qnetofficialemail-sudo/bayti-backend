import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"

# Search for categories endpoint in all router files
for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'scripts']]
    for fname in files:
        if not fname.endswith('.py'):
            continue
        content = open(os.path.join(root, fname), encoding='utf-8', errors='ignore').read()
        if '@router.get' in content and 'categor' in content.lower():
            lines = content.splitlines()
            hits = [i for i, l in enumerate(lines) 
                    if '@router.get' in l and 'categor' in l.lower()]
            if hits:
                print(f"\n=== {fname} ===")
                for h in hits:
                    start = max(0, h-1)
                    end = min(len(lines), h+20)
                    for i in range(start, end):
                        print(f"  {i+1}: {lines[i]}")
                    print()
