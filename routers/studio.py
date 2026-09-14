from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
import os, base64, anthropic

router = APIRouter(prefix="/api/studio", tags=["studio"])

# ── فئات المنتجات ──────────────────────────────────────────────────────────────
PRODUCT_CATEGORIES = {
    # ملابس وإكسسوارات
    "apparel":   {"label": "ملابس وعبايات",   "group": "fashion"},
    "bag":       {"label": "حقائب",            "group": "fashion"},
    "jewelry":   {"label": "مجوهرات",          "group": "fashion"},
    "glasses":   {"label": "نظارات",           "group": "fashion"},
    "watch":     {"label": "ساعات",            "group": "fashion"},
    "shoes":     {"label": "أحذية",            "group": "fashion"},
    # منزل وديكور
    "candle":    {"label": "شموع وعطور",       "group": "home"},
    "decor":     {"label": "ديكور منزلي",      "group": "home"},
    "plants":    {"label": "نباتات وأصص",      "group": "home"},
    # طعام وحلويات
    "food":      {"label": "طعام وأكلات",      "group": "food"},
    "sweets":    {"label": "حلويات وكيك",      "group": "food"},
    "drinks":    {"label": "مشروبات وعصائر",   "group": "food"},
    # جمال وعناية
    "skincare":  {"label": "عناية بالبشرة",    "group": "beauty"},
    "makeup":    {"label": "مكياج",            "group": "beauty"},
    "haircare":  {"label": "عناية بالشعر",     "group": "beauty"},
    # يدوي وفن
    "handcraft": {"label": "أعمال يدوية وفن",  "group": "craft"},
}

# ── خيارات الملابس ──────────────────────────────────────────────────────────────
FASHION_MODEL_STYLES = {
    "female_gulf_modern": "a fictional adult female model wearing hijab, modest modern Gulf fashion style",
    "female_modern":      "a fictional adult female model, modern casual contemporary style",
    "female_elegant":     "a fictional adult female model, elegant formal style",
    "neutral_studio":     "clean studio product display without a model, on a mannequin or flat lay",
    "ghost_mannequin":    "invisible ghost mannequin effect showing garment structure clearly",
}
FASHION_POSES = {
    "standing_neutral":  "standing in a natural confident neutral pose, hands relaxed",
    "walking":           "walking dynamically toward the camera, natural movement",
    "sitting_elegant":   "sitting elegantly on a minimal stool or chair",
    "looking_side":      "looking slightly to the side in a candid lifestyle pose",
    "hand_on_hip":       "one hand on hip, confident editorial stance",
    "twirling":          "mid-twirl showing fabric movement and flow",
}
FASHION_SIZES = {
    "slim":    "slim/petite build",
    "regular": "regular/average build",
    "curvy":   "curvy/plus-size full-figured build",
}
FASHION_BACKGROUNDS = {
    "white_studio":  "pure white seamless studio background, professional clean",
    "warm_beige":    "warm beige textured studio background, soft shadows",
    "cream_minimal": "minimal cream off-white background, luxurious feel",
    "cafe":          "blurred modern upscale cafe interior background",
    "street":        "blurred modern Dubai city street at golden hour",
    "garden":        "blurred lush garden with soft dappled sunlight",
    "interior":      "blurred elegant contemporary home interior",
    "desert":        "blurred golden UAE desert dunes at sunset",
}

