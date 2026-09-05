import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Add delete endpoints to admin.py ──
admin_path = os.path.join(BACKEND, 'routers', 'admin.py')
content = open(admin_path, encoding='utf-8').read()

delete_endpoints = '''

# ── Delete endpoints ──
@router.delete("/sellers/{seller_id}")
def delete_seller(seller_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    user_id = seller.user_id
    # Delete seller's products first (cascade)
    from models.user import Product, Order
    db.query(Product).filter(Product.seller_id == seller_id).delete()
    db.delete(seller)
    # Also delete the user account
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
    db.commit()
    return {"message": "Seller and all their products deleted"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin accounts")
    # If user is a seller, delete seller profile + products first
    if user.role == "seller":
        seller = db.query(Seller).filter(Seller.user_id == user_id).first()
        if seller:
            from models.user import Product
            db.query(Product).filter(Product.seller_id == seller.id).delete()
            db.delete(seller)
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
'''

# Append before the last line
if "delete_seller" not in content:
    content = content.rstrip() + "\n" + delete_endpoints
    open(admin_path, 'w', encoding='utf-8').write(content)
    print("✅ 1. Delete endpoints added to admin.py")
else:
    print("⚠️  Delete endpoints already exist in admin.py")

# ── 2. Add delete buttons to AdminPanel.tsx ──
admin_tsx_path = os.path.join(FRONTEND, 'src', 'pages', 'AdminPanel.tsx')
content2 = open(admin_tsx_path, encoding='utf-8').read()

# Add deleteItem function after the existing state declarations
# Find a good insertion point — after the last useState
delete_fn = '''
  const deleteItem = async (type: 'seller' | 'user', id: number, name: string) => {
    if (!window.confirm(`Delete ${name}? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/admin/${type}s/${id}`);
      alert(`${name} deleted successfully`);
      // Refresh the relevant list
      if (type === 'seller') {
        setSellers(prev => prev.filter((s: any) => s.id !== id));
      } else {
        setUsers(prev => prev.filter((u: any) => u.id !== id));
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Delete failed');
    }
  };
'''

# Find insertion point — after fetchData function or similar
if 'deleteItem' not in content2:
    # Insert after the first useEffect closing brace area — find fetchData or similar
    insert_after = '  }, []);'
    if insert_after in content2:
        # Find the last occurrence (after the main data fetch useEffect)
        idx = content2.rfind(insert_after)
        content2 = content2[:idx + len(insert_after)] + '\n' + delete_fn + content2[idx + len(insert_after):]
        print("✅ 2. deleteItem function added to AdminPanel.tsx")
    else:
        # Try another pattern
        insert_after2 = 'const [activeTab'
        idx2 = content2.find(insert_after2)
        if idx2 > 0:
            # Find end of that line
            eol = content2.find('\n', idx2)
            content2 = content2[:eol+1] + '\n' + delete_fn + content2[eol+1:]
            print("✅ 2. deleteItem function added (fallback)")
        else:
            print("❌ 2. Could not find insertion point for deleteItem")
else:
    print("⚠️  deleteItem already exists")

# ── 3. Add Delete button to sellers table ──
# Find the approve/disable buttons in the sellers tab and add a delete button after them
old_seller_btn = '''                        onClick={() => toggleSeller(s.id, s.user?.is_active)}
                        className={`text-xs px-2 py-1 rounded ${s.user?.is_active ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                        {s.user?.is_active ? (isArabic ? 'تعطيل' : 'Disable') : (isArabic ? 'تفعيل' : 'Enable')}
                      </button>'''

new_seller_btn = '''                        onClick={() => toggleSeller(s.id, s.user?.is_active)}
                        className={`text-xs px-2 py-1 rounded ${s.user?.is_active ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                        {s.user?.is_active ? (isArabic ? 'تعطيل' : 'Disable') : (isArabic ? 'تفعيل' : 'Enable')}
                      </button>
                      <button
                        onClick={() => deleteItem('seller', s.id, s.shop_name)}
                        className="text-xs px-2 py-1 rounded bg-gray-800 text-white hover:bg-red-700 transition">
                        🗑️ {isArabic ? 'حذف' : 'Delete'}
                      </button>'''

if old_seller_btn in content2:
    content2 = content2.replace(old_seller_btn, new_seller_btn)
    print("✅ 3. Delete button added to sellers table")
else:
    # Try a simpler pattern
    old_simple = "bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>"
    if old_simple in content2:
        idx3 = content2.find(old_simple)
        # Find the closing </button> after this
        close_btn = content2.find('</button>', idx3)
        if close_btn > 0:
            insert_pt = close_btn + len('</button>')
            delete_btn_html = '''
                      <button
                        onClick={() => deleteItem('seller', s.id, s.shop_name)}
                        className="text-xs px-2 py-1 rounded bg-gray-800 text-white hover:bg-red-700 transition">
                        🗑️ {isArabic ? 'حذف' : 'Delete'}
                      </button>'''
            content2 = content2[:insert_pt] + delete_btn_html + content2[insert_pt:]
            print("✅ 3. Delete button added to sellers table (fallback)")
        else:
            print("❌ 3. Could not find sellers button insertion point")
    else:
        print("❌ 3. Could not find sellers disable button pattern")

# ── 4. Add Delete button to users table ──
# Find the disable user button pattern
old_user_btn = "onClick={() => toggleUser(u.id, u.is_active)}"
if old_user_btn in content2:
    idx4 = content2.find(old_user_btn)
    close_btn2 = content2.find('</button>', idx4)
    if close_btn2 > 0:
        insert_pt2 = close_btn2 + len('</button>')
        delete_user_btn = '''
                      <button
                        onClick={() => deleteItem('user', u.id, u.full_name)}
                        className="text-xs px-2 py-1 rounded bg-gray-800 text-white hover:bg-red-700 transition ml-1">
                        🗑️ {isArabic ? 'حذف' : 'Delete'}
                      </button>'''
        content2 = content2[:insert_pt2] + delete_user_btn + content2[insert_pt2:]
        print("✅ 4. Delete button added to users table")
    else:
        print("❌ 4. Could not find users button close tag")
else:
    print("❌ 4. Could not find toggleUser pattern")

open(admin_tsx_path, 'w', encoding='utf-8').write(content2)
print("\n🎉 Done! Now push both repos.")
