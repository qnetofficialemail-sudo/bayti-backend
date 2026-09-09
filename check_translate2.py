content = open('routers/products.py', encoding='utf-8').read()
idx = content.find('Translate')
print(repr(content[idx:idx+400]))