# ── خيارات المنزل والديكور ──────────────────────────────────────────────────────
HOME_SHOT_STYLES = {
    "flat_lay_overhead":  "perfectly styled flat lay, shot directly from above (bird's eye view)",
    "45_angle":           "shot from a 45-degree angle, classic product photography perspective",
    "lifestyle_scene":    "lifestyle scene styled in a real home setting (shelf, table, windowsill)",
    "close_up_macro":     "extreme close-up macro shot emphasizing texture and material details",
    "hero_shot":          "dramatic hero product shot centered on a pedestal with spotlight",
    "grouped_collection": "group of 3-5 similar products arranged in an aesthetically pleasing composition",
}
HOME_SURFACES = {
    "linen_cream":    "warm cream linen fabric surface, soft and textured",
    "marble_white":   "white Italian marble surface with natural veining",
    "dark_wood":      "rich dark walnut wood surface with natural grain",
    "light_oak":      "light oak wooden surface, Scandinavian minimal feel",
    "concrete_gray":  "cool concrete gray surface, industrial modern aesthetic",
    "travertine":     "warm travertine stone surface, Mediterranean luxury feel",
    "rattan_natural": "natural rattan or wicker surface, tropical bohemian",
}
HOME_MOODS = {
    "warm_cozy":      "warm cozy atmosphere with soft candlelight glow and amber tones",
    "clean_minimal":  "clean minimal Scandinavian aesthetic, white and natural tones",
    "luxury_dark":    "moody luxury dark atmosphere, deep jewel tones and dramatic shadows",
    "botanical":      "botanical lush green vibe with dried flowers and eucalyptus",
    "arabic_heritage":"warm Arabic heritage aesthetic with brass accents and geometric patterns",
    "modern_chic":    "modern chic contemporary styling with metallic accents",
}
HOME_PROPS = {
    "none":            "no additional props, product only",
    "botanicals":      "surrounded by dried pampas grass, eucalyptus, and pressed flowers",
    "candles_ambient": "complemented by lit tea light candles creating warm ambient glow",
    "citrus_fresh":    "styled with fresh cut citrus fruits (lemon, orange) for freshness",
    "coffee_book":     "styled with a book, reading glasses, and a cup of coffee",
    "petals_romantic": "scattered fresh and dried rose petals and small buds",
    "seasonal_eid":    "Eid/Ramadan decor elements: small lantern, dates, crescent accent",
    "herbs_natural":   "fresh herbs like rosemary, lavender, mint for a natural organic feel",
}

# ── خيارات الطعام ──────────────────────────────────────────────────────────────
FOOD_SHOT_STYLES = {
    "overhead_flat":    "overhead flat lay shot, perfect for showcasing the full dish",
    "45_editorial":     "45-degree editorial food photography angle",
    "close_up_steam":   "close-up shot capturing steam, texture, and freshness",
    "plated_hero":      "elegant hero plating shot on a beautiful ceramic plate",
    "rustic_spread":    "rustic abundant spread with multiple dishes on a wooden table",
    "single_hero":      "single product hero shot with perfect lighting and garnish",
}
FOOD_SURFACES = {
    "white_marble":    "clean white marble surface with subtle veining",
    "dark_slate":      "dark slate or black marble surface for contrast",
    "rustic_wood":     "rustic aged wooden table surface",
    "ceramic_plate":   "beautiful artisan ceramic plate or tray",
    "linen_napkin":    "cream linen napkin or tablecloth surface",
    "golden_tray":     "elegant gold serving tray",
}
FOOD_MOODS = {
    "fresh_bright":    "bright airy fresh mood with natural daylight streaming in",
    "warm_homemade":   "warm cozy homemade feel with soft golden kitchen light",
    "luxury_fine":     "fine dining luxury presentation with dramatic side lighting",
    "festive_eid":     "festive Eid/Ramadan celebration mood with lantern elements",
    "cafe_modern":     "modern cafe aesthetic with a cup of Arabic coffee beside",
}
FOOD_GARNISH = {
    "none":            "no additional garnish",
    "herbs_fresh":     "garnished with fresh mint, parsley, or basil leaves",
    "nuts_honey":      "topped with roasted nuts, a drizzle of honey, and powdered sugar",
    "flowers_edible":  "decorated with edible flowers and microgreens",
    "sauce_drizzle":   "with a beautiful artistic sauce drizzle on the plate",
    "powdered_sugar":  "dusted with delicate powdered sugar for an elegant finish",
}

