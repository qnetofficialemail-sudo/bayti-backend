content = open('main.py', encoding='utf-8').read()
import re
idx = content.find('categor')
while idx >= 0:
    print(repr(content[idx-10:idx+150]))
    print()
    idx = content.find('categor', idx+1)
    if idx > 5000:
        break
