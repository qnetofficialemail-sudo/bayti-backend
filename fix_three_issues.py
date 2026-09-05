import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Check and fix ProductOut schema ──
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
schema = open(schema_path, encoding='utf-8').read()
print("image_2 in schema:", 'image_2' in schema)
print("primary_image_index in schema:", 'primary_image_index' in schema)

if 'image_2' not in schema:
    old = '    image_url: Optional[str]'
    new = '''    image_url: Optional[str] = None
    image_2: Optional[str] = None
    image_3: Optional[str] = None
    image_4: Optional[str] = None
    image_5: Optional[str] = None
    primary_image_index: int = 0
    time_unit: Optional[str] = "minutes"'''
    if old in schema:
        schema = schema.replace(old, new)
        # Remove duplicate time_unit if exists
        open(schema_path, 'w', encoding='utf-8').write(schema)
        print("Done - image fields added to ProductOut schema")
    else:
        print("FAIL - could not find image_url in schema")
        idx = schema.find('image_url')
        print(repr(schema[max(0,idx-50):idx+100]))
else:
    print("Skip - already in schema")

# ── 2. Add delete product endpoint to products router ──
products_path = os.path.join(BACKEND, 'routers', 'products.py')
products = open(products_path, encoding='utf-8').read()

delete_endpoint = '''

@router.delete("/seller/{product_id}")
def seller_delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}
'''

if '/seller/{product_id}' not in products:
    products = products.rstrip() + '\n' + delete_endpoint
    open(products_path, 'w', encoding='utf-8').write(products)
    print("Done - seller delete product endpoint added")
else:
    print("Skip - seller delete endpoint already exists")

# ── 3. Add delete button to SellerDashboard ──
dashboard_path = os.path.join(FRONTEND, 'src', 'pages', 'SellerDashboard.tsx')
dashboard = open(dashboard_path, encoding='utf-8').read()

# Find the edit button pattern in products tab
old_edit_btn = 'onClick={() => navigate(`/seller/products/${p.id}/edit`)}'
if old_edit_btn in dashboard and 'deleteProduct' not in dashboard:
    # Add deleteProduct function
    old_fn = '  const toggleProduct = async'
    new_fn = '''  const deleteProduct = async (product: any) => {
    if (!window.confirm(`Delete "${product.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/products/seller/${product.id}`);
      setProducts(prev => prev.filter((p: any) => p.id !== product.id));
    } catch (e: any) {
      alert(e.response?.data?.detail || "Delete failed");
    }
  };

  const toggleProduct = async'''
    
    if old_fn in dashboard:
        dashboard = dashboard.replace(old_fn, new_fn)
        print("Done - deleteProduct function added")
    else:
        print("FAIL - could not find toggleProduct in SellerDashboard")

    # Add delete button after edit button
    idx = dashboard.find(old_edit_btn)
    close_btn = dashboard.find('</button>', idx)
    if close_btn > 0:
        insert = close_btn + len('</button>')
        delete_btn = '''
                      <button onClick={() => deleteProduct(p)}
                        className="text-xs bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg transition font-medium">
                        {isArabic ? "حذف" : "Delete"}
                      </button>'''
        dashboard = dashboard[:insert] + delete_btn + dashboard[insert:]
        print("Done - delete button added to SellerDashboard")
    else:
        print("FAIL - could not find edit button closing tag")
    
    open(dashboard_path, 'w', encoding='utf-8').write(dashboard)
else:
    if 'deleteProduct' in dashboard:
        print("Skip - deleteProduct already exists")
    else:
        print("FAIL - edit button not found in SellerDashboard")

# ── 4. Add multi-image support to EditProduct ──
edit_path = os.path.join(FRONTEND, 'src', 'pages', 'EditProduct.tsx')
edit = open(edit_path, encoding='utf-8').read()
print("\nimage_2 in EditProduct:", 'image_2' in edit)

if 'image_2' not in edit:
    # Add existing images display - find where current image is shown
    old_img_section = "      <label className=\"block text-sm font-medium text-gray-700 mb-2\">{isArabic ? \"الصورة الحالية\" : \"Current Image\"}</label>"
    if old_img_section in edit:
        new_img_section = '''      <label className="block text-sm font-medium text-gray-700 mb-2">{isArabic ? "الصور الحالية" : "Current Images"}</label>
      <div className="flex gap-2 flex-wrap mb-3">
        {[form.image_url, (form as any).image_2, (form as any).image_3, (form as any).image_4, (form as any).image_5].filter(Boolean).map((img: string, i: number) => (
          <div key={i} className="relative">
            <img src={img.startsWith("http") ? img : `https://web-production-63685.up.railway.app${img}`}
              alt={`Image ${i+1}`} className="w-20 h-20 object-cover rounded-xl border border-gray-200" />
            <span className="absolute bottom-0 left-0 right-0 text-center text-xs bg-black bg-opacity-40 text-white rounded-b-xl py-0.5">
              {i === 0 ? (isArabic ? "رئيسية" : "Main") : i + 1}
            </span>
          </div>
        ))}
      </div>'''
        edit = edit.replace(old_img_section, new_img_section)
        open(edit_path, 'w', encoding='utf-8').write(edit)
        print("Done - existing images shown in EditProduct")
    else:
        print("FAIL - could not find Current Image label in EditProduct")
        idx = edit.find('Current Image')
        if idx > 0:
            print(repr(edit[max(0,idx-100):idx+100]))
        else:
            print("'Current Image' label not found at all")