# ── خيارات الجمال ──────────────────────────────────────────────────────────────
BEAUTY_SHOT_STYLES = {
    "flat_lay_clean":   "clean flat lay on a pristine white or marble background",
    "hero_product":     "single hero product shot with dramatic side lighting",
    "lifestyle_vanity": "lifestyle shot styled on a beautiful vanity or dressing table",
    "grouped_routine":  "skincare routine flatlay with complementary products",
    "macro_texture":    "extreme macro close-up showing product texture and consistency",
    "open_product":     "product partially open showing texture, cream, or color inside",
}
BEAUTY_BACKGROUNDS = {
    "white_clean":      "pristine white background, clinical clean luxury",
    "marble_pink":      "soft pink marble surface, feminine luxury aesthetic",
    "cream_linen":      "cream linen fabric, organic natural skincare vibe",
    "dark_luxury":      "deep charcoal or black velvet background, prestige luxury",
    "botanical_green":  "soft botanical green background with plant elements",
    "glass_reflective": "glass reflective surface with subtle caustic light patterns",
}
BEAUTY_PROPS = {
    "none":             "minimal — product only",
    "flowers_pink":     "surrounded by delicate pink and white flower petals",
    "crystals":         "complemented by rose quartz crystals and pearl beads",
    "herbs_botanical":  "styled with fresh botanical elements: lavender, rosehip, chamomile",
    "gold_accents":     "accented with small gold rings, gold leaf, and luxury touches",
    "mirror_elegant":   "reflected in an elegant hand mirror with gold frame",
    "water_splash":     "with a fresh water splash effect suggesting purity and hydration",
}

# ── خيارات الأعمال اليدوية ──────────────────────────────────────────────────────
CRAFT_SHOT_STYLES = {
    "flat_lay":         "artful flat lay arrangement showing the piece at its best",
    "hands_wearing":    "being worn or held by elegant hands with subtle lighting",
    "display_stand":    "displayed on a beautiful jewelry stand or art display",
    "atelier_scene":    "styled in a creative atelier/workshop scene with tools",
    "gift_presentation":"beautifully gift-wrapped or in a luxury gift box",
    "collection_spread":"spread with a collection of related pieces",
}

# ── مشتركة ──────────────────────────────────────────────────────────────────────
LIGHTING_OPTIONS = {
    "soft_natural":    "soft diffused natural daylight from a large window",
    "golden_hour":     "warm golden hour sunlight, long shadows, rich amber tones",
    "studio_bright":   "bright professional studio strobe lighting, even and shadowless",
    "moody_dramatic":  "moody dramatic low-key side lighting, deep shadows",
    "ring_light":      "soft ring light creating a glamorous catchlight",
    "backlit_rim":     "beautiful backlit rim lighting creating a halo effect",
    "candlelight":     "warm intimate candlelight, flickering amber glow",
}
SEASON_OPTIONS = {
    "none":    "",
    "summer":  "summer vibes: bright, airy, fresh, light and breezy atmosphere",
    "winter":  "winter cozy atmosphere: warm blankets, hot drinks, intimate warmth",
    "ramadan": "Ramadan elegant festive mood: crescent moon, lanterns, warm amber light",
    "eid":     "Eid celebration: joyful, festive, luxurious, celebratory colors",
    "national":"UAE National Day: pride, heritage, warm UAE flag color accents",
}
OUTPUT_FORMATS = {
    "product_square":  "1:1 square format, perfect for Instagram feed",
    "story_vertical":  "9:16 vertical format, perfect for Instagram/TikTok stories",
    "landscape_wide":  "16:9 wide landscape format, perfect for banners and covers",
}


