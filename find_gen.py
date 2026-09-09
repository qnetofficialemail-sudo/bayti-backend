import os
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, encoding='utf-8').read()
            if 'generate-description' in content or 'generate_description' in content:
                print(f'{path}: FOUND')
