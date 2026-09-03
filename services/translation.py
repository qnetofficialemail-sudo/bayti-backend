import anthropic
import os
import json
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

def translate_product_to_arabic(name: str, description: str, category: str = None) -> dict:
    """Translate product name and description to Arabic using Claude."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""You are a professional Arabic translator specializing in food and marketplace content for the UAE.
Translate the following product listing to Modern Standard Arabic (فصحى).
Make it sound natural, appetizing, and culturally appropriate for UAE customers.

Product name: {name}
Description: {description}
Category: {category or "Food"}

Respond in JSON format only, no markdown:
{{
  "name_ar": "Arabic product name",
  "description_ar": "Arabic product description"
}}"""
            }]
        )
        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        result = json.loads(response_text.strip())
        return {"success": True, "name_ar": result["name_ar"], "description_ar": result["description_ar"]}
    except Exception as e:
        print(f"Translation error: {e}")
        return {"success": False, "name_ar": None, "description_ar": None}
