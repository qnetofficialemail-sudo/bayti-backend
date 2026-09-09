content = open('routers/products.py', encoding='utf-8').read()
idx = content.find('auto_translate')
print(repr(content[idx:idx+600]))
