path = r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\orders.py'
content = open(path, encoding='utf-8').read()

# Find the seller orders return dict and expand it
old = '''        "delivery_area": o.delivery_area,
            "created_at": o.created_at,
            "items": [{
                "quantity": item.quantity,
                "product": {"name": item.product.name if item.product else "Deleted"} if item.product else None
            } for item in o.items]'''

new = '''        "delivery_address": o.delivery_address,
            "delivery_area": o.delivery_area,
            "notes": o.notes,
            "created_at": o.created_at,
            "buyer": {
                "full_name": o.buyer.full_name if o.buyer else "",
                "phone": o.buyer.phone if o.buyer else ""
            },
            "items": [{
                "quantity": item.quantity,
                "product": {
                    "name": item.product.name if item.product else "Deleted",
                    "price": item.product.price if item.product else 0
                } if item.product else None
            } for item in o.items]'''

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ Seller orders now include full address, notes and buyer info")
else:
    # Show all delivery_area occurrences
    import re
    for m in re.finditer(r'delivery_area', content):
        print(f"Found at {m.start()}:")
        print(repr(content[max(0,m.start()-100):m.start()+200]))
        print("---")
