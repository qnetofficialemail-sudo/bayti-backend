import os
for root, dirs, files in os.walk('routers'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, encoding='utf-8').read()
            if '""))' in content or '""), ' in content:
                print(f'BROKEN: {path}')
            else:
                print(f'OK: {path}')
