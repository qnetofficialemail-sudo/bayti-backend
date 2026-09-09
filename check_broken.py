import os
for root, dirs, files in os.walk('routers'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, encoding='utf-8').read()
            if '""), ' in content:
                print(f'{path}: HAS BROKEN PATTERN')
                import re
                matches = re.findall(r'@router\.\w+\(""\),[^\n]+', content)
                for m in matches:
                    print(f'  {m}')
