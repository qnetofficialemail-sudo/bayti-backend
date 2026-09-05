import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'

# ── 1. Patch orders.py - track confirmed_at and update avg_response_minutes ──
orders_path = os.path.join(BACKEND, 'routers', 'orders.py')
content = open(orders_path, encoding='utf-8').read()

old = '''    order.status = status
    db.commit()
    return {"order_id": order_id, "status": order.status}'''

new = '''    order.status = status

    # Track response time when seller confirms
    if status == "confirmed" and order.confirmed_at is None:
        from datetime import datetime, timezone as tz
        now = datetime.now(tz.utc)
        order.confirmed_at = now
        if order.created_at:
            created = order.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=tz.utc)
            diff_minutes = (now - created).total_seconds() / 60
            seller_obj = db.query(SellerProfile).filter(SellerProfile.id == order.seller_id).first()
            if seller_obj:
                confirmed_orders = db.query(Order).filter(
                    Order.seller_id == seller_obj.id,
                    Order.confirmed_at != None
                ).order_by(Order.confirmed_at.desc()).limit(19).all()
                times = []
                for co in confirmed_orders:
                    if co.created_at and co.confirmed_at:
                        c = co.created_at
                        cf = co.confirmed_at
                        if c.tzinfo is None:
                            c = c.replace(tzinfo=tz.utc)
                        if cf.tzinfo is None:
                            cf = cf.replace(tzinfo=tz.utc)
                        times.append((cf - c).total_seconds() / 60)
                times.append(diff_minutes)
                seller_obj.avg_response_minutes = round(sum(times) / len(times), 1)

    db.commit()
    return {"order_id": order_id, "status": order.status}'''

if "confirmed_at" not in content:
    if old in content:
        content = content.replace(old, new)
        open(orders_path, 'w', encoding='utf-8').write(content)
        print("Done - response time tracking added to orders.py")
    else:
        print("FAIL - could not find target block in orders.py")
else:
    print("Skip - already patched")

# ── 2. Expose avg_response_minutes in sellers public endpoint ──
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
sellers = open(sellers_path, encoding='utf-8').read()

# Add avg_response_minutes to the public seller profile response
old_rating = '"rating": seller.rating,'
new_rating = '"rating": seller.rating,\n        "avg_response_minutes": seller.avg_response_minutes,'

if "avg_response_minutes" not in sellers:
    if old_rating in sellers:
        sellers = sellers.replace(old_rating, new_rating)
        open(sellers_path, 'w', encoding='utf-8').write(sellers)
        print("Done - avg_response_minutes added to seller public profile")
    else:
        # Try alternate pattern
        old2 = '"total_orders": seller.total_orders,'
        new2 = '"total_orders": seller.total_orders,\n        "avg_response_minutes": seller.avg_response_minutes,'
        if old2 in sellers:
            sellers = sellers.replace(old2, new2)
            open(sellers_path, 'w', encoding='utf-8').write(sellers)
            print("Done - avg_response_minutes added (fallback)")
        else:
            print("FAIL - could not find rating or total_orders in sellers.py")
else:
    print("Skip - already in sellers.py")

# ── 3. Run DB migration ──
print("\nRunning DB migration...")
import sys
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
import subprocess
result = subprocess.run(
    [sys.executable, 'migrate_response_time.py'],
    capture_output=True, text=True, cwd=BACKEND
)
print(result.stdout)
if result.stderr:
    print("ERR:", result.stderr[:300])
