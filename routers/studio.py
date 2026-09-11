from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
    model_size:    str = Form("regular"),
    lighting:      str = Form("soft_natural"),
    season:        str = Form("none"),
    pose:          str = Form("standing_neutral"),
    extra_notes:   str = Form(""),
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

    size_map = {"slim": "slim build", "regular": "regular/average build", "curvy": "curvy/full-figured build"}
    light_map = {"soft_natural": "soft natural daylight", "golden_hour": "warm golden hour sunset light", "studio_bright": "bright clean studio lighting", "moody_dark": "moody dramatic low-key lighting"}
    pose_map = {"standing_neutral": "standing in a natural neutral pose", "walking": "walking dynamically toward the camera", "sitting_elegant": "sitting elegantly", "looking_side": "looking slightly to the side in a candid pose"}
    season_map = {"none": "", "summer": "summer vibes, bright and airy", "winter": "winter cozy atmosphere", "ramadan": "Ramadan elegant festive mood, subtle lantern or crescent elements in background", "eid": "Eid celebration joyful elegant mood"}

    size_desc    = size_map.get(model_size, "regular/average build")
    light_desc   = light_map.get(lighting, "soft natural daylight")
    pose_desc    = pose_map.get(pose, "standing in a natural neutral pose")
    season_desc  = season_map.get(season, "")
    extra_desc   = extra_notes.strip() if extra_notes else ""

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
- Model: {model_desc}, {size_desc}
- Pose: {pose_desc}
- Background: {bg_desc}
- Lighting: {light_desc}
- Shot: {framing_desc}, {format_desc}
- Season/Mood: {season_desc if season_desc else "timeless, no specific season"}
- Style: professional commercial fashion photography, editorial quality
- Special requests: {extra_desc if extra_desc else "none"}

Extract from the image:
1. The EXACT color(s) — be very specific (e.g. "jet black", "ivory white", "dusty rose")
2. Fabric type if visible (silk, cotton, chiffon, velvet, etc.)
3. Key design details (V-neck, tie front, wide sleeves, embroidery, buttons, etc.)
4. Any patterns or textures

Then write ONE detailed prompt starting with "A hyper-realistic professional fashion photograph of" that:
- States the exact color explicitly (e.g. "deep crimson red", not just "red")
- Describes ALL visible design details from the image precisely
- Includes the model description, pose, background, lighting, shot style
- Specifies fabric feel: "soft fleece", "flowing chiffon", "structured cotton", etc.
- Mentions camera technical details at the end: "Shot on Sony A7R V, 85mm f/1.4 lens, shallow depth of field, tack sharp focus on clothing"
- Ends with: "Photorealistic, 8K resolution, professional fashion editorial. No text overlays, no watermarks, no extra logos beyond what is on the garment. AI-generated marketing visualization."

Important for maximum accuracy:
- If the garment has a graphic/print, describe it in exact detail so it is reproduced faithfully
- Specify the exact shade of every color (use paint/pantone-style names)
- Mention fabric weight if visible (heavyweight, lightweight, medium-weight)
- Include styling details: tucked/untucked, layered, accessories worn

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
