content = open('routers/ai.py', encoding='utf-8').read()

new_endpoint = '''
@router.post("/generate-description")
async def ai_generate_description(
    product_name: str = Form(""),
    category: str = Form(""),
    language: str = Form("en"),
    price: str = Form(""),
    image: UploadFile = File(None),
    current_user=Depends(get_current_seller)
):
    """AI listing generator — generates name, description and tags for a product."""
    import os, requests as _requests, base64, json

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    lang_instruction = "Respond in Arabic only." if language == "ar" else "Respond in English only."
    
    # Build message content
    content_parts = []
    
    # Add image if provided
    if image and image.filename:
        img_bytes = await image.read()
        img_b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
        ext = image.filename.split(".")[-1].lower()
        media_type = f"image/{'jpeg' if ext in ['jpg','jpeg'] else ext}"
        content_parts.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": img_b64}
        })

    prompt = f"""You are a UAE marketplace product listing expert. {lang_instruction}
    
Product name: {product_name or "Unknown"}
Category: {category or "General"}
Price: {price + " AED" if price else "Not specified"}

Generate a compelling product listing. Return ONLY valid JSON with these fields:
- suggested_name: A better product name (max 8 words)
- description: Engaging product description (2-3 sentences, highlight quality and benefits)
- tags: Array of 5 relevant search tags
- suggested_price_range: Price range suggestion based on category (e.g. "AED 50-80")

Return only the JSON object, nothing else."""

    content_parts.append({"type": "text", "text": prompt})

    try:
        resp = _requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 500, "messages": [{"role": "user", "content": content_parts}]},
            timeout=30,
        )
        text = resp.json().get("content", [{}])[0].get("text", "{}")
        clean = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

# Add UploadFile and Form imports if needed
if 'from fastapi import' in content and 'UploadFile' not in content:
    content = content.replace('from fastapi import APIRouter, Depends, HTTPException', 'from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form')

if 'get_current_seller' not in content:
    content = content.replace('from core.auth import get_current_user', 'from core.auth import get_current_user, get_current_seller')

content = content + new_endpoint
open('routers/ai.py', 'w', encoding='utf-8').write(content)
print('OK')
