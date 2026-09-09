import os
for f in ['Procfile', 'railway.json', 'railway.toml', 'nixpacks.toml']:
    try:
        content = open(f, encoding='utf-8').read()
        print(f"=== {f} ===")
        print(content)
    except:
        print(f"{f}: not found")
