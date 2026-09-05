import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
model_path = os.path.join(BACKEND, 'models', 'user.py')
content = open(model_path, encoding='utf-8').read()

old_img = '    image_url = Column(String, nullable=True)'
new_img = '''    image_url = Column(String, nullable=True)
    image_2 = Column(String, nullable=True)
    image_3 = Column(String, nullable=True)
    image_4 = Column(String, nullable=True)
    image_5 = Column(String, nullable=True)
    primary_image_index = Column(Integer, default=0)'''

# Make sure we only replace inside the Product class
# Find the Product class section
product_idx = content.find('class Product(Base):')
seller_idx = content.find('class SellerProfile(Base):')

if product_idx > 0:
    product_section = content[product_idx:product_idx+1000]
    if 'image_2 = Column' not in product_section:
        if old_img in product_section:
            # Replace only within product section
            new_product_section = product_section.replace(old_img, new_img, 1)
            content = content[:product_idx] + new_product_section + content[product_idx+1000:]
            open(model_path, 'w', encoding='utf-8').write(content)
            print("Done - image_2..5 and primary_image_index added to Product model")
        else:
            print("FAIL - image_url not found in Product class")
            print(repr(product_section[:500]))
    else:
        print("Skip - already in Product model")
else:
    print("FAIL - Product class not found")
