import os
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
            context = "\nSimilar products on the platform:\n"
            for p in similar_products[:5]:
                context += f"- {p['name']}: AED {p['price']}\n"

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
