import os

os.makedirs('services', exist_ok=True)

files = {}

files['services/whatsapp.py'] = '''import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")

def send_whatsapp(to_phone: str, message: str) -> bool:
    """Send a WhatsApp message via Twilio sandbox."""
    try:
        if not account_sid or not auth_token:
            print("Twilio credentials not configured")
            return False
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_phone}",
            body=message
        )
        print(f"WhatsApp sent: {msg.sid}")
        return True
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return False

def notify_seller_new_order(seller_phone: str, seller_name: str, buyer_name: str,
                             items: list, total: float, area: str, notes: str = None):
    """Notify seller when a new order arrives."""
    items_text = ", ".join([f"{item['quantity']}x {item['name']}" for item in items])
    message = (
        f"🛍️ New order on HomeMarket UAE!\\n\\n"
        f"Hello {seller_name},\\n"
        f"📦 Order from: {buyer_name}\\n"
        f"🍽️ Items: {items_text}\\n"
        f"📍 Delivery to: {area}\\n"
        f"💰 Total: AED {total:.2f}\\n"
    )
    if notes:
        message += f"📝 Note: {notes}\\n"
    message += "\\nLog in to HomeMarket UAE to confirm this order."
    return send_whatsapp(seller_phone, message)

def notify_buyer_order_confirmed(buyer_phone: str, buyer_name: str,
                                  shop_name: str, prep_time: int = 60):
    """Notify buyer when seller confirms their order."""
    message = (
        f"✅ Your order is confirmed!\\n\\n"
        f"Hi {buyer_name},\\n"
        f"🏠 {shop_name} has confirmed your order.\\n"
        f"⏱️ Estimated prep time: {prep_time} minutes\\n\\n"
        f"We\\'ll notify you when it\\'s ready for delivery."
    )
    return send_whatsapp(buyer_phone, message)

def notify_buyer_order_ready(buyer_phone: str, buyer_name: str, shop_name: str):
    """Notify buyer when order is out for delivery."""
    message = (
        f"🚴 Your order is on the way!\\n\\n"
        f"Hi {buyer_name},\\n"
        f"Your order from {shop_name} is out for delivery.\\n"
        f"Please be available to receive it. 🏠"
    )
    return send_whatsapp(buyer_phone, message)
'''

files['services/ai_service.py'] = '''import os
import anthropic
import base64
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

def generate_product_description(product_name: str, category: str = None,
                                   price: float = None, image_data: bytes = None,
                                   image_type: str = "image/jpeg") -> dict:
    """
    Use Claude to generate a compelling product description.
    Can analyze an image if provided.
    Returns dict with description, suggested_name, tags, and suggested_price_range.
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)

        if image_data:
            b64_image = base64.standard_b64encode(image_data).decode("utf-8")
            content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_type,
                        "data": b64_image,
                    }
                },
                {
                    "type": "text",
                    "text": f"""You are a food marketing expert for a UAE home-based food marketplace.
Analyze this food photo and generate compelling product listing content.

Product name (if provided): {product_name or "Unknown"}
Category: {category or "Food"}
Price (if set): {f"AED {price}" if price else "Not set"}

Respond in JSON format only, no markdown:
{{
  "description": "2-3 sentence mouth-watering description highlighting ingredients, taste, and occasion. Max 100 words.",
  "suggested_name": "Improved product name if the original needs work, otherwise repeat the original",
  "tags": ["tag1", "tag2", "tag3"],
  "suggested_price_range": "e.g. AED 25-35",
  "preparation_note": "One line about freshness or preparation e.g. Made fresh daily"
}}"""
                }
            ]
        else:
            content = f"""You are a food marketing expert for a UAE home-based food marketplace.
Generate compelling product listing content for:

Product name: {product_name}
Category: {category or "Food"}
Price: {f"AED {price}" if price else "Not set"}

Respond in JSON format only, no markdown:
{{
  "description": "2-3 sentence mouth-watering description. Max 100 words.",
  "suggested_name": "Improved product name if needed, otherwise repeat original",
  "tags": ["tag1", "tag2", "tag3"],
  "suggested_price_range": "e.g. AED 25-35",
  "preparation_note": "One line about freshness or preparation"
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": content}]
        )

        import json
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        result = json.loads(response_text.strip())
        return {"success": True, "data": result}

    except Exception as e:
        print(f"AI service error: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "description": "",
                "suggested_name": product_name,
                "tags": [],
                "suggested_price_range": "",
                "preparation_note": ""
            }
        }

def suggest_price(product_name: str, category: str, similar_products: list = None) -> dict:
    """Suggest a competitive price for a product based on market context."""
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
            messages=[{
                "role": "user",
                "content": f"""You are a pricing expert for a UAE home food marketplace.
Suggest a competitive price for:
Product: {product_name}
Category: {category}
{context}

Consider UAE market rates for home-cooked food. Respond in JSON only:
{{
  "suggested_price": 45,
  "min_price": 35,
  "max_price": 55,
  "reasoning": "One sentence explanation"
}}"""
            }]
        )

        import json
        result = json.loads(message.content[0].text.strip())
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''

files['routers/ai.py'] = '''from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from core.auth import get_current_seller
from services.ai_service import generate_product_description, suggest_price
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import Product, SellerProfile

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/generate-description")
async def generate_description(
    product_name: str = Form(...),
    category: str = Form(None),
    price: float = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_seller)
):
    """Generate AI product description, optionally from an image."""
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
        image_type=image_type
    )
    return result

@router.post("/suggest-price")
async def suggest_price_endpoint(
    product_name: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    """Suggest a competitive price based on similar products."""
    similar = db.query(Product).filter(
        Product.is_available == True
    ).order_by(Product.created_at.desc()).limit(10).all()

    similar_list = [{"name": p.name, "price": p.price} for p in similar]
    result = suggest_price(product_name, category, similar_list)
    return result
'''

for path, content in files.items():
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

print("\nAll service files written!")
