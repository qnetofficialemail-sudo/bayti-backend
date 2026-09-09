import os, re
for f in os.listdir('routers'):
    if f.endswith('.py'):
        content = open(f'routers/{f}', encoding='utf-8').read()
        if '/api/categories' in content or 'prefix="/api/categories"' in content:
            print(f'{f}')
            idx = content.find('categories')
            print(repr(content[idx-20:idx+100]))