@router.post("/analyze")
async def analyze_product(
    # مشتركة
    product_type:   str = Form(...),
    output_format:  str = Form("product_square"),
    lighting:       str = Form("soft_natural"),
    season:         str = Form("none"),
    extra_notes:    str = Form(""),
    # ملابس
    model_style:    str = Form("female_gulf_modern"),
    model_size:     str = Form("regular"),
    pose:           str = Form("standing_neutral"),
    background:     str = Form("white_studio"),
    # منزل/ديكور/شموع
    home_shot_style: str = Form("flat_lay_overhead"),
    home_surface:    str = Form("linen_cream"),
    home_mood:       str = Form("warm_cozy"),
    home_props:      str = Form("botanicals"),
    # طعام
    food_shot_style: str = Form("overhead_flat"),
    food_surface:    str = Form("white_marble"),
    food_mood:       str = Form("warm_homemade"),
    food_garnish:    str = Form("none"),
    # جمال
    beauty_shot_style: str = Form("hero_product"),
    beauty_background: str = Form("white_clean"),
    beauty_props:      str = Form("none"),
    # أعمال يدوية
    craft_shot_style: str = Form("flat_lay"),
    # الصورة
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="الصورة أكبر من 10MB")
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="صيغة الملف غير مدعومة")

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    mime = image.content_type or "image/jpeg"

    # تحديد المجموعة
    category_info = PRODUCT_CATEGORIES.get(product_type, {"label": "منتج", "group": "craft"})
    group = category_info["group"]

    # بناء وصف الخيارات حسب المجموعة
    format_desc  = OUTPUT_FORMATS.get(output_format, OUTPUT_FORMATS["product_square"])
    light_desc   = LIGHTING_OPTIONS.get(lighting, LIGHTING_OPTIONS["soft_natural"])
    season_desc  = SEASON_OPTIONS.get(season, "")
    extra_desc   = extra_notes.strip()

    if group == "fashion":
        model_desc  = FASHION_MODEL_STYLES.get(model_style, FASHION_MODEL_STYLES["female_gulf_modern"])
        pose_desc   = FASHION_POSES.get(pose, FASHION_POSES["standing_neutral"])
        size_desc   = FASHION_SIZES.get(model_size, FASHION_SIZES["regular"])
        bg_desc     = FASHION_BACKGROUNDS.get(background, FASHION_BACKGROUNDS["white_studio"])
        type_hints  = {
            "apparel": "clothing/fashion item (abaya, dress, top, jacket, modest wear, etc.)",
            "bag": "bag or handbag (leather, fabric, designer style)",
            "jewelry": "jewelry piece (necklace, ring, bracelet, earrings, hair accessory)",
            "glasses": "eyewear (sunglasses, prescription glasses, fashion frames)",
            "watch": "watch or timepiece",
            "shoes": "footwear (heels, flats, sneakers, sandals)",
        }
        type_hint = type_hints.get(product_type, "fashion product")

        system_prompt = """You are an elite fashion photography prompt engineer for AI image generation.
Analyze the product image precisely and generate a detailed, professional Gemini prompt.
Preserve exact colors, fabric, pattern, and design details. Always write prompts in English."""

        user_prompt = f"""Analyze this {type_hint} carefully and generate a Gemini AI image generation prompt.

Settings chosen by the seller:
- Model: {model_desc}, {size_desc} build
- Pose: {pose_desc}
- Background: {bg_desc}
- Lighting: {light_desc}
- Shot format: {format_desc}
- Season/mood: {season_desc if season_desc else "timeless, seasonless"}
- Special requests: {extra_desc if extra_desc else "none"}

From the image, extract:
1. EXACT color(s) — be hyper-specific (e.g. "deep mauve purple", "warm ivory with champagne undertones")
2. Fabric type (chiffon, silk, cotton, crepe, nida, linen, velvet, leather, etc.)
3. Every design detail (collar type, sleeve style, length, cuts, embroidery, buttons, ties, panels, etc.)
4. Any prints, patterns, or textures

Generate ONE perfect prompt starting with "A hyper-realistic professional fashion photograph of" that:
- States EXACT color explicitly
- Describes ALL design details precisely
- Includes the full model, pose, background, lighting description
- Specifies fabric drape and feel
- Ends with: "Shot on Sony A7R V, 85mm f/1.4, shallow depth of field, tack-sharp focus on garment. Photorealistic 8K, editorial fashion photography. No text, no watermarks, no logos."

Also provide:
- arabic_description: 2-sentence Arabic description of the expected result
- tips: 3 Arabic tips specific to this product type
- detected_color, detected_fabric, detected_details

JSON only:
{{"prompt":"...","arabic_description":"...","tips":["...","...","..."],"detected_color":"...","detected_fabric":"...","detected_details":"..."}}"""

    elif group == "home":
        shot_desc    = HOME_SHOT_STYLES.get(home_shot_style, HOME_SHOT_STYLES["flat_lay_overhead"])
        surface_desc = HOME_SURFACES.get(home_surface, HOME_SURFACES["linen_cream"])
        mood_desc    = HOME_MOODS.get(home_mood, HOME_MOODS["warm_cozy"])
        props_desc   = HOME_PROPS.get(home_props, HOME_PROPS["botanicals"])
        type_hints = {
            "candle": "candle, reed diffuser, or home fragrance product",
            "decor":  "home decor piece (vase, frame, ornament, sculpture, cushion, etc.)",
            "plants": "plant, succulent, or decorative pot/planter",
        }
        type_hint = type_hints.get(product_type, "home product")

        system_prompt = """You are an expert interior and product photography prompt engineer specializing in home goods, candles, and decor for UAE market.
Generate detailed Gemini image prompts that create stunning, marketplace-ready product photos. Always write in English."""

        user_prompt = f"""Analyze this {type_hint} and generate a Gemini AI image generation prompt.

Settings:
- Shot style: {shot_desc}
- Surface/base: {surface_desc}
- Mood & atmosphere: {mood_desc}
- Props & styling: {props_desc}
- Lighting: {light_desc}
- Format: {format_desc}
- Season/occasion: {season_desc if season_desc else "timeless"}
- Special requests: {extra_desc if extra_desc else "none"}

From the image, extract:
1. Product type, shape, and size
2. Exact color(s) with specific shade names
3. Material/finish (matte, glossy, frosted, ceramic, glass, wooden, etc.)
4. Any labels, text, patterns on the product (describe but specify NO TEXT in final image)
5. Key distinguishing features

Generate ONE perfect product photography prompt starting with "A stunning professional product photograph of" that:
- Describes the exact product appearance faithfully
- Incorporates the chosen shot style, surface, mood, and props naturally
- Creates a cohesive, beautiful scene
- Specifies: "No text or writing anywhere in the image. No logos or labels visible."
- Ends with: "Shot on Phase One IQ4, macro lens, perfect product focus, photorealistic 8K resolution, professional commercial product photography."

Also provide:
- arabic_description: 2 sentences in Arabic describing the expected beautiful result
- tips: 3 Arabic photography tips for this specific product
- detected_color, detected_fabric (material instead), detected_details

JSON only:
{{"prompt":"...","arabic_description":"...","tips":["...","...","..."],"detected_color":"...","detected_fabric":"...","detected_details":"..."}}"""

    elif group == "food":
        shot_desc    = FOOD_SHOT_STYLES.get(food_shot_style, FOOD_SHOT_STYLES["overhead_flat"])
        surface_desc = FOOD_SURFACES.get(food_surface, FOOD_SURFACES["white_marble"])
        mood_desc    = FOOD_MOODS.get(food_mood, FOOD_MOODS["warm_homemade"])
        garnish_desc = FOOD_GARNISH.get(food_garnish, FOOD_GARNISH["none"])
        type_hints = {
            "food":   "homemade cooked dish or meal",
            "sweets": "dessert, sweet, cake, or pastry",
            "drinks": "beverage, juice, smoothie, or drink",
        }
        type_hint = type_hints.get(product_type, "food product")

        system_prompt = """You are a world-class food photography prompt engineer specializing in Middle Eastern and homemade cuisine.

YOUR MOST CRITICAL RULE: The food itself must be reproduced EXACTLY as it appears in the photo — same dish, same ingredients, same colors, same sauces, same toppings, same portions. You are NOT allowed to change, add, or remove any food component.

What you CAN and SHOULD improve:
- The serving plate/bowl (material, color, pattern, elegance)
- The surface/table beneath (wood, marble, fabric, tray)
- The surrounding atmosphere and decor props
- The lighting quality and direction
- The background scene and mood
- Camera angle and framing

What you must NEVER change:
- The food itself
- The sauce or broth covering the food
- The toppings and garnishes already present
- The color and texture of the ingredients
- The quantity and arrangement of the food components

Always write prompts in English."""

        user_prompt = f"""Analyze this {type_hint} image very carefully and generate a Gemini AI image generation prompt.

IMPORTANT: Your job is to PRESERVE the food exactly as-is and only enhance the surrounding environment.

Settings chosen by the seller:
- Shot style: {shot_desc}
- Surface/base: {surface_desc}
- Mood & atmosphere: {mood_desc}
- Additional garnish: {garnish_desc}
- Lighting: {light_desc}
- Format: {format_desc}
- Occasion/season: {season_desc if season_desc else "everyday warm"}
- Special requests: {extra_desc if extra_desc else "none"}

Step 1 — Extract EXACTLY from the image (preserve these in the prompt):
1. Dish name and type
2. EVERY sauce, broth, or liquid present (e.g. yogurt sauce, gravy, syrup — describe its color, consistency, and how it coats the food)
3. EVERY topping visible (nuts, herbs, seeds, etc.) with exact colors
4. Rice/bread/base color and texture exactly
5. Meat/main ingredient appearance exactly
6. Any existing garnish that must be kept

Step 2 — Generate ONE perfect prompt starting with "A mouth-watering professional food photograph of" that:
- Reproduces the food with 100% fidelity — SAME dish, SAME sauce, SAME toppings, SAME colors
- Describes ALL sauces and liquids exactly as they appear (never omit them)
- Places the food on the chosen serving surface: {surface_desc}
- Sets the scene with the chosen mood: {mood_desc}
- Applies the chosen lighting: {light_desc}
- Only adds garnish if seller requested it AND it complements naturally
- Adds life: rising steam wisps, light reflections on sauce, warm bokeh background
- Ends with: "The food is reproduced with photographic accuracy — every sauce, topping, and color is identical to the original. Shot on Canon R5, 100mm macro lens, photorealistic 8K, professional commercial food photography. No text overlays."

Also provide:
- arabic_description: 2 sentences in Arabic describing that the food looks exactly as-is but in a more beautiful setting
- tips: 3 Arabic tips for photographing this specific dish at home
- detected_color, detected_fabric (texture/sauce description), detected_details (list every ingredient and sauce spotted)

JSON only:
{{"prompt":"...","arabic_description":"...","tips":["...","...","..."],"detected_color":"...","detected_fabric":"...","detected_details":"..."}}"""

    elif group == "beauty":
        shot_desc    = BEAUTY_SHOT_STYLES.get(beauty_shot_style, BEAUTY_SHOT_STYLES["hero_product"])
        bg_desc      = BEAUTY_BACKGROUNDS.get(beauty_background, BEAUTY_BACKGROUNDS["white_clean"])
        props_desc   = BEAUTY_PROPS.get(beauty_props, BEAUTY_PROPS["none"])
        type_hints = {
            "skincare": "skincare product (serum, moisturizer, oil, mask, cleanser, etc.)",
            "makeup":   "makeup product (lipstick, eyeshadow, foundation, blush, etc.)",
            "haircare": "hair care product (shampoo, conditioner, hair oil, mask, etc.)",
        }
        type_hint = type_hints.get(product_type, "beauty product")

        system_prompt = """You are a luxury beauty product photography prompt engineer.
Generate stunning, aspirational beauty photography prompts for Gemini AI that rival high-end cosmetics brands.
Always write in English. Focus on elegance, clarity, and desire."""

        user_prompt = f"""Analyze this {type_hint} and generate a Gemini AI image generation prompt.

Settings:
- Shot style: {shot_desc}
- Background: {bg_desc}
- Props & styling: {props_desc}
- Lighting: {light_desc}
- Format: {format_desc}
- Occasion: {season_desc if season_desc else "timeless luxury"}
- Special requests: {extra_desc if extra_desc else "none"}

From the image, extract:
1. Product type (bottle, tube, jar, compact, etc.) and exact shape
2. Exact color of packaging and product
3. Material/finish (glass, plastic, matte, metallic, frosted, etc.)
4. Size and proportions
5. Any visible text or branding (note: final image should have NO TEXT)

Generate ONE perfect luxury beauty photography prompt starting with "A stunning high-end beauty product photograph of" that:
- Conveys luxury, efficacy, and desirability
- Incorporates shot style, background, props seamlessly
- Plays with light reflections, glass caustics, or material sheen
- Specifies: "No text, no labels, no product branding visible in the final image."
- Ends with: "Shot on Hasselblad X2D, 120mm macro, perfect product focus, photorealistic 8K, luxury cosmetics campaign photography."

Also provide:
- arabic_description: 2 sentences in Arabic about the expected luxurious result
- tips: 3 Arabic tips for photographing beauty products beautifully
- detected_color, detected_fabric (material/finish instead), detected_details

JSON only:
{{"prompt":"...","arabic_description":"...","tips":["...","...","..."],"detected_color":"...","detected_fabric":"...","detected_details":"..."}}"""

    else:  # craft
        shot_desc = {
            "flat_lay":          "artful overhead flat lay with beautiful composition",
            "hands_wearing":     "worn or held by elegant feminine hands with soft lighting",
            "display_stand":     "displayed on an elegant jewelry stand or art display pedestal",
            "atelier_scene":     "styled in a creative atelier scene with artistic tools around",
            "gift_presentation": "beautifully gift-wrapped or presented in a luxury gift box",
            "collection_spread": "arranged as a curated collection spread",
        }.get(craft_shot_style, "artful overhead flat lay")

        system_prompt = """You are a creative artisan product photography prompt engineer.
Generate evocative, artistic photography prompts for handmade and craft products for Gemini AI.
Celebrate craftsmanship, uniqueness, and human artistry. Always write in English."""

        user_prompt = f"""Analyze this handmade/artisan product and generate a Gemini AI image generation prompt.

Settings:
- Shot style: {shot_desc}
- Lighting: {light_desc}
- Format: {format_desc}
- Season/occasion: {season_desc if season_desc else "timeless artisan"}
- Special requests: {extra_desc if extra_desc else "none"}

From the image, extract:
1. Craft type (jewelry, macramé, pottery, painting, embroidery, etc.)
2. Exact colors with specific shade names
3. Materials (clay, thread, gold wire, fabric, wood, resin, etc.)
4. Handmade textures and imperfections that show craftsmanship
5. Unique design elements

Generate ONE perfect artisan photography prompt starting with "A beautifully crafted artisan product photograph of" that:
- Celebrates the handmade nature and uniqueness
- Creates a warm, story-telling atmosphere
- Shows texture and craftsmanship detail
- Uses the chosen shot style naturally
- Ends with: "Shot on Sony A7R V, 90mm macro, tack-sharp detail on craftsmanship, photorealistic 8K, fine artisan product photography. No text overlays."

Also provide:
- arabic_description: 2 sentences in Arabic about the expected artistic result
- tips: 3 Arabic tips for photographing this handmade product
- detected_color, detected_fabric (material instead), detected_details

JSON only:
{{"prompt":"...","arabic_description":"...","tips":["...","...","..."],"detected_color":"...","detected_fabric":"...","detected_details":"..."}}"""

    # ── استدعاء Claude ──────────────────────────────────────────────────────────
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": image_b64}},
                {"type": "text", "text": user_prompt}
            ],
        }]
    )

    import json
    text = response.content[0].text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        parsed = json.loads(text[start:end])
    else:
        raise HTTPException(status_code=500, detail="Failed to parse AI response")

    return {
        "prompt":             parsed.get("prompt", ""),
        "arabic_description": parsed.get("arabic_description", ""),
        "tips":               parsed.get("tips", []),
        "detected_color":     parsed.get("detected_color", ""),
        "detected_fabric":    parsed.get("detected_fabric", ""),
        "detected_details":   parsed.get("detected_details", ""),
        "gemini_url":         "https://gemini.google.com",
        "product_type":       product_type,
        "product_group":      group,
    }
