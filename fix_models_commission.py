import sys
sys.path.insert(0, '.')

content = open("models/user.py", encoding="utf-8").read()

# Add commission_rate to SellerProfile if missing
if "commission_rate" not in content:
    content = content.replace(
        "    total_orders = Column(Integer, default=0)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())\n    user = relationship",
        "    total_orders = Column(Integer, default=0)\n    commission_rate = Column(Float, default=12.0)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())\n    user = relationship"
    )
    print("Added commission_rate to SellerProfile")
else:
    print("commission_rate already in SellerProfile")

# Add commission_amount to Order if missing
if "commission_amount" not in content:
    content = content.replace(
        "    delivery_fee = Column(Float, default=10.0)\n    notes = Column(Text, nullable=True)",
        "    delivery_fee = Column(Float, default=10.0)\n    commission_amount = Column(Float, default=0.0)\n    notes = Column(Text, nullable=True)"
    )
    print("Added commission_amount to Order")
else:
    print("commission_amount already in Order")

open("models/user.py", "w", encoding="utf-8").write(content)
print("Done!")
