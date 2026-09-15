from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from core.database import get_db
from core.auth import get_current_seller, get_current_admin
from pydantic import BaseModel
from typing import List, Optional
import os
import requests

router = APIRouter(prefix="/api/ai", tags=["ai"])

class ShopperRequest(BaseModel):
    query: str
    products: List[dict]

@router.post("/shopper")
def ai_personal_shopper(data: ShopperRequest):
    """AI Personal Shopper — recommends products based on buyer query."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    system_prompt = """You are Bayti's AI Personal Shopper for a UAE local marketplace.
Recommend the best matching products from the available inventory based on what the buyer is looking for.
Always respond in the same language the buyer uses (Arabic or English).
Return ONLY a valid JSON array of exactly 3 recommendations (or fewer if less than 3 products match).
Each recommendation must have: product_id (number), reason (string, max 20 words, warm and personal tone).
Example: [{"product_id": 1, "reason": "Perfect oud scent under AED 150, handmade by a local Dubai seller."}]
ONLY return the JSON array, nothing else."""

    user_prompt = f"""Buyer request: "{data.query}"

Available products:
{str(data.products[:50])}

Return 3 product recommendations as JSON array."""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=30,
        )
        result = response.json()
        text = result.get("content", [{}])[0].get("text", "[]")
        import json
        clean = text.replace("```json", "").replace("```", "").strip()
        recommendations = json.loads(clean)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PricingRequest(BaseModel):
    product_name: str
    category: str
    category_id: int | None = None
    price: float
    lang: str = "ar"

@router.post("/pricing-advisor")
def ai_pricing_advisor(data: PricingRequest):
    """AI Pricing Advisor — real UAE market prices via web search."""
    import json, statistics, re, anthropic
    from core.database import SessionLocal
    from models.user import Product

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    # ── Step 1: بيانات بيتي الداخلية للمقارنة ─────────────────────
    db = SessionLocal()
    try:
        all_products = db.query(Product).filter(Product.price > 0).limit(500).all()
    finally:
        db.close()

    def get_keywords(text):
        stop_words = {"من", "في", "على", "مع", "هذا", "هذه", "و", "the", "and", "with", "for", "of", "a", "an"}
        words = re.findall(r"[\w\u0600-\u06FF]{3,}", text.lower())
        result = set()
        for w in words:
            if w not in stop_words:
                result.add(w)
        return result

    query_keywords = get_keywords(data.product_name)
    matched_ids = set()
    for p in all_products:
        product_keywords = get_keywords(p.name) | get_keywords(p.name_ar or "")
        if query_keywords & product_keywords:
            matched_ids.add(p.id)
    if data.category_id:
        for p in all_products:
            if p.category_id == data.category_id:
                matched_ids.add(p.id)

    bayti_prices = [p.price for p in all_products if p.id in matched_ids]
    bayti_context = ""
    if len(bayti_prices) >= 2:
        bayti_context = f"Internal Bayti marketplace data: {len(bayti_prices)} similar products, range AED {int(min(bayti_prices))}–{int(max(bayti_prices))}, avg AED {int(statistics.mean(bayti_prices))}."

    # ── Step 2: Web Search للسوق الإماراتي ────────────────────────
    client = anthropic.Anthropic(api_key=api_key)

    WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search"}

    system_prompt = f"""You are a UAE market pricing analyst. Your job:
1. Search for real prices of the given product in UAE markets (noon.com, Instagram UAE sellers, Carrefour UAE, Amazon.ae, local UAE sellers).
2. Analyze the prices found.
3. Return a JSON object with your findings.

Rules:
- Search in English for better results (translate Arabic product names to English first)
- Focus on UAE market prices only (AED currency)
- Ignore prices from outside UAE
- Be realistic — handmade/homemade products typically cost more than supermarket items
- {bayti_context if bayti_context else "No internal marketplace data available yet."}
- Language for advice text: {"Arabic (فصحى خفيفة)" if data.lang == "ar" else "English"}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "market_min": <lowest price found in AED, number>,
  "market_max": <highest price found in AED, number>,
  "market_avg": <average price in AED, number>,
  "sources_found": ["source1", "source2"],
  "verdict": "low" or "good" or "high" or "unique",
  "verdict_reason": "<one sentence why, in the response language>",
  "tip": "<one practical tip max 15 words, in the response language>",
  "search_summary": "<what you found in 1 sentence>"
}}

Verdict logic:
- "low": seller price is below 85% of market min — they are undercharging
- "good": seller price is within market range +/- 15%
- "high": seller price exceeds market max by more than 15%
- "unique": could not find similar products in UAE market"""

    user_msg = f"""Product: "{data.product_name}"
Category: {data.category}
Seller's current price: AED {data.price}

Search for this product's price in UAE markets now.
Search queries to try:
1. "{data.product_name} price UAE AED"
2. "{data.product_name} noon.com UAE"
3. "{data.product_name} Dubai buy online"
4. If product name is Arabic, also search the English translation

After searching, analyze what you found and return the JSON."""

    # ── Step 3: Multi-turn tool use ────────────────────────────────
    messages = [{"role": "user", "content": user_msg}]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_prompt,
        tools=[WEB_SEARCH_TOOL],
        messages=messages,
    )

    for _ in range(6):
        if response.stop_reason != "tool_use":
            break
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Search completed successfully"
                })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system_prompt,
            tools=[WEB_SEARCH_TOOL],
            messages=messages,
        )

    # ── Step 4: استخراج JSON ───────────────────────────────────────
    final_text = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            final_text = block.text
            break

    final_text = final_text.strip().replace("```json", "").replace("```", "").strip()

    try:
        start = final_text.find("{")
        end = final_text.rfind("}") + 1
        parsed = json.loads(final_text[start:end])
    except Exception:
        return {
            "verdict": "unique",
            "suggestion": "لم نتمكن من العثور على أسعار مشابهة في السوق الإماراتي حالياً." if data.lang == "ar" else "Could not find comparable prices in UAE market right now.",
            "min": None,
            "max": None,
            "sources": [],
            "search_summary": ""
        }

    # ── Step 5: الرد النهائي ───────────────────────────────────────
    verdict = parsed.get("verdict", "unique")
    market_min = parsed.get("market_min")
    market_max = parsed.get("market_max")
    tip = parsed.get("tip", "")
    verdict_reason = parsed.get("verdict_reason", "")
    sources = parsed.get("sources_found", [])
    search_summary = parsed.get("search_summary", "")
    suggestion = f"{verdict_reason} {tip}".strip()

    return {
        "verdict": verdict,
        "suggestion": suggestion,
        "min": int(market_min) if market_min else None,
        "max": int(market_max) if market_max else None,
        "sources": sources[:3],
        "search_summary": search_summary,
        "bayti_context": bayti_context
    }


@router.get("/demand-forecast")
def ai_demand_forecast(db: Session = Depends(get_db)):
    """AI Demand Forecasting — UAE seasonal demand spikes per category."""
    from core.database import SessionLocal
    from models.user import Category
    import json, datetime

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    db2 = SessionLocal()
    try:
        categories = db2.query(Category).filter(Category.is_active == True).all()
        cat_names = [{"id": c.id, "name": c.name, "name_ar": c.name_ar} for c in categories]
    finally:
        db2.close()

    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year

    prompt = f"""You are a UAE marketplace demand analyst. Today is month {current_month} of {current_year}.

