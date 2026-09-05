content = open(r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\products.py', encoding='utf-8').read()

# Add name_ar and description_ar to the PUT endpoint form fields
old = '''    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    is_available: Optional[bool] = Form(None),
    preparation_time: Optional[int] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    track_stock: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),'''

new = '''    name: Optional[str] = Form(None),
    name_ar: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    description_ar: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    is_available: Optional[bool] = Form(None),
    preparation_time: Optional[int] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    track_stock: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),'''

content = content.replace(old, new)

# Update the function body to handle name_ar/description_ar directly
# Replace the name handling block to not overwrite arabic if provided directly
old2 = '''    if name:
        product.name = name
        try:
            result = translate_product_to_arabic(name, description or product.description or name)
            if result["success"]:
                product.name_ar = result["name_ar"]
                product.description_ar = result["description_ar"]
        except Exception as e:
            print(f"Re-translation failed: {e}")
    if description is not None: product.description = description'''

new2 = '''    if name:
        product.name = name
        # Only auto-translate if no manual Arabic provided
        if not name_ar:
            try:
                result = translate_product_to_arabic(name, description or product.description or name)
                if result["success"]:
                    product.name_ar = result["name_ar"]
                    product.description_ar = result["description_ar"]
            except Exception as e:
                print(f"Re-translation failed: {e}")
    if name_ar is not None: product.name_ar = name_ar
    if description is not None: product.description = description
    if description_ar is not None: product.description_ar = description_ar'''

content = content.replace(old2, new2)

open(r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\products.py', 'w', encoding='utf-8').write(content)
print("✅ products.py updated!")
print("Now push to Railway.")
