content = open(r'C:\Users\Dell\Desktop\homemarketplace\backend\main.py', encoding='utf-8').read()

old = '            Category(name="Home Cooked Meals", icon="\U0001f37d\ufe0f"),\n            Category(name="Desserts & Sweets", icon="\U0001f370"),\n            Category(name="Baked Goods", icon="\U0001f956"),\n            Category(name="Healthy Food", icon="\U0001f957"),\n            Category(name="Juices & Drinks", icon="\U0001f9c3"),\n            Category(name="Handmade Crafts", icon="\U0001f3a8"),\n            Category(name="Beauty & Skincare", icon="\u2728"),\n            Category(name="Perfumes & Candles", icon="\U0001f56f\ufe0f"),'

new = '            Category(name="Home Cooked Meals", name_ar="\u0648\u062c\u0628\u0627\u062a \u0645\u0646\u0632\u0644\u064a\u0629", icon="\U0001f37d\ufe0f"),\n            Category(name="Desserts & Sweets", name_ar="\u062d\u0644\u0648\u064a\u0627\u062a \u0648\u0633\u0643\u0631\u064a\u0627\u062a", icon="\U0001f370"),\n            Category(name="Baked Goods", name_ar="\u0645\u062e\u0628\u0648\u0632\u0627\u062a", icon="\U0001f956"),\n            Category(name="Healthy Food", name_ar="\u0637\u0639\u0627\u0645 \u0635\u062d\u064a", icon="\U0001f957"),\n            Category(name="Juices & Drinks", name_ar="\u0639\u0635\u0627\u0626\u0631 \u0648\u0645\u0634\u0631\u0648\u0628\u0627\u062a", icon="\U0001f9c3"),\n            Category(name="Handmade Crafts", name_ar="\u0645\u0634\u063a\u0648\u0644\u0627\u062a \u064a\u062f\u0648\u064a\u0629", icon="\U0001f3a8"),\n            Category(name="Beauty & Skincare", name_ar="\u062c\u0645\u0627\u0644 \u0648\u0639\u0646\u0627\u064a\u0629 \u0628\u0627\u0644\u0628\u0634\u0631\u0629", icon="\u2728"),\n            Category(name="Perfumes & Candles", name_ar="\u0639\u0637\u0648\u0631 \u0648\u0634\u0645\u0648\u0639", icon="\U0001f56f\ufe0f"),'

if old in content:
    content = content.replace(old, new)
    open(r'C:\Users\Dell\Desktop\homemarketplace\backend\main.py', 'w', encoding='utf-8').write(content)
    print("Done!")
else:
    # Try a simpler direct replacement approach
    import re
    
    def replace_category(m):
        name = m.group(1)
        icon = m.group(2)
        ar_map = {
            "Home Cooked Meals": "وجبات منزلية",
            "Desserts & Sweets": "حلويات وسكريات",
            "Baked Goods": "مخبوزات",
            "Healthy Food": "طعام صحي",
            "Juices & Drinks": "عصائر ومشروبات",
            "Handmade Crafts": "مشغولات يدوية",
            "Beauty & Skincare": "جمال وعناية بالبشرة",
            "Perfumes & Candles": "عطور وشموع",
        }
        name_ar = ar_map.get(name, "")
        if name_ar:
            return f'Category(name="{name}", name_ar="{name_ar}", icon="{icon}")'
        return m.group(0)
    
    new_content = re.sub(r'Category\(name="([^"]+)", icon="([^"]+)"\)', replace_category, content)
    
    if new_content != content:
        open(r'C:\Users\Dell\Desktop\homemarketplace\backend\main.py', 'w', encoding='utf-8').write(new_content)
        print("✅ Fixed via regex!")
    else:
        print("❌ No changes made")
