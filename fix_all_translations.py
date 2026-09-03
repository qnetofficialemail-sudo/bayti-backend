import os

files = {}

# Fix 1: Translate categories in database
files['translate_categories.py'] = '''import sys
sys.path.insert(0, '.')
from core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Add name_ar column to categories if not exists
try:
    db.execute(text("ALTER TABLE categories ADD COLUMN name_ar TEXT"))
    db.commit()
    print("Added name_ar column to categories")
except:
    print("Column already exists")

# Arabic category translations
categories_ar = {
    "Home Cooked Meals": "وجبات منزلية",
    "Desserts & Sweets": "حلويات ومعجنات",
    "Baked Goods": "مخبوزات",
    "Healthy Food": "أكل صحي",
    "Juices & Drinks": "عصائر ومشروبات",
    "Handmade Crafts": "حرف يدوية",
    "Beauty & Skincare": "جمال وعناية",
    "Perfumes & Candles": "عطور وشموع",
}

for name_en, name_ar in categories_ar.items():
    db.execute(
        text("UPDATE categories SET name_ar = :name_ar WHERE name = :name"),
        {"name_ar": name_ar, "name": name_en}
    )
    print(f"✅ {name_en} -> {name_ar}")

db.commit()
db.close()
print("Categories translated!")
'''

# Fix 2: Translate the new Arabian product
files['translate_new_product.py'] = '''import sys
sys.path.insert(0, '.')
from core.database import SessionLocal
from sqlalchemy import text
from services.translation import translate_product_to_arabic

db = SessionLocal()
rows = db.execute(text("SELECT id, name, description FROM products WHERE name_ar IS NULL OR name_ar = ''")).fetchall()
print(f"Found {len(rows)} untranslated products")
for row in rows:
    product_id, name, description = row[0], row[1], row[2]
    print(f"Translating: {name}")
    result = translate_product_to_arabic(name, description or name)
    if result["success"]:
        db.execute(
            text("UPDATE products SET name_ar = :name_ar, description_ar = :desc_ar WHERE id = :id"),
            {"name_ar": result["name_ar"], "desc_ar": result["description_ar"], "id": product_id}
        )
        print(f"  -> {result['name_ar']}")
db.commit()
db.close()
print("Done!")
'''

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

print("\nBackend scripts ready!")

# Fix 3: Update AI service to support Arabic output
files['services/ai_service.py'] = '''import os
import anthropic
import base64
import json
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

def generate_product_description(product_name: str, category: str = None,
                                   price: float = None, image_data: bytes = None,
                                   image_type: str = "image/jpeg",
                                   language: str = "en") -> dict:
    try:
        client = anthropic.Anthropic(api_key=api_key)

        lang_instruction = ""
        if language == "ar":
            lang_instruction = "IMPORTANT: Respond entirely in Arabic (العربية). All fields including description, suggested_name, tags, and preparation_note must be in Arabic."
        else:
            lang_instruction = "Respond in English."

        json_format = """{"description": "2-3 sentence mouth-watering description. Max 100 words.", "suggested_name": "Product name", "tags": ["tag1", "tag2", "tag3"], "suggested_price_range": "e.g. AED 25-35", "preparation_note": "One line about freshness or preparation"}"""

        if image_data:
            b64_image = base64.standard_b64encode(image_data).decode("utf-8")
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": image_type, "data": b64_image}},
                {"type": "text", "text": f"""You are a food marketing expert for a UAE home-based food marketplace.
Analyze this food photo and generate compelling product listing content.
{lang_instruction}

Product name (if provided): {product_name or "Unknown"}
Category: {category or "Food"}
Price (if set): {f"AED {price}" if price else "Not set"}

Respond in JSON format only, no markdown:
{json_format}"""}
            ]
        else:
            content = f"""You are a food marketing expert for a UAE home-based food marketplace.
Generate compelling product listing content for:
{lang_instruction}

Product name: {product_name}
Category: {category or "Food"}
Price: {f"AED {price}" if price else "Not set"}

Respond in JSON format only, no markdown:
{json_format}"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": content}]
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        result = json.loads(response_text.strip())
        return {"success": True, "data": result}

    except Exception as e:
        print(f"AI service error: {e}")
        return {"success": False, "error": str(e), "data": {"description": "", "suggested_name": product_name, "tags": [], "suggested_price_range": "", "preparation_note": ""}}

def suggest_price(product_name: str, category: str, similar_products: list = None) -> dict:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        context = ""
        if similar_products:
            context = "\\nSimilar products on the platform:\\n"
            for p in similar_products[:5]:
                context += f"- {p[\'name\']}: AED {p[\'price\']}\\n"

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": f"""You are a pricing expert for a UAE home food marketplace.
Suggest a competitive price for:
Product: {product_name}
Category: {category}
{context}
Respond in JSON only:
{{"suggested_price": 45, "min_price": 35, "max_price": 55, "reasoning": "One sentence explanation"}}"""}]
        )
        result = json.loads(message.content[0].text.strip())
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''

# Fix 4: Update AI router to accept language parameter
files['routers/ai.py'] = '''from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from core.auth import get_current_seller
from services.ai_service import generate_product_description, suggest_price
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import Product

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/generate-description")
async def generate_description(
    product_name: str = Form(...),
    category: str = Form(None),
    price: float = Form(None),
    language: str = Form("en"),
    image: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_seller)
):
    image_data = None
    image_type = "image/jpeg"
    if image:
        image_data = await image.read()
        image_type = image.content_type or "image/jpeg"

    result = generate_product_description(
        product_name=product_name,
        category=category,
        price=price,
        image_data=image_data,
        image_type=image_type,
        language=language
    )
    return result

@router.post("/suggest-price")
async def suggest_price_endpoint(
    product_name: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    similar = db.query(Product).filter(Product.is_available == True).order_by(Product.created_at.desc()).limit(10).all()
    similar_list = [{"name": p.name, "price": p.price} for p in similar]
    result = suggest_price(product_name, category, similar_list)
    return result
'''

# Fix 5: Update categories schema to include name_ar
files['update_category_schema.py'] = '''import sys
sys.path.insert(0, '.')
content = open("schemas/schemas.py", encoding="utf-8").read()
content = content.replace(
    "class CategoryOut(BaseModel):\\n    id: int\\n    name: str\\n    icon: Optional[str]",
    "class CategoryOut(BaseModel):\\n    id: int\\n    name: str\\n    name_ar: Optional[str] = None\\n    icon: Optional[str]"
)
open("schemas/schemas.py", "w", encoding="utf-8").write(content)
print("CategoryOut schema updated with name_ar")
'''

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

print("\\nAll files written!")

files['update_category_model.py'] = '''import sys
sys.path.insert(0, '.')
content = open("models/user.py", encoding="utf-8").read()
if "name_ar" not in content.split("class Category")[1].split("class Product")[0]:
    content = content.replace(
        "    icon = Column(String, nullable=True)\\n    products = relationship",
        "    icon = Column(String, nullable=True)\\n    name_ar = Column(Text, nullable=True)\\n    products = relationship"
    )
    open("models/user.py", "w", encoding="utf-8").write(content)
    print("Category model updated with name_ar")
else:
    print("Category model already has name_ar")
'''

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("All files written!")