UAE seasonal calendar:
- Ramadan (March/April): high demand for food, gifts, home decor, modest fashion
- Eid Al-Fitr (April): very high demand for fashion, accessories, gifts, sweets
- Eid Al-Adha (June/July): high demand for fashion, home goods, gifts
- Back to school (August/September): accessories, stationery, fashion
- UAE National Day (December 2): home decor, gifts, UAE-themed products
- Dubai Shopping Festival (December/January): all categories spike
- Mother's Day UAE (March 21): gifts, candles, beauty, accessories
- Valentine's Day (February 14): candles, gifts, accessories

Categories on Bayti: {json.dumps(cat_names)}

For each category, provide a demand forecast for the next 4 months.
Return ONLY a valid JSON array. Each item must have:
- category_id (number)
- category_name (string, in English)
- monthly_demand (array of 6 objects, each with: month (1-12), year (number), demand_index (0-100), season_label (string, short), season_label_ar (string in Arabic))
- top_season (string, the single biggest upcoming opportunity in English)
- top_season_ar (string, same in Arabic)
- tip (string, one actionable tip in English, max 15 words)
- tip_ar (string, same tip in Arabic)

Return only the JSON array, nothing else."""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        result = response.json()
        text = result.get("content", [{}])[0].get("text", "[]")
        clean = text.replace("```json", "").replace("```", "").strip()
        forecasts = json.loads(clean)
        return {"forecasts": forecasts, "current_month": current_month, "current_year": current_year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

    content_parts = []

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


@router.post("/instagram-content")
def generate_instagram_content(data: dict):
    """Generate Instagram post caption + AI image for Bayti"""
    import anthropic, base64, httpx, os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    topic = data.get("topic", "دعوة البائعات المنزليات للانضمام إلى بيتي")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system="""أنت مدير محتوى إنستقرام لمنصة بيتي — سوق محلي في الإمارات للبائعين المنزليين و غيرهم.
الموقع في مرحلة تجريبية. اكتب بالعربية الفصحى الخفيفة. لا تخترع أرقاماً.
الأسلوب: دافئ، مشجع، احترافي. هوية بيتي: برتقالي دافئ، كريمي، طابع منزلي دافئ.
مهم: لا تخصّص المحتوى لجنسية معينة — الموقع لجميع المقيمين في الإمارات بغض النظر عن جنسيتهم.
لا تكتب "الإماراتية" أو "الإماراتيات" للإشارة للبائعات — اكتب "المقيمين في الإمارات" أو "بائعي الإمارات" فقط.""",
        messages=[{
            "role": "user",
            "content": f"""أنشئ منشور إنستقرام عن: {topic}

أعطني JSON فقط بهذا الشكل:
{{
  "caption": "نص المنشور — يبدأ بجملة قوية، إيموجي، ١٥٠-٢٠٠ كلمة، ينتهي بـ:\n\n🔗 سجّلي الآن: bayti.ink/sell",
  "image_prompt": "Creative Instagram-worthy photograph related to [{topic}]. Choose ONE of these styles randomly: (1) Warm lifestyle flat lay with handmade UAE products, morning golden light, linen texture, terracotta and cream tones (2) Moody overhead shot, dark wood surface, candles lit, dramatic shadows, rich amber and orange (3) Bright airy aesthetic, white marble, fresh flowers, pastel accents, clean minimalist (4) Rustic outdoor scene, natural stone surface, dried botanicals, earthy browns and warm greens (5) Elegant luxury setup, velvet fabric, gold accents, deep jewel tones, sophisticated lighting. Make it photorealistic, highly detailed, unique composition. No people, no text, no logos, no faces."
}}"""
        }]
    )

    import json as json_lib
    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    parsed = json_lib.loads(text[start:end])

    image_url = None
    if openai_key:
        try:
            img_response = httpx.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-image-1",
                    "prompt": parsed["image_prompt"] + ". No people, no text, no logos.",
                    "n": 1,
                    "size": "1024x1024"
                },
                timeout=60
            )
            img_data = img_response.json()["data"][0]
            if "url" in img_data:
                image_url = img_data["url"]
            elif "b64_json" in img_data:
                image_url = f"data:image/png;base64,{img_data['b64_json']}"
        except Exception:
            pass

    HASHTAGS_AR = "#بيتي #بيع_من_البيت #بائعات_الإمارات #منتجات_محلية #bayti"
    HASHTAGS_EN = "#bayti #UAEshopping #DubaiFinds #HomeBusiness #HandmadeUAE #UAEsellers #ShopLocalUAE #MadeInUAE #DubaiHandmade #WomenInBusiness"
    lang = data.get("lang", "ar")
    HASHTAGS = HASHTAGS_AR if lang == "ar" else HASHTAGS_EN
    return {
        "caption": parsed["caption"],
        "hashtags": HASHTAGS,
        "image_url": image_url,
        "topic": topic
    }


@router.post("/instagram-content-v2")
def generate_instagram_content_v2(data: dict):
    """Generate Instagram content — text only (3 types: sellers, events, value)"""
    import anthropic, httpx, os, datetime, random, json as json_lib

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    client = anthropic.Anthropic(api_key=api_key)
    content_type = data.get("type", "sellers")

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4)))
    current_date = now.strftime("%B %d, %Y")
    current_month = now.strftime("%B")

    HASHTAGS_AR = "#بيتي #بيع_من_البيت #بائعات_الإمارات #منتجات_محلية #bayti"
    HASHTAGS_EN = "#bayti #UAEshopping #DubaiFinds #HomeBusiness #HandmadeUAE #UAEsellers #ShopLocalUAE #MadeInUAE #DubaiHandmade #WomenInBusiness"
    lang = data.get("lang", "ar")
    HASHTAGS = HASHTAGS_AR if lang == "ar" else HASHTAGS_EN

    if content_type == "sellers":
        topics = [
            "دعوة البائعين في الإمارات للانضمام إلى بيتي قبل الإطلاق الرسمي",
            "مميزات البيع عبر بيتي — الذكاء الاصطناعي يكتب وصف منتجك",
            "استوديو بيتي الذكي — حوّل صورة منتجك إلى صورة تسويقية احترافية مجاناً",
            "بيتي ليس فقط للمنتجات اليدوية — كل من يبيع في الإمارات مرحب به",
            "هل تستوردين منتجات وتبيعينها؟ بيتي مكانك",
            "صورة منتج احترافية بدون كاميرا ولا مصور — مع استوديو بيتي",
            "نصيحة للبائع المبتدئ: كيف تصوّر منتجك باحترافية",
            "استطلاع: أي فئة تفضلون؟ شموع، عبايات، حلويات، إكسسوارات؟",
            "كن من الأوائل — مميزات حصرية لمن يسجّل الآن",
            "بيتي والبائعون: قصة نبنيها معاً في الإمارات",
            "رحلة من البيت أو المستودع إلى الزبون — كيف يعمل بيتي",
            "لماذا بيتي يختلف عن البيع عبر إنستقرام؟",
            "خلف الكواليس: كيف نبني بيتي",
            "كيف تحدد سعر منتجك بذكاء؟",
            "أخطاء شائعة يقع فيها البائعون المبتدئون",
            "كيف تصوّر منتجك باحترافية من المنزل؟",
            "كيف تكتب وصفاً جذاباً لمنتجك؟",
            "كيف تجد زبائنك الأوائل في الإمارات؟",
            "من يمكنه البيع عبر بيتي؟ الجواب سيفاجئك",
            "خاصية الخصم في بيتي — كيف تستخدمينها بذكاء لتبيعي أكثر",
            "التوصيل المجاني من بيتي — كيف يزيد مبيعاتك تلقائياً",
            "الرفع المتعدد الذكي في بيتي — أضف 20 منتج في دقائق بدل ساعات",
        ]
        topics_en = [
            "Inviting UAE-based sellers to join Bayti before official launch",
            "Why selling on Bayti is smarter — AI writes your product listings",
            "Bayti Smart Studio: turn your product photo into a professional marketing image — free",
            "Bayti is not just for handmade — all sellers in the UAE are welcome",
            "Do you import products and resell them? Bayti is your place",
            "Get a professional product photo without a camera — with Bayti Studio",
            "Beginner tip: how to photograph your product professionally",
            "Poll: which category do you prefer? Candles, abayas, sweets, accessories?",
            "Be one of the first — exclusive perks for early sellers",
            "Bayti and sellers: a story we build together in the UAE",
            "From home or warehouse to customer — how Bayti works",
            "Why Bayti is better than selling on Instagram",
            "Behind the scenes: how we built Bayti",
            "How to price your product smartly",
            "Common mistakes new sellers make",
            "How to write an attractive product description",
            "How to find your first customers in the UAE",
            "Who can sell on Bayti? The answer will surprise you",
            "The smart bulk upload on Bayti — add 20 products at once",
        ]
        topic = random.choice(topics_en if lang == "en" else topics)

        system_en = """You are an Instagram content manager for Bayti — a UAE local marketplace connecting sellers and buyers.
