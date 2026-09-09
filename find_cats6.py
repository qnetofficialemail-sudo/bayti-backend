content = open('main.py', encoding='utf-8').read()
idx = content.find('@app.get("/api/categories"')
print(repr(content[idx:idx+400]))
