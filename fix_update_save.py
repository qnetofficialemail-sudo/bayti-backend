import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

old = '        product.image_url = upload_product_image(file_bytes, filename)\n\n    db.commit()\n    db.refresh(product)\n    return product\n\n@router.patch("/{product_id}/restock")'

new = '''        product.image_url = upload_product_image(file_bytes, filename)

    if time_unit is not None: product.time_unit = time_unit
    if primary_image_index is not None: product.primary_image_index = primary_image_index
    for i, extra_img in enumerate([image_2, image_3, image_4, image_5], 2):
        if extra_img and extra_img.filename:
            ext2 = extra_img.filename.split(".")[-1]
            fn2 = f"product_extra_{product.id}_{i}_{ext2}"
            fb2 = await extra_img.read()
            setattr(product, f"image_{i}", upload_product_image(fb2, fn2))

    db.commit()
    db.refresh(product)
    return product

@router.patch("/{product_id}/restock")'''

if 'time_unit is not None' not in content:
    if old in content:
        content = content.replace(old, new)
        open(products_path, 'w', encoding='utf-8').write(content)
        print("Done - update save logic added")
    else:
        print("FAIL")
        idx = content.find('product.image_url = upload_product_image(file_bytes, filename)')
        # Find second occurrence (in update endpoint)
        idx2 = content.find('product.image_url = upload_product_image(file_bytes, filename)', idx+1)
        if idx2 > 0:
            print(repr(content[idx2:idx2+150]))
        else:
            print("Only one occurrence found")
            print(repr(content[idx:idx+150]))
else:
    print("Skip - already patched")
