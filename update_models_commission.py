import sys
sys.path.insert(0, '.')

content = open("models/user.py", encoding="utf-8").read()

# Add commission_rate to SellerProfile
if "commission_rate" not in content:
    content = content.replace(
        "    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship",
        "    commission_rate = Column(Float, default=12.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship"
    )
    print("Added commission_rate to SellerProfile")

# Add commission_amount to Order
if "commission_amount" not in content:
    content = content.replace(
        "    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at",
        "    notes = Column(Text, nullable=True)
    commission_amount = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at"
    )
    print("Added commission_amount to Order")

open("models/user.py", "w", encoding="utf-8").write(content)
print("Models updated successfully")
