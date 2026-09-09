content = open('routers/sellers.py', encoding='utf-8').read()
idx = content.find('def list_sellers')
print(repr(content[idx:idx+300]))
