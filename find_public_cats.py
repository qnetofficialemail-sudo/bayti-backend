import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"

for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'scripts']]
    for fname in files:
        if not fname.endswith('.py'):
            continue
        content = open(os.path.join(root, fname), encoding='utf-8', errors='ignore').read()
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if ('categories' in line.lower() and 
                ('@router.get' in line or '@app.get' in line) and
                'manage' not in line.lower()):
                start = max(0, i-1)
                end = min(len(lines), i+25)
                print(f"\n=== {fname} line {i+1} ===")
                for j in range(start, end):
                    print(f"  {j+1}: {lines[j]}")
