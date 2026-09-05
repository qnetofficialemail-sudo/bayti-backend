import sys
sys.path.insert(0, '.')
content = open("models/user.py", encoding="utf-8").read()
if "name_ar" not in content.split("class Category")[1].split("class Product")[0]:
    content = content.replace(
        "    icon = Column(String, nullable=True)\n    products = relationship",
        "    icon = Column(String, nullable=True)\n    name_ar = Column(Text, nullable=True)\n    products = relationship"
    )
    open("models/user.py", "w", encoding="utf-8").write(content)
    print("Category model updated with name_ar")
else:
    print("Category model already has name_ar")
