import os, re

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. models/user.py ── add schedule fields to SellerProfile
model_path = os.path.join(BACKEND, 'models', 'user.py')
content = open(model_path, encoding='utf-8').read()

old = '    commission_rate = Column(Float, default=12.0)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())\n    user = relationship("User", back_populates="seller_profile")'
new = '''    commission_rate = Column(Float, default=12.0)
    # Schedule fields
    available_days = Column(String, nullable=True)        # e.g. "0,1,2,3,4" (Mon-Fri), 0=Mon 6=Sun
    available_from = Column(String, nullable=True)         # e.g. "09:00"
    available_until = Column(String, nullable=True)        # e.g. "21:00"
    accepting_orders = Column(Boolean, default=True)       # manual override
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="seller_profile")'''

if old in content:
    content = content.replace(old, new)
    open(model_path, 'w', encoding='utf-8').write(content)
    print("✅ models/user.py updated")
else:
    print("❌ models/user.py pattern not found")

# ── 2. schemas/schemas.py ── add schedule fields to SellerOut
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
content = open(schema_path, encoding='utf-8').read()
print(f"\nSchema content preview (seller section):")
idx = content.find('commission_rate')
print(content[max(0,idx-100):idx+200])
