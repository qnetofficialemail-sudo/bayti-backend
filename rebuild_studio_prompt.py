import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"

new_studio = '''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
import os, base64, anthropic

router = APIRouter(prefix="/api/studio", tags=["studio"])

MODEL_LABELS = {
    "female_gulf_modern": "a fictional adult female model wearing hijab, modest modern Gulf fashion style",
    "female_modern":      "a fictional adult female model, modern casual style",
    "neutral_studio":     "clean studio product display without a model",
}
BG_LABELS = {
    "white_studio": "pure white studio background with soft even lighting",
    "warm_beige":   "warm beige studio background with soft natural lighting",
    "cafe":         "blurred modern cafe interior background",
    "street":       "blurred modern city street at golden hour",
    "interior":     "blurred elegant home interior",
}
FRAMING_LABELS = {
    "full_body":  "full body shot",
    "half_body":  "half body shot from waist up",
    "close_up":   "close-up shot focusing on product detail",
}
FORMAT_LABELS = {
    "product_square":  "1:1 square format",
    "story_vertical":  "9:16 vertical story format",
}

@router.post("/analyze")
async def analyze_product(
    product_type:  str = Form(...),
    model_style:   str = Form("female_gulf_modern"),
    background:    str = Form("white_studio"),
    framing:       str = Form("full_body"),
    output_format: str = Form("product_square"),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    # Read image
    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="الصورة أكبر من 10MB")
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="صيغة الملف غير مدعومة")

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    mime = image.content_type or "image/jpeg"

    model_desc   = MODEL_LABELS.get(model_style, MODEL_LABELS["female_gulf_modern"])
    bg_desc      = BG_LABELS.get(background, BG_LABELS["white_studio"])
    framing_desc = FRAMING_LABELS.get(framing, FRAMING_LABELS["full_body"])
    format_desc  = FORMAT_LABELS.get(output_format, FORMAT_LABELS["product_square"])

    type_hints = {
        "apparel":  "clothing item (abaya, dress, top, jacket, etc.)",
        "bag":      "bag or handbag",
        "jewelry":  "jewelry piece (necklace, ring, bracelet, earrings)",
        "glasses":  "eyewear (sunglasses or prescription glasses)",
        "watch":    "watch or timepiece",
        "belt":     "belt or waist accessory",
    }
    type_hint = type_hints.get(product_type, "fashion product")

    system_prompt = """You are a professional fashion photography prompt engineer specializing in AI image generation.
Your job: analyze a product image and generate a perfect, detailed prompt for Gemini image generation.
The prompt must preserve the product's exact color, design, fabric, and details.
Always write prompts in English. Be specific and detailed. Focus on accuracy."""

    user_prompt = f"""Analyze this {type_hint} image carefully and generate a Gemini image generation prompt.

The generated image should show:
- Model: {model_desc}
- Background: {bg_desc}  
- Shot: {framing_desc}, {format_desc}
- Style: professional commercial fashion photography, editorial quality

Extract from the image:
1. The EXACT color(s) — be very specific (e.g. "jet black", "ivory white", "dusty rose")
2. Fabric type if visible (silk, cotton, chiffon, velvet, etc.)
3. Key design details (V-neck, tie front, wide sleeves, embroidery, buttons, etc.)
4. Any patterns or textures

Then write ONE detailed prompt starting with "A hyper-realistic professional fashion photograph of" that:
- States the exact color explicitly
- Describes all design details from the image
- Includes the model, background, shot style
- Ends with: "No text, no watermarks, no logos. AI-generated marketing visualization."

Also provide:
- A SHORT Arabic description of what the prompt will create (2 sentences max)
- 3 tips in Arabic for best results with this specific product

Respond in this exact JSON format:
{{
  "prompt": "...",
  "arabic_description": "...",
  "tips": ["tip1", "tip2", "tip3"],
  "detected_color": "...",
  "detected_fabric": "...",
  "detected_details": "..."
}}"""

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": user_prompt}
            ],
        }]
    )

    import json
    text = response.content[0].text.strip()
    # Clean JSON
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        parsed = json.loads(text[start:end])
    else:
        raise HTTPException(status_code=500, detail="Failed to parse AI response")

    return {
        "prompt": parsed.get("prompt", ""),
        "arabic_description": parsed.get("arabic_description", ""),
        "tips": parsed.get("tips", []),
        "detected_color": parsed.get("detected_color", ""),
        "detected_fabric": parsed.get("detected_fabric", ""),
        "detected_details": parsed.get("detected_details", ""),
        "gemini_url": "https://gemini.google.com",
        "product_type": product_type,
        "model_style": model_style,
        "background": background,
    }
'''

studio_path = os.path.join(BACKEND, "routers", "studio.py")
with open(studio_path, "w", encoding="utf-8") as f:
    f.write(new_studio)
print("✅ Rebuilt studio.py — now generates prompts instead of images")
print("\nDone! Push backend.")