The platform is in beta. Write in clear, warm, professional English. Don't invent numbers.
Sellers are diverse: handmade makers, home cooks, importers, resellers — all welcome.
Don't limit content to one nationality. Write "sellers in the UAE" or "UAE residents".

Bayti features you can mention:
- AI writes product descriptions from photos automatically
- Bayti Smart Studio: generates professional marketing photos free
- Smart Pricing Advisor: scans real competitor prices across the UAE market and suggests the optimal price for each product — no guessing, no manual research
- Easy dashboard to manage products and orders
- Wide audience across the UAE
- Free during beta
- Smart bulk upload: upload up to 20 photos at once, AI writes name and description
- Discount % feature: add discount on any product
- Free shipping feature: set minimum order for free delivery

When mentioning the Smart Pricing Advisor, describe it as: a tool that analyzes live UAE market prices from real competitors and recommends the ideal price — never say "Claude" or "AI model", say "Smart Pricing Advisor" or "intelligent pricing tool"."""

        system = """أنت مدير محتوى إنستقرام لمنصة بيتي — منصة محلية في الإمارات تجمع البائعين والمشترين.
الموقع في مرحلة تجريبية. اكتب بالعربية الفصحى دائماً، لا عامية. لا تخترع أرقاماً.
الأسلوب: دافئ، مشجع، احترافي.

مهم جداً:
- لا تقل "منصة إماراتية" بل "منصة محلية في الإمارات"
- لا تخصّص المحتوى لجنسية معينة — المنصة لجميع المقيمين في الإمارات
- البائعون متنوعون: من يصنع يدوياً، من يطبخ، ومن يستورد بضائع ويعيد بيعها
- لا تقتصر على "المنتجات المنزلية اليدوية" فقط

مميزات بيتي التي يمكنك ذكرها:
- الذكاء الاصطناعي يكتب وصف المنتج تلقائياً من الصورة
- استوديو بيتي الذكي: يولّد صوراً تسويقية احترافية مجاناً
- مستشار التسعير الذكي: يحلل أسعار المنافسين الفعليين في السوق الإماراتي ويقترح السعر الأمثل لكل منتج تلقائياً — بلا تخمين ولا مقارنة يدوية
- لوحة تحكم سهلة لإدارة المنتجات والطلبات
- وصول لجمهور واسع في الإمارات
- بدون عمولة في المرحلة التجريبية
- خاصية الخصم: أضف نسبة خصم % على أي منتج — يظهر السعر الأصلي مشطوباً وbadge أحمر للمشتري
- خاصية التوصيل المجاني: حدد مبلغ أدنى للطلب ويتحول التوصيل لمجاني تلقائياً
- رفع متعدد ذكي: ارفع حتى 20 صورة دفعة واحدة، جمّعها حسب المنتج، والذكاء الاصطناعي يكتب الاسم والوصف تلقائياً لكل مجموعة

عند ذكر مستشار التسعير الذكي: صفه دائماً بأنه يحلل أسعار السوق الإماراتي الفعلية ويوصي بالسعر الأمثل — لا تقل "كلود" أو "نموذج ذكاء اصطناعي"، قل "مستشار التسعير الذكي" أو "أداة التسعير الذكية"."""

        if lang == "en":
            user_msg_en = f"""Create an Instagram post about: {topic}

Write the text directly without JSON, without extra headers.
Start with a catchy strong sentence, relevant emojis, 150-200 words.
End exactly with:
🔗 Join now: bayti.ink/sell"""
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=system_en,
                messages=[{"role": "user", "content": user_msg_en}]
            )
        else:
            user_msg_ar = f"""أنشئ منشور إنستقرام عن: {topic}

