content = open('schemas/schemas.py', encoding='utf-8').read()
idx = content.find('class OrderItemOut')
print(repr(content[idx:idx+300]))
