content = open('routers/orders.py', encoding='utf-8').read()
idx = content.find('@router.get("/my"')
print(repr(content[idx:idx+500]))
