content = open('routers/ai.py', encoding='utf-8').read()
if 'get_current_seller' in content:
    idx = content.find('get_current_seller')
    print('Found at:', repr(content[idx-100:idx+50]))
else:
    print('get_current_seller NOT in file')
