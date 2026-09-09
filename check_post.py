content = open('routers/products.py', encoding='utf-8').read()
idx = content.find('@router.post(""), response_model=ProductOut)')
print(repr(content[idx:idx+100]))
