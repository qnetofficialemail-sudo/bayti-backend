#!/usr/bin/env python3
"""
Patches /app/routers/products.py
Run in Railway Console: python3 /app/patch_backend.py
"""

path = "/app/routers/products.py"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

changes = 0

# ── 1. Add params to update_product signature ───────────────────────────────
old1 = "    track_stock: Optional[bool] = Form(None),\n    primary_image_index: Optional[int] = Form(None),"
new1 = """    track_stock: Optional[bool] = Form(None),
    discount_percent: Optional[float] = Form(None),
    free_shipping_min_amount: Optional[float] = Form(None),
    primary_image_index: Optional[int] = Form(None),"""

if old1 in content:
    content = content.replace(old1, new1)
    print("✅ update_product signature patched")
    changes += 1
else:
    print("⚠️  update_product signature not found")

# ── 2. Add fields update in update_product body ─────────────────────────────
old2 = "    if track_stock is not None: product.track_stock = 1 if track_stock else 0\n    if stock_quantity is not None: product.stock_quantity = stock_quantity"
new2 = """    if track_stock is not None: product.track_stock = 1 if track_stock else 0
    if stock_quantity is not None: product.stock_quantity = stock_quantity
    if discount_percent is not None: product.discount_percent = discount_percent
    if free_shipping_min_amount is not None:
        product.free_shipping_min_amount = free_shipping_min_amount if free_shipping_min_amount > 0 else None"""

if old2 in content:
    content = content.replace(old2, new2)
    print("✅ update_product body patched")
    changes += 1
else:
    print("⚠️  update_product body not found")

# ── 3. Add params to create_product signature ───────────────────────────────
old3 = "    stock_quantity: int = Form(10),\n    track_stock: bool = Form(False),"
new3 = """    stock_quantity: int = Form(10),
    track_stock: bool = Form(False),
    discount_percent: float = Form(0),
    free_shipping_min_amount: Optional[float] = Form(None),"""

if old3 in content:
    content = content.replace(old3, new3)
    print("✅ create_product signature patched")
    changes += 1
else:
    print("⚠️  create_product signature not found")

# ── 4. Add fields to Product() constructor ──────────────────────────────────
old4 = "        stock_quantity=stock_quantity if track_stock else -1,\n        track_stock=1 if track_stock else 0,\n        is_available=True,\n    )"
new4 = """        stock_quantity=stock_quantity if track_stock else -1,
        track_stock=1 if track_stock else 0,
        is_available=True,
        discount_percent=discount_percent if discount_percent and discount_percent > 0 else 0,
        free_shipping_min_amount=free_shipping_min_amount,
    )"""

if old4 in content:
    content = content.replace(old4, new4)
    print("✅ Product() constructor patched")
    changes += 1
else:
    print("⚠️  Product() constructor not found")

# ── Write ────────────────────────────────────────────────────────────────────
with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\n{'✅' if changes == 4 else '⚠️'} Done — {changes}/4 patches applied")