اكتب النص مباشرة بدون JSON وبدون عناوين.
يبدأ بجملة جذابة قوية، إيموجي مناسبة، ١٥٠-٢٠٠ كلمة.
ينتهِ بـ:
🔗 سجّلي الآن: bayti.ink/sell"""
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": user_msg_ar}]
            )

        caption = response.content[0].text.strip()
        return {"caption": caption, "hashtags": HASHTAGS, "image_url": None, "type": content_type, "event": ""}

    elif content_type == "events":
        system_en = """You are an Instagram content manager specialized in UAE-related content.
Search for the most notable positive news or event in the UAE today and write a post about it.
Strict rules:
- Write in warm, professional English
- Completely avoid: politics, wars, crimes, accidents, any negative news
- Focus on: events, festivals, openings, achievements, food, art, sports, weather
- Do not mention Bayti or any platform in the post
- End with an engaging question, then: Follow us for more 🏡"""

        system_ar = """أنت مدير محتوى إنستقرام متخصص في المحتوى الإماراتي.
ابحث عن أبرز خبر أو فعالية إيجابية في الإمارات اليوم واكتب منشوراً عنه.
قواعد صارمة:
- اكتب بالعربية الفصحى الخفيفة
- تجنّب تماماً: السياسة، الحروب، الجرائم، الحوادث، أي أخبار سلبية
- ركّز على: الفعاليات، المهرجانات، الافتتاحات، الإنجازات، الطعام، الفن، الرياضة، الطقس
- لا تذكر بيتي أو أي منصة في المنشور
- انهِ بسؤال تفاعلي ثم: تابعونا لمزيد 🏡"""

        system = system_en if lang == "en" else system_ar

        WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search"}

        if lang == "en":
            user_msg = f"""Today: {current_date}

Search now for the most notable positive news or event in the UAE today or this week.
Search for: UAE events {current_month} 2026, Dubai festivals today, Abu Dhabi events

After searching, choose the most positive and appealing one and give me JSON only:
{{
  "event": "Event title",
  "caption": "Instagram post in English — engaging, 150-200 words, an interactive question, then:\n\nFollow us for more 🏡",
  "hashtags": "5 hashtags: 2-3 about the event + #bayti + #UAE"
}}"""
        else:
            user_msg = f"""اليوم: {current_date}

ابحث الآن عن أبرز خبر أو فعالية إيجابية في الإمارات اليوم أو هذا الأسبوع.
ابحث عن: UAE events {current_month} 2026, Dubai festivals today, Abu Dhabi events, فعاليات الإمارات اليوم

بعد البحث اختر الأكثر إيجابية وجمالاً وأعطني JSON فقط:
{{
  "event": "عنوان الحدث",
  "caption": "منشور إنستقرام بالعربية الفصحى الخفيفة — جذاب، ١٥٠-٢٠٠ كلمة، سؤال تفاعلي، ثم:\n\nتابعونا لمزيد 🏡",
  "hashtags": "٥ هاشتاقات: ٢-٣ عن الحدث + #بيتي + #الإمارات"
}}"""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system,
            tools=[WEB_SEARCH_TOOL],
            messages=[{"role": "user", "content": user_msg}]
        )

        msgs = [{"role": "user", "content": user_msg}]
        for _ in range(5):
            if response.stop_reason != "tool_use":
                break
            tool_results = [{"type": "tool_result", "tool_use_id": b.id, "content": "Search completed"} for b in response.content if b.type == "tool_use"]
            msgs.append({"role": "assistant", "content": response.content})
            msgs.append({"role": "user", "content": tool_results})
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=system,
                tools=[WEB_SEARCH_TOOL],
                messages=msgs
            )

        final_text = next((b.text for b in response.content if hasattr(b, "text") and b.text), "")
        final_text = final_text.strip().replace("```json", "").replace("```", "").strip()
        start = final_text.find("{")
        end = final_text.rfind("}") + 1
        fallback = {"event": "UAE Event", "caption": final_text, "hashtags": "#bayti #UAE"} if lang == "en" else {"event": "فعالية الإمارات", "caption": final_text, "hashtags": "#بيتي #الإمارات"}
        parsed = json_lib.loads(final_text[start:end]) if start >= 0 and end > start else fallback

        tags = parsed.get("hashtags", fallback["hashtags"]).split()[:5]
        return {"caption": parsed["caption"], "hashtags": " ".join(tags), "image_url": None, "type": content_type, "event": parsed.get("event", "")}

    else:
        value_topics_ar = [
            "٥ نصائح لتصوير منتجاتك باحترافية من البيت",
            "كيف تحددين سعر منتجك بذكاء؟",
            "أفكار هدايا مميزة من منتجات محلية",
            "كيف تبنين علامتك التجارية الشخصية؟",
            "أخطاء شائعة تقع فيها البائعات المبتدئات",
            "كيف تكتبين وصفاً جذاباً لمنتجك؟",
            "نصائح لتغليف منتجاتك باحترافية",
            "كيف تتعاملين مع الزبون الصعب؟",
            "كيف تجدين زبائنك الأوائل؟",
            "لماذا تحتاجين قصة لعلامتك التجارية؟",
            "متى يجب أن تضيفي خصماً على منتجك؟ ومتى يضرّك؟",
            "التوصيل المجاني: هل هو ميزة أم فخ؟ كيف تحسبينه صح",
            "كيف ترفع 20 صورة لمنتجاتك دفعة واحدة وتوفر ساعات من العمل",
        ]
        value_topics_en = [
            "5 tips to photograph your products professionally at home",
            "How to price your product smartly?",
            "Unique gift ideas from local products",
            "How to build your personal brand?",
            "Common mistakes new sellers make",
            "How to write an attractive product description?",
            "Tips for professional product packaging",
            "How to deal with a difficult customer?",
            "How to find your first customers?",
            "Why do you need a story for your brand?",
            "When should you add a discount to your product? And when does it hurt you?",
            "Free shipping: a feature or a trap? How to calculate it right",
            "How to upload 20 product photos at once and save hours of work",
        ]
        topic = random.choice(value_topics_en if lang == "en" else value_topics_ar)

        system_en = """You are a marketing and content expert specialized in home-based entrepreneurship.
You write valuable, practical content that helps people grow their businesses.
Write in warm, professional English. Style: educational, practical, inspiring."""

        system_ar = """أنت خبير تسويق ومحتوى متخصص في ريادة الأعمال المنزلية.
تكتب محتوى قيّماً وعملياً يساعد الناس على تطوير مشاريعهم.
اكتب بالعربية الفصحى الخفيفة. الأسلوب: تعليمي، عملي، ملهم."""

        system = system_en if lang == "en" else system_ar

        if lang == "en":
            user_msg = f"""Create an educational Instagram post about: {topic}

