content = open('main.py', encoding='utf-8').read()

# Add push router import
old = 'from routers import auth, products, orders, sellers, ai, translation, admin, reviews'
new = 'from routers import auth, products, orders, sellers, ai, translation, admin, reviews, push'

if old in content:
    content = content.replace(old, new)
    print('Import OK')
else:
    print('Import NOT FOUND')

# Register push router
old2 = 'app.include_router(reviews.router)'
new2 = 'app.include_router(reviews.router)\napp.include_router(push.router)'

if old2 in content:
    content = content.replace(old2, new2)
    open('main.py', 'w', encoding='utf-8').write(content)
    print('Router OK')
else:
    print('Router NOT FOUND')
