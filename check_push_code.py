content = open('routers/orders.py', encoding='utf-8').read()
idx = content.find('send_push_notification')
print(repr(content[idx-200:idx+400]))