Write the text directly without JSON.
Start with a question or an interesting fact, clear practical points with emojis, 150-200 words.
End with:
💡 Start your journey with Bayti: bayti.ink/sell"""
        else:
            user_msg = f"""أنشئ منشور إنستقرام تعليمي عن: {topic}

اكتب النص مباشرة بدون JSON.
يبدأ بسؤال أو حقيقة مثيرة، نقاط عملية واضحة مع إيموجي، ١٥٠-٢٠٠ كلمة.
ينتهِ بـ:
💡 ابدأي رحلتك مع بيتي: bayti.ink/sell"""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user_msg}]
        )

        caption = response.content[0].text.strip()
        return {"caption": caption, "hashtags": HASHTAGS, "image_url": None, "type": content_type, "event": ""}


class InviteRequest(BaseModel):
    seller_name: str = ""
    bio_text: str
    lang: str = ""

@router.post("/generate-invite")
def generate_invite_message(data: InviteRequest):
    """يولد رسالة دعوة ذكية حسب لغة صفحة البائع"""
    import re as _re, os, requests as _requests

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    lang = data.lang
    if not lang:
        arabic = len(_re.findall(r"[\u0600-\u06FF]", data.bio_text))
        english = len(_re.findall(r"[a-zA-Z]", data.bio_text))
        total = arabic + english
        arabic_ratio = arabic / total if total > 0 else 0
        lang = "ar" if arabic_ratio >= 0.15 else "en"

    if lang == "ar":
        system = "أنت مسؤول علاقات بائعين في بيتي — منصة محلية في الإمارات. أسلوبك دافئ ومشجع. اكتب بالعربية الفصحى الخفيفة."
        prompt = f"""اكتب رسالة دعوة قصيرة لبائع اسمه {data.seller_name or "البائع"} بناءً على وصف صفحته:
{data.bio_text}

الرسالة تشمل:
- إطراء صادق على منتجاته
- تعريف بيتي كمنصة محلية في الإمارات
- ذكر أن المنصة تدعم العربية والإنجليزية للوصول لجمهور أوسع
- ذكر مستشار التسعير الذكي بأسلوب جذاب: أداة تحلل أسعار السوق الإماراتي الفعلية وتوصي بالسعر الأمثل لكل منتج تلقائياً — لا تخمين ولا مقارنة يدوية (لا تقل "ذكاء اصطناعي" أو "كلود"، قل "مستشار التسعير الذكي")
- الهدية المجانية (استوديو ذكي لأول ١٠ بائعين)
- سؤال للإذن بإرسال التفاصيل
اكتب مباشرة بدون عناوين."""
    else:
        system = "You are a seller relations manager at Bayti — a UAE home marketplace. Your tone is warm and encouraging."
        prompt = f"""Write a short invitation message for a seller named {data.seller_name or "the seller"} based on their page description:
{data.bio_text}

