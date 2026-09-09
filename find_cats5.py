content = open('main.py', encoding='utf-8').read()
import re
for m in re.finditer(r'@app\.\w+\("[^"]*"', content):
    print(m.group())
