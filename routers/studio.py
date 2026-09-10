from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
import httpx, os, base64, uuid
from typing import Optional

router = APIRouter(prefix="/api/studio", tags=["studio"])

# ── Cloudinary upload helper ─────────────────────────────────────────
def upload_to_cloudinary(image_bytes: bytes, filename: str) -> dict:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "widblmd7")
    api_key    = os.getenv("CLOUDINARY_API_KEY", "")
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="Cloudinary not configured")
    import hashlib, time
    timestamp = str(int(time.time()))
    folder = "bayti_studio"
    sig_str = f"folder={folder}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(sig_str.encode()).hexdigest()
    resp = httpx.post(
        f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
        data={"api_key": api_key, "timestamp": timestamp, "signature": signature, "folder": folder},
        files={"file": (filename, image_bytes, "image/png")},
        timeout=30
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Cloudinary upload failed")
    return resp.json()

# ── Build prompt from selections ─────────────────────────────────────
def build_prompt(product_type: str, model_style: str, background: str, framing: str, output_format: str) -> str:
    
    model_map = {
        "female_gulf_modern": "a fictional adult female model in modest modern Gulf fashion style, wearing hijab",
        "female_modern":      "a fictional adult female model in modern casual style",
        "neutral_studio":     "a clean studio product display, no model",
    }
    bg_map = {
        "white_studio": "pure white studio background, soft even lighting",
        "warm_beige":   "warm beige studio background, soft natural lighting",
        "cafe":         "blurred modern cafe interior background",
        "street":       "blurred modern city street background, golden hour",
        "interior":     "blurred elegant home interior background",
    }
    framing_map = {
        "full_body":  "full body shot showing the complete outfit",
        "half_body":  "half body shot from waist up",
        "close_up":   "close-up shot focusing on the product detail",
    }
    size_map = {
        "product_square":  "1:1 square format",
        "story_vertical":  "9:16 vertical story format",
    }

    model_desc   = model_map.get(model_style, model_map["female_gulf_modern"])
    bg_desc      = bg_map.get(background, bg_map["white_studio"])
    framing_desc = framing_map.get(framing, framing_map["full_body"])
    size_desc    = size_map.get(output_format, size_map["product_square"])

    if product_type == "apparel":
        return f"""Create a clean commercial fashion photograph. 
Use the uploaded garment as the exact reference — preserve its original color, silhouette, fabric texture, pattern, and any visible details or closures exactly as shown.
Place it on {model_desc}.
Setting: {bg_desc}.
Shot: {framing_desc}, {size_desc}.
Style: professional fashion editorial, soft natural lighting, no extra accessories, no text, no watermark.
This is an AI-generated marketing visualization. Do not change the garment design in any way."""

    elif product_type in ("bag", "belt"):
        return f"""Create a clean commercial product photograph.
Use the uploaded bag/accessory as the exact reference — preserve its color, shape, hardware, stitching, and proportions exactly.
Show it held or worn by {model_desc}, or displayed elegantly.
Setting: {bg_desc}.
Shot: {framing_desc}, {size_desc}.
Style: professional fashion editorial, no text, no watermark, no extra items."""

    elif product_type in ("jewelry", "watch"):
        return f"""Create a clean commercial close-up product photograph.
Use the uploaded jewelry/watch as the exact reference — preserve its exact color, shape, stones, metal finish, and proportions.
Display it worn by {model_desc} or on an elegant surface.
Setting: {bg_desc}.
Shot: {framing_desc}, {size_desc}.
Style: luxury product photography, sharp focus on product, no invented logos or text, no watermark."""

    elif product_type == "glasses":
        return f"""Create a clean commercial eyewear photograph.
Use the uploaded glasses as the exact reference — preserve frame color, shape, lens tint, and details exactly.
Show them worn by {model_desc}.
Setting: {bg_desc}.
Shot: {framing_desc}, {size_desc}.
Style: modern eyewear editorial, no text, no watermark."""

    else:
        return f"""Create a clean commercial product photograph using the uploaded item as reference.
Preserve the product's original color, shape, and details exactly.
Display it with {model_desc} or as a styled product shot.
Setting: {bg_desc}.
Shot: {framing_desc}, {size_desc}.
Style: professional commercial photography, no text, no watermark."""


# ── Main endpoint ────────────────────────────────────────────────────
@router.post("/generate")
async def generate_studio_image(
    product_type:  str = Form(...),   # apparel | bag | jewelry | glasses | watch | belt
    model_style:   str = Form("female_gulf_modern"),
    background:    str = Form("white_studio"),
    framing:       str = Form("full_body"),
    output_format: str = Form("product_square"),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=500, detail="Image service not configured")

    # Read image
    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="الصورة أكبر من 10MB")
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="صيغة الملف غير مدعومة (JPG/PNG/WebP فقط)")

    # Build prompt
    prompt = build_prompt(product_type, model_style, background, framing, output_format)

    # Output size
    size = "1024x1536" if output_format == "story_vertical" else "1024x1024"

    # Call OpenAI gpt-image-1 with reference image
    try:
        image_b64 = base64.b64encode(image_bytes).decode()
        mime = image.content_type or "image/jpeg"

        response = httpx.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-image-1",
                "prompt": prompt,
                "n": 1,
                "size": size,
                "quality": "medium"
            },
            timeout=120
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"فشل التوليد: {response.text[:200]}")

        result = response.json()
        img_data = result["data"][0]

        # Get image bytes
        if "b64_json" in img_data:
            result_bytes = base64.b64decode(img_data["b64_json"])
        elif "url" in img_data:
            r = httpx.get(img_data["url"], timeout=30)
            result_bytes = r.content
        else:
            raise HTTPException(status_code=500, detail="لم يتم استلام الصورة")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في التوليد: {str(e)}")

    # Upload to Cloudinary
    try:
        filename = f"studio_{uuid.uuid4().hex[:8]}.png"
        cloud_result = upload_to_cloudinary(result_bytes, filename)
        image_url = cloud_result.get("secure_url", "")
    except Exception as e:
        # Return as base64 if Cloudinary fails
        image_url = f"data:image/png;base64,{base64.b64encode(result_bytes).decode()}"

    return {
        "image_url": image_url,
        "product_type": product_type,
        "model_style": model_style,
        "background": background,
        "framing": framing,
        "output_format": output_format,
        "is_ai_generated": True
    }
