import os, re
for root, dirs, files in os.walk('routers'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, encoding='utf-8').read()
            matches = re.findall(r'@router\.(get|post|put|patch|delete)\("/"', content)
            if matches:
                print(f'{path}: {len(matches)} trailing slash routes')
