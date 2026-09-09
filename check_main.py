content = open('main.py', encoding='utf-8').read()
idx = content.find('app = FastAPI')
print(repr(content[idx:idx+200]))
