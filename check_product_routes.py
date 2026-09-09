content = open('routers/products.py', encoding='utf-8').read()
import re
for m in re.finditer(r'@router\.\w+\("[^"]*"', content):
    print(m.group())
