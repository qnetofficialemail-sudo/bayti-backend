content = open('schemas/schemas.py', encoding='utf-8').read()
idx = content.find('class ProductOut')
print(repr(content[idx:idx+400]))