The message should include:
- A genuine compliment on their products
- Introduce Bayti as a local UAE marketplace
- Mention that the platform supports both Arabic and English — helping reach a wider UAE audience
- Mention the Smart Pricing Advisor naturally: a tool that scans real competitor prices across the UAE market and recommends the ideal price for each product automatically — no guessing, no manual research (never say "AI model" or "Claude", say "Smart Pricing Advisor" or "intelligent pricing tool")
- The free gift (smart AI studio for the first 10 sellers)
- Ask permission to send details
Write directly without headers."""

    try:
        resp = _requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 600, "system": system, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        result = resp.json()
        message = result.get("content", [{}])[0].get("text", "").strip()
        return {"message": message, "lang": lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProposalRequest(BaseModel):
    account_id: int
    language: Optional[str] = None

DEFAULT_PRODUCT = {"emoji": "📦", "name": "Product", "price": "AED 50"}
DEFAULT_REASON = "A strong fit for Bayti's growing UAE buyer base."

# Static (non-AI-generated) proposal template copy, per language. Selected by `language`
# and merged into `replacements` so every section of the template is fully translated,
# not just the AI-written cover.
PROPOSAL_STATIC_TEXT_EN = {
    "{{BETA_BANNER_TEXT}}": "Platform is <strong>live and fully functional</strong> — Official public launch in <strong>1–2 months</strong>. Join now as a founding seller and get <strong>priority placement</strong> at launch.",

    "{{SECTION_WHATISBAYTI_LABEL}}": "About the Platform",
    "{{SECTION_WHATISBAYTI_TITLE}}": "What is Bayti?",
    "{{SECTION_WHATISBAYTI_INTRO}}": "Bayti{brand_gloss} is a UAE-based online marketplace built <strong>exclusively for home-based sellers</strong>. Unlike Instagram or WhatsApp, you get a dedicated shop page, an order management system, AI-powered tools, and a growing customer base — all without any technical setup.",

    "{{SECTION_YOURSHOP_LABEL}}": "Your Shop",
    "{{SECTION_YOURSHOP_TITLE}}": "Everything on Your Seller Page",
    "{{SECTION_YOURSHOP_INTRO}}": "Your public shop page is where buyers find you, browse your menu, and place orders. Here's everything included — out of the box, for free.",

    "{{FEATURE_1_TITLE}}": "Shop Identity",
    "{{FEATURE_1_DESC}}": "Name, profile photo & logo displayed prominently to all buyers",
    "{{FEATURE_2_TITLE}}": "Bilingual Description",
    "{{FEATURE_2_DESC}}": "Arabic & English — AI translates automatically when you save",
    "{{FEATURE_3_TITLE}}": "Shop Gallery",
    "{{FEATURE_3_DESC}}": "Up to 3 showcase photos displayed on your public page",
    "{{FEATURE_4_TITLE}}": "Product Listings",
    "{{FEATURE_4_DESC}}": "Photos, names, descriptions, pricing & prep time per dish",
    "{{FEATURE_5_TITLE}}": "Discount Badges",
    "{{FEATURE_5_DESC}}": "Add % discounts — original price shows crossed-out to buyers",
    "{{FEATURE_6_TITLE}}": "Free Shipping Threshold",
    "{{FEATURE_6_DESC}}": "Set a min. order amount for free delivery — calculated automatically",
    "{{FEATURE_7_TITLE}}": "Delivery by Emirate",
    "{{FEATURE_7_DESC}}": "Set your delivery fee per emirate, or mark as unavailable",
    "{{FEATURE_8_TITLE}}": "Working Hours",
    "{{FEATURE_8_DESC}}": "Your available days & hours shown to buyers before ordering",
    "{{FEATURE_9_TITLE}}": "Response Time Badge",
    "{{FEATURE_9_DESC}}": "Shows your average reply time — builds buyer confidence",
    "{{FEATURE_10_TITLE}}": "Reviews & Ratings",
    "{{FEATURE_10_DESC}}": "Verified customer reviews displayed on your shop page",
    "{{FEATURE_11_TITLE}}": "Minimum Order",
    "{{FEATURE_11_DESC}}": "Set your minimum order value — shown clearly before checkout",
    "{{FEATURE_12_TITLE}}": "Order Dashboard",
    "{{FEATURE_12_DESC}}": "Manage all incoming orders from one simple screen",

    "{{SECTION_AITOOLS_LABEL}}": "Included Free",
    "{{SECTION_AITOOLS_TITLE}}": "AI Tools Built For You",
    "{{SECTION_AITOOLS_INTRO}}": "Four AI-powered tools that save you time and help you sell more — included in every seller account, at no cost.",

    "{{AI_CARD_1_TITLE}}": "Smart Product Description",
    "{{AI_CARD_1_DESC}}": "Upload a photo of your product → AI writes a compelling description in both Arabic & English. No writing needed — just a photo.",
    "{{AI_CARD_2_TITLE}}": "Bayti Studio",
    "{{AI_CARD_2_DESC}}": "Transform any product photo into a professional marketing image — styled backgrounds, lighting effects — completely free.",
    "{{AI_CARD_3_TITLE}}": "Pricing Advisor",
    "{{AI_CARD_3_DESC}}": "Enter your product name & price → AI compares it with similar items in the UAE market and tells you if it's well-positioned.",
    "{{AI_CARD_4_TITLE}}": "Auto-Translation",
    "{{AI_CARD_4_DESC}}": "Write your shop description in English → instantly translated to Arabic. Or in Arabic → translated to English. Automatic on save.",

    "{{SECTION_HOWORDERS_LABEL}}": "The Flow",
    "{{SECTION_HOWORDERS_TITLE}}": "How Orders Work",
    "{{SECTION_HOWORDERS_INTRO}}": "A simple, end-to-end flow — from browse to delivery. You manage everything from your dashboard.",

    "{{STEP_1_TEXT}}": "Buyer browses your shop",
    "{{STEP_2_TEXT}}": "Places an order",
    "{{STEP_3_TEXT}}": "You get notified instantly",
    "{{STEP_4_TEXT}}": "You prepare & deliver",
    "{{STEP_5_TEXT}}": "Payment confirmed ✓",
    "{{SECTION_HOWORDERS_NOTE}}": "Everything managed from a simple dashboard — accessible from your phone or laptop.",

    "{{SECTION_PRICING_LABEL}}": "Cost",
    "{{SECTION_PRICING_TITLE}}": "What Does It Cost?",
    "{{PRICING_BOX_TITLE}}": "Completely Free During Beta",
    "{{PRICING_ITEM_1}}": "No commission on any sale",
    "{{PRICING_ITEM_2}}": "No monthly subscription fee",
    "{{PRICING_ITEM_3}}": "No hidden charges, ever",
    "{{PRICING_ITEM_4}}": "Every dirham you earn is 100% yours",
    "{{PRICING_NOTE}}": "Pricing will only be introduced after the official launch — and early sellers will always receive the most favorable rates.",
    "{{PRICING_AMOUNT}}": "FREE",
    "{{PRICING_PERIOD}}": "During beta phase",

    "{{SECTION_BETAPHASE_LABEL}}": "Where We Are Now",
    "{{SECTION_BETAPHASE_TITLE}}": "About the Beta Phase",
    "{{SECTION_BETAPHASE_INTRO}}": "We're in private beta — the platform is live and fully working, but we haven't publicly launched yet. Here's what that means for you.",

    "{{BETA_CARD_1_TITLE}}": "Launch in 1–2 Months",
    "{{BETA_CARD_1_DESC}}": "Public launch is planned for the coming weeks. Joining now means you're ready from day one.",
    "{{BETA_CARD_2_TITLE}}": "Priority Visibility",
    "{{BETA_CARD_2_DESC}}": "Founding sellers get featured placement and priority ranking when we open to the public.",
    "{{BETA_CARD_3_TITLE}}": "Safe to Explore",
    "{{BETA_CARD_3_DESC}}": "Create your account, set up your full shop, and explore all features — completely risk-free. No commitment required.",
    "{{SECTION_BETAPHASE_NOTE}}": "💡 <strong>You can register today, explore the platform at your own pace, and decide if it's right for you — with zero pressure and zero commitment.</strong> We want you to feel confident before you commit to anything.",

    "{{CTA_EYEBROW}}": "Ready to Start?",
    "{{CTA_TITLE}}": "Create Your Free Shop Today",
    "{{CTA_SUB}}": "Sign up in minutes. Set up your shop, add your products, and see exactly how {display_name} looks on Bayti — before you decide anything.",
    "{{CTA_NOTE}}": "Questions? Just reply to this message — we're happy to walk you through it 😊",
}

PROPOSAL_STATIC_TEXT_AR = {
    "{{BETA_BANNER_TEXT}}": "المنصة <strong>تعمل بالكامل الآن</strong> — الإطلاق الرسمي خلال <strong>شهر إلى شهرين</strong>. انضم الآن كبائع مؤسس واحصل على <strong>أولوية الظهور</strong> عند الإطلاق.",

    "{{SECTION_WHATISBAYTI_LABEL}}": "عن المنصة",
    "{{SECTION_WHATISBAYTI_TITLE}}": "ما هي بيتي؟",
    "{{SECTION_WHATISBAYTI_INTRO}}": "بيتي منصة تسوق إلكترونية في الإمارات مخصصة <strong>حصرياً للبائعين من المنزل</strong>. بخلاف إنستقرام أو واتساب، تحصل على صفحة متجر مستقلة، نظام لإدارة الطلبات، أدوات ذكاء اصطناعي، وقاعدة عملاء متنامية — دون أي إعداد تقني.",

    "{{SECTION_YOURSHOP_LABEL}}": "متجرك",
    "{{SECTION_YOURSHOP_TITLE}}": "كل ما تحتاجه في صفحة متجرك",
    "{{SECTION_YOURSHOP_INTRO}}": "صفحة متجرك العامة هي المكان الذي يجدك فيه المشترون، يتصفحون منتجاتك، ويقدّمون طلباتهم. إليك كل ما هو متاح — جاهز فوراً ومجاناً.",

    "{{FEATURE_1_TITLE}}": "هوية المتجر",
    "{{FEATURE_1_DESC}}": "الاسم، الصورة الشخصية والشعار تظهر بوضوح لكل المشترين",
    "{{FEATURE_2_TITLE}}": "وصف ثنائي اللغة",
    "{{FEATURE_2_DESC}}": "عربي وإنجليزي — الذكاء الاصطناعي يترجم تلقائياً عند الحفظ",
    "{{FEATURE_3_TITLE}}": "معرض صور المتجر",
    "{{FEATURE_3_DESC}}": "حتى 3 صور تعريفية تظهر في صفحتك العامة",
    "{{FEATURE_4_TITLE}}": "عرض المنتجات",
    "{{FEATURE_4_DESC}}": "صور، أسماء، أوصاف، أسعار ووقت التحضير لكل منتج",
    "{{FEATURE_5_TITLE}}": "شارات الخصم",
    "{{FEATURE_5_DESC}}": "أضف نسبة خصم % — يظهر السعر الأصلي مشطوباً للمشترين",
    "{{FEATURE_6_TITLE}}": "حد التوصيل المجاني",
    "{{FEATURE_6_DESC}}": "حدد مبلغاً أدنى للطلب للحصول على توصيل مجاني — يُحسب تلقائياً",
    "{{FEATURE_7_TITLE}}": "التوصيل حسب الإمارة",
    "{{FEATURE_7_DESC}}": "حدد رسوم التوصيل لكل إمارة، أو ضعها كغير متاحة",
    "{{FEATURE_8_TITLE}}": "ساعات العمل",
    "{{FEATURE_8_DESC}}": "أيامك وساعات عملك المتاحة تظهر للمشترين قبل الطلب",
    "{{FEATURE_9_TITLE}}": "شارة سرعة الرد",
    "{{FEATURE_9_DESC}}": "تُظهر متوسط وقت ردك — تبني ثقة المشتري",
    "{{FEATURE_10_TITLE}}": "التقييمات والمراجعات",
    "{{FEATURE_10_DESC}}": "مراجعات عملاء موثّقة تظهر في صفحة متجرك",
    "{{FEATURE_11_TITLE}}": "الحد الأدنى للطلب",
    "{{FEATURE_11_DESC}}": "حدد القيمة الدنيا للطلب — تظهر بوضوح قبل إتمام الشراء",
    "{{FEATURE_12_TITLE}}": "لوحة إدارة الطلبات",
    "{{FEATURE_12_DESC}}": "أدر جميع الطلبات الواردة من شاشة واحدة بسيطة",

    "{{SECTION_AITOOLS_LABEL}}": "متضمّن مجاناً",
    "{{SECTION_AITOOLS_TITLE}}": "أدوات ذكاء اصطناعي مصممة لك",
    "{{SECTION_AITOOLS_INTRO}}": "أربع أدوات مدعومة بالذكاء الاصطناعي توفّر وقتك وتساعدك على البيع أكثر — متضمّنة في كل حساب بائع، دون أي تكلفة.",

    "{{AI_CARD_1_TITLE}}": "وصف المنتج الذكي",
    "{{AI_CARD_1_DESC}}": "ارفع صورة منتجك ← يكتب الذكاء الاصطناعي وصفاً جذاباً بالعربية والإنجليزية معاً. بلا كتابة — فقط صورة.",
    "{{AI_CARD_2_TITLE}}": "استوديو بيتي",
    "{{AI_CARD_2_DESC}}": "حوّل أي صورة منتج إلى صورة تسويقية احترافية — خلفيات مصممة وتأثيرات إضاءة — مجاناً بالكامل.",
    "{{AI_CARD_3_TITLE}}": "مستشار التسعير",
    "{{AI_CARD_3_DESC}}": "أدخل اسم منتجك وسعره ← يقارنه الذكاء الاصطناعي بمنتجات مشابهة في السوق الإماراتي ويخبرك إن كان سعرك مناسباً.",
    "{{AI_CARD_4_TITLE}}": "الترجمة التلقائية",
    "{{AI_CARD_4_DESC}}": "اكتب وصف متجرك بالإنجليزية ← يُترجم فوراً للعربية. أو بالعربية ← يُترجم للإنجليزية. تلقائياً عند الحفظ.",

    "{{SECTION_HOWORDERS_LABEL}}": "آلية العمل",
    "{{SECTION_HOWORDERS_TITLE}}": "كيف تعمل الطلبات؟",
    "{{SECTION_HOWORDERS_INTRO}}": "مسار بسيط من البداية للنهاية — من التصفح إلى التوصيل. تدير كل شيء من لوحة تحكمك.",

    "{{STEP_1_TEXT}}": "المشتري يتصفح متجرك",
    "{{STEP_2_TEXT}}": "يقدّم طلباً",
    "{{STEP_3_TEXT}}": "تصلك إشعار فوري",
    "{{STEP_4_TEXT}}": "تجهّز وتوصّل الطلب",
    "{{STEP_5_TEXT}}": "تأكيد الدفع ✓",
    "{{SECTION_HOWORDERS_NOTE}}": "كل شيء تديره من لوحة تحكم بسيطة — يمكن الوصول إليها من هاتفك أو حاسوبك.",

    "{{SECTION_PRICING_LABEL}}": "التكلفة",
    "{{SECTION_PRICING_TITLE}}": "كم تكلف المنصة؟",
    "{{PRICING_BOX_TITLE}}": "مجانية بالكامل خلال المرحلة التجريبية",
    "{{PRICING_ITEM_1}}": "بدون عمولة على أي عملية بيع",
    "{{PRICING_ITEM_2}}": "بدون رسوم اشتراك شهرية",
    "{{PRICING_ITEM_3}}": "بدون رسوم خفية على الإطلاق",
    "{{PRICING_ITEM_4}}": "كل درهم تكسبه هو لك بالكامل",
    "{{PRICING_NOTE}}": "لن يتم تفعيل أي رسوم إلا بعد الإطلاق الرسمي — وسيحصل البائعون الأوائل دائماً على أفضل الشروط.",
    "{{PRICING_AMOUNT}}": "مجاناً",
    "{{PRICING_PERIOD}}": "خلال المرحلة التجريبية",

    "{{SECTION_BETAPHASE_LABEL}}": "أين نحن الآن",
    "{{SECTION_BETAPHASE_TITLE}}": "عن المرحلة التجريبية",
    "{{SECTION_BETAPHASE_INTRO}}": "نحن في مرحلة تجريبية خاصة — المنصة تعمل بالكامل، لكننا لم نطلقها للجمهور بعد. إليك ماذا يعني هذا بالنسبة لك.",

    "{{BETA_CARD_1_TITLE}}": "الإطلاق خلال شهر إلى شهرين",
    "{{BETA_CARD_1_DESC}}": "الإطلاق الرسمي مخطط له خلال الأسابيع القادمة. الانضمام الآن يعني أنك جاهز منذ اليوم الأول.",
    "{{BETA_CARD_2_TITLE}}": "أولوية الظهور",
    "{{BETA_CARD_2_DESC}}": "يحصل البائعون المؤسسون على ظهور مميز وترتيب أولوية عند الإطلاق للجمهور.",
    "{{BETA_CARD_3_TITLE}}": "آمن للتجربة",
    "{{BETA_CARD_3_DESC}}": "أنشئ حسابك، جهّز متجرك بالكامل، واستكشف كل الميزات — دون أي مخاطرة. بلا أي التزام.",
    "{{SECTION_BETAPHASE_NOTE}}": "💡 <strong>يمكنك التسجيل اليوم واستكشاف المنصة بالوتيرة التي تناسبك، ثم تقرر إن كانت مناسبة لك — دون أي ضغط أو التزام.</strong> نريدك أن تشعر بالثقة قبل أن تلتزم بأي شيء.",

    "{{CTA_EYEBROW}}": "جاهز للبدء؟",
    "{{CTA_TITLE}}": "أنشئ متجرك المجاني اليوم",
    "{{CTA_SUB}}": "سجّل خلال دقائق. جهّز متجرك، أضف منتجاتك، وشاهد بالضبط كيف يظهر {display_name} على بيتي — قبل أن تقرر أي شيء.",
    "{{CTA_NOTE}}": "لديك أسئلة؟ فقط ردّ على هذه الرسالة — يسعدنا مساعدتك 😊",
}

@router.post("/generate-proposal")
def generate_proposal(data: ProposalRequest, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Generates a personalized HTML sales proposal for an outreach account,
    filling the bayti-proposals template (see backend/templates/proposal_template.html,
    based on public/p/auntyzkitchen.html) with AI-written, account-specific content."""
    import json, datetime, anthropic
    from pathlib import Path
    from routers.growth import OutreachAccount

    account = db.query(OutreachAccount).filter(OutreachAccount.id == data.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    # Deterministic language detection (same convention as growth.generate_message),
    # decided up front so the template's lang/dir and static bits match Claude's output.
    # An explicit `language` in the request overrides auto-detection.
    if data.language in ("ar", "en"):
        language = data.language
    else:
        import re as _re
        text_sample = f"{account.display_name} {account.category} {account.product_note}"
        arabic_chars = len(_re.findall(r"[؀-ۿ]", text_sample))
        english_chars = len(_re.findall(r"[a-zA-Z]", text_sample))
        total_chars = arabic_chars + english_chars
        arabic_ratio = arabic_chars / total_chars if total_chars > 0 else 0
        language = "ar" if arabic_ratio >= 0.30 else "en"
    lang_instruction = "Write cover_title, cover_sub, product names, and reasons in Arabic only." if language == "ar" \
        else "Write cover_title, cover_sub, product names, and reasons in English only."

    system_prompt = f"""You are writing a personalized sales proposal page for Bayti, a UAE local marketplace for home-based sellers, targeting a specific Instagram seller Bayti wants to recruit.

{lang_instruction} Do not mix languages within a field.

Return ONLY valid JSON with these fields:
- cover_title: a punchy hook for the seller's specific niche, max 8 words, may include one <br> tag to break it into two lines
- cover_sub: one sentence (max 30 words) pitching Bayti to this specific seller's niche
- shop_icon: a single emoji representing their product category
- products: array of exactly 3 objects {{"emoji": ..., "name": ..., "price": "AED NN"}}, each a plausible example product for this seller's category with a realistic AED price
- reasons: array of exactly 6 short strings (each one sentence, may use <strong>...</strong> once for emphasis) explaining specifically why THIS seller is a strong fit for Bayti

Rules:
- Do not invent specific facts about the seller you don't know (years in business, exact follower counts, review counts, testimonials) unless given in the input — base reasons on their category/niche/location/market fit instead
- Do not promise guaranteed sales
- Tone: warm, professional, specific to their niche — not generic hype
- Return ONLY the JSON object, nothing else"""

    user_prompt = f"""Seller Instagram: @{account.username}
Display name: {account.display_name or account.username}
Category: {account.category or "general home business"}
Emirate: {account.emirate or "UAE"}
Product note: {account.product_note or "not specified"}
Followers: {account.followers or "not specified"}

Write the personalized proposal content as JSON."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        parsed = json.loads(clean[start:end])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")

    products = (parsed.get("products") or [])[:3]
    while len(products) < 3:
        products.append(DEFAULT_PRODUCT)
    reasons = (parsed.get("reasons") or [])[:6]
    while len(reasons) < 6:
        reasons.append(DEFAULT_REASON)

    template_path = Path(__file__).resolve().parent.parent / "templates" / "proposal_template.html"
    html = template_path.read_text(encoding="utf-8")

    # Server-computed (not Claude-generated) so language consistency is guaranteed rather
    # than trusted to the model's output.
    if language == "ar":
        dir_value = "rtl"
        brand_secondary = "بيتي"
        brand_gloss = " (بيتي)"
        cover_badge = "⚡ مرحلة تجريبية — انضم الآن"
    else:
        dir_value = "ltr"
        brand_secondary = ""
        brand_gloss = ""
        cover_badge = "⚡ Beta Phase — Join Now"

    replacements = {
        "{{USERNAME}}": account.username,
        "{{DISPLAY_NAME}}": account.display_name or account.username,
        "{{EMIRATE}}": account.emirate or "UAE",
        "{{LANGUAGE}}": language,
        "{{DIR}}": dir_value,
        "{{BRAND_SECONDARY}}": brand_secondary,
        "{{BRAND_GLOSS}}": brand_gloss,
        "{{COVER_BADGE}}": cover_badge,
        "{{COVER_TITLE}}": parsed.get("cover_title") or "Your Shop,<br>Now Online.",
        "{{COVER_SUB}}": parsed.get("cover_sub") or "Bayti connects sellers like you with buyers across the UAE — a professional shop, AI tools, and order management, all in one place.",
        "{{SHOP_ICON}}": parsed.get("shop_icon") or "🏠",
        "{{MONTH_YEAR}}": datetime.datetime.now().strftime("%B %Y"),
    }
    for i, p in enumerate(products, start=1):
        replacements[f"{{{{PRODUCT_{i}_EMOJI}}}}"] = p.get("emoji", DEFAULT_PRODUCT["emoji"])
        replacements[f"{{{{PRODUCT_{i}_NAME}}}}"] = p.get("name", DEFAULT_PRODUCT["name"])
        replacements[f"{{{{PRODUCT_{i}_PRICE}}}}"] = p.get("price", DEFAULT_PRODUCT["price"])
    for i, r in enumerate(reasons, start=1):
        replacements[f"{{{{REASON_{i}}}}}"] = r

    static_text = PROPOSAL_STATIC_TEXT_AR if language == "ar" else PROPOSAL_STATIC_TEXT_EN
    display_name = account.display_name or account.username
    for placeholder, value in static_text.items():
        replacements[placeholder] = value.format(brand_gloss=brand_gloss, display_name=display_name)

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    return {
        "html_content": html,
        "suggested_filename": f"{account.username}.html",
    }
