content = open('routers/ai.py', encoding='utf-8').read()
# Find the new endpoint
idx = content.find('generate-description')
print(repr(content[idx-50:idx+200]))
