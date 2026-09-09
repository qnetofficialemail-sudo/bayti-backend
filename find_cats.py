import os, re
for f in os.listdir('routers'):
    content = open(f'routers/{f}', encoding='utf-8').read()
    if 'categories' in content and '@router' in content:
        routes = re.findall(r'@router\.\w+\("[^"]*categor[^"]*"', content)
        if routes:
            print(f'{f}: {routes}')
