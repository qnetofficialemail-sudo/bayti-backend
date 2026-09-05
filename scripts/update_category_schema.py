import sys
sys.path.insert(0, '.')
content = open("schemas/schemas.py", encoding="utf-8").read()
content = content.replace(
    "class CategoryOut(BaseModel):\n    id: int\n    name: str\n    icon: Optional[str]",
    "class CategoryOut(BaseModel):\n    id: int\n    name: str\n    name_ar: Optional[str] = None\n    icon: Optional[str]"
)
open("schemas/schemas.py", "w", encoding="utf-8").write(content)
print("CategoryOut schema updated with name_ar")
