import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Add delete button to SellerDashboard ──
dashboard_path = os.path.join(FRONTEND, 'src', 'pages', 'SellerDashboard.tsx')
dashboard = open(dashboard_path, encoding='utf-8').read()

old_edit_link = '''                    <Link to={`/seller/products/${product.id}/edit`} className="text-xs text-orange-500 hover:text-orange-700 transition">
                      {isArabic ? "\u062a\u0639\u062f\u064a\u0644" : "Edit"}
                    </Link>'''

new_edit_link = '''                    <Link to={`/seller/products/${product.id}/edit`} className="text-xs text-orange-500 hover:text-orange-700 transition">
                      {isArabic ? "\u062a\u0639\u062f\u064a\u0644" : "Edit"}
                    </Link>
                    <span className="text-gray-300">|</span>
                    <button onClick={() => deleteProduct(product)} className="text-xs text-red-500 hover:text-red-700 transition">
                      {isArabic ? "\u062d\u0630\u0641" : "Delete"}
                    </button>'''

if 'deleteProduct' not in dashboard:
    # Add deleteProduct function before the return statement
    old_return = '  return ('
    new_fn = '''  const deleteProduct = async (product: any) => {
    if (!window.confirm(`Delete "${product.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/products/seller/${product.id}`);
      setProducts((prev: any[]) => prev.filter((p: any) => p.id !== product.id));
    } catch (e: any) {
      alert(e.response?.data?.detail || "Delete failed");
    }
  };

  return ('''
    dashboard = dashboard.replace(old_return, new_fn, 1)
    if old_edit_link in dashboard:
        dashboard = dashboard.replace(old_edit_link, new_edit_link)
        print("Done - delete button and function added to SellerDashboard")
    else:
        print("FAIL - edit link pattern not found")
        idx = dashboard.find('/seller/products/${product.id}/edit')
        print(repr(dashboard[max(0,idx-100):idx+200]))
    open(dashboard_path, 'w', encoding='utf-8').write(dashboard)
else:
    print("Skip - deleteProduct already exists")

# ── 2. Verify schema has image fields ──
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
schema = open(schema_path, encoding='utf-8').read()
print("\nimage_2 in schema:", 'image_2' in schema)
print("primary_image_index in schema:", 'primary_image_index' in schema)
print("time_unit in schema:", 'time_unit: Optional[str]' in schema)
