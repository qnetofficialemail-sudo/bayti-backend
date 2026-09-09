content = open('schemas/schemas.py', encoding='utf-8').read()

# Find SellerProfileOut and check what user data it exposes
idx = content.find('class SellerProfileOut')
print(repr(content[idx:idx+600]))
