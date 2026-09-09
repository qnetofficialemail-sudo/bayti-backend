content = open('routers/ai.py', encoding='utf-8').read()
import re
routes = re.findall(r'@router\.\w+\("[^"]+\"', content)
for r in routes:
    print(r)
