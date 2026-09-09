from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from core.database import get_db
from core.auth import get_current_seller
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
    """AI Pricing Advisor — data-driven pricing based on real market prices."""
    from core.database import SessionLocal
    from models.user import Product, Category
    import statistics, json

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    # Search ALL products by keyword — category is irrelevant for pricing
    db = SessionLocal()
    try:
        all_products = db.query(Product).filter(Product.price > 0).limit(500).all()
    finally:
        db.close()

    # Keyword-based similarity — extract meaningful words (3+ chars)
    import re
    def get_keywords(text):
        stop_words = {"من", "في", "على", "مع", "هذا", "هذه", "و", "the", "and", "with", "for", "of", "a", "an"}
        import re as _re
        words = _re.findall(r"[\w؀-ۿ]{3,}", text.lower())
        stemmed = set()
        for w in words:
            if w not in stop_words:
                stemmed.add(w)
                if w.endswith("s") and len(w) > 4:
                    stemmed.add(w[:-1])
                if w.endswith("es") and len(w) > 5:
                    stemmed.add(w[:-2])
        return stemmed

    # Search using keywords from BOTH name and name_ar of query — language-agnostic
    query_keywords = get_keywords(data.product_name)

    # Match against both AR and EN product names — collect matched product ids
    matched_ids = set()
    for p in all_products:
        product_keywords = get_keywords(p.name) | get_keywords(p.name_ar or "")
        if query_keywords & product_keywords:
            matched_ids.add(p.id)

    # Also add all products from same category_id to the matched pool
    # This ensures "candles" and "شموع" get the same range when same category selected
    if data.category_id:
        for p in all_products:
            if p.category_id == data.category_id:
                matched_ids.add(p.id)

    prices = [p.price for p in all_products if p.id in matched_ids]

    # Calculate range from real data
    if len(prices) == 0:
        # No similar products at all — truly unique
        price_min = None
        price_max = None
        verdict = "unique"
    elif len(prices) >= 3:
        avg = statistics.mean(prices)
        stdev = statistics.stdev(prices)
        price_min = round(max(avg - stdev, min(prices)), 0)
        price_max = round(min(avg + stdev, max(prices)), 0)
        if data.price < price_min * 0.85:
            verdict = "low"
        elif data.price > price_max * 1.15:
            verdict = "high"
        else:
            verdict = "good"
    else:
        # 1-2 similar products — use their range
        price_min = round(min(prices) * 0.8, 0)
        price_max = round(max(prices) * 1.2, 0)
        if data.price < price_min * 0.85:
            verdict = "low"
        elif data.price > price_max * 1.15:
            verdict = "high"
        else:
            verdict = "good"

    # Ask AI only for a short suggestion text
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
                "max_tokens": 60,
                "system": f"You are a UAE marketplace pricing advisor. Write ONE short sentence of practical advice (max 12 words). Always write in {'Arabic' if data.lang == 'ar' else 'English'}. Be warm and direct. No JSON, just the sentence.",
                "messages": [{"role": "user", "content": f'Product: "{data.product_name}", Price: AED {data.price}, Market range: AED {price_min}-{price_max}, Verdict: {verdict}. Give one short tip.'}],
            },
            timeout=15,
        )
        result = response.json()
        suggestion = result.get("content", [{}])[0].get("text", "").strip()
    except:
        suggestion = f"Market range for this category: AED {price_min}–{price_max}"

    if verdict == "unique":
        return {"verdict": "unique", "suggestion": suggestion, "min": None, "max": None}
    return {"verdict": verdict, "suggestion": suggestion, "min": int(price_min), "max": int(price_max)}


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

    # Generate caption + image prompt together
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system="""أنت مدير محتوى إنستقرام لمنصة بيتي — سوق للبائعات المنزليات المقيمات في الإمارات من جميع الجنسيات.
الموقع في مرحلة تجريبية. اكتب بالعربية الفصحى الخفيفة. لا تخترع أرقاماً.
الأسلوب: دافئ، مشجع، احترافي. هوية بيتي: برتقالي دافئ، كريمي، طابع منزلي دافئ.
مهم: لا تخصّص المحتوى لجنسية معينة — الموقع لجميع النساء المقيمات في الإمارات بغض النظر عن جنسيتهن.
لا تكتب "الإماراتية" أو "الإماراتيات" للإشارة للبائعات — اكتب "المقيمات في الإمارات" أو "بائعات الإمارات" فقط.""",
        messages=[{
            "role": "user",
            "content": f"""أنشئ منشور إنستقرام عن: {topic}

أعطني JSON فقط بهذا الشكل:
{{
  "caption": "نص المنشور — يبدأ بجملة قوية، إيموجي، ١٥٠-٢٠٠ كلمة، ينتهي بـ:\n\n🔗 سجّلي الآن: bayti-frontend-three.vercel.app/sell",
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

    # Generate image if OpenAI key available
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
                # Store as data URL
                image_url = f"data:image/png;base64,{img_data['b64_json']}"
        except Exception:
            pass

    HASHTAGS = "#بيتي #بيع_من_البيت #بائعات_الإمارات #منتجات_محلية #bayti"
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

    HASHTAGS = "#بيتي #بيع_من_البيت #بائعات_الإمارات #منتجات_محلية #bayti"

    # ── Type 1: Sellers ─────────────────────────────────────────────
    if content_type == "sellers":
        topics = [
            "دعوة البائعات المنزليات للانضمام إلى بيتي قبل الإطلاق الرسمي",
            "مميزات البيع عبر بيتي — الذكاء الاصطناعي يكتب عنك",
            "نصيحة للبائعة المبتدئة: كيف تصوّرين منتجك باحترافية",
            "استطلاع: أي فئة تفضلين؟ شموع، عبايات، حلويات؟",
            "كوني من الأوائل — مميزات حصرية لمن تسجّل الآن",
            "بيتي والبائعات: قصة نبنيها معاً",
            "رحلة من البيت إلى الزبون — كيف يعمل بيتي",
            "لماذا بيتي أفضل من الانستقرام للبيع؟",
            "خلف الكواليس: كيف نبني بيتي",
            "كيف تحددين سعر منتجك بذكاء؟",
            "أخطاء شائعة تقع فيها البائعات المبتدئات",
            "كيف تصوّرين منتجك باحترافية من البيت؟",
            "كيف تكتبين وصفاً جذاباً لمنتجك؟",
            "كيف تجدين زبائنك الأوائل؟",
        ]
        topic = random.choice(topics)

        system = """أنت مدير محتوى إنستقرام لمنصة بيتي — سوق للبائعات المنزليات المقيمات في الإمارات من جميع الجنسيات.
الموقع في مرحلة تجريبية. اكتب بالعربية الفصحى الخفيفة. لا تخترع أرقاماً.
الأسلوب: دافئ، مشجع، احترافي.
لا تخصّص المحتوى لجنسية معينة — الموقع لجميع النساء المقيمات في الإمارات."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": f"""أنشئ منشور إنستقرام عن: {topic}

اكتب النص مباشرة بدون JSON وبدون عناوين.
يبدأ بجملة جذابة قوية، إيموجي مناسبة، ١٥٠-٢٠٠ كلمة.
ينتهي بـ:
🔗 سجّلي الآن: bayti-frontend-three.vercel.app/sell"""}]
        )

        caption = response.content[0].text.strip()
        return {"caption": caption, "hashtags": HASHTAGS, "image_url": None, "type": content_type, "event": ""}

    # ── Type 2: Events & Trends (with web search) ────────────────────
    elif content_type == "events":
        system = """أنت مدير محتوى إنستقرام متخصص في المحتوى الإماراتي.
ابحث عن أبرز خبر أو فعالية إيجابية في الإمارات اليوم واكتب منشوراً عنه.
قواعد صارمة:
- اكتب بالعربية الفصحى الخفيفة
- تجنّب تماماً: السياسة، الحروب، الجرائم، الحوادث، أي أخبار سلبية
- ركّز على: الفعاليات، المهرجانات، الافتتاحات، الإنجازات، الطعام، الفن، الرياضة، الطقس
- لا تذكر بيتي أو أي منصة في المنشور
- انهِ بسؤال تفاعلي ثم: تابعونا لمزيد 🏡"""

        WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search"}

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

        # Handle multi-turn tool use
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
        parsed = json_lib.loads(final_text[start:end]) if start >= 0 and end > start else {"event": "فعالية الإمارات", "caption": final_text, "hashtags": "#بيتي #الإمارات"}

        tags = parsed.get("hashtags", "#بيتي #الإمارات").split()[:5]
        return {"caption": parsed["caption"], "hashtags": " ".join(tags), "image_url": None, "type": content_type, "event": parsed.get("event", "")}

    # ── Type 3: Value content ────────────────────────────────────────
    else:
        value_topics = [
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
        ]
        topic = random.choice(value_topics)

        system = """أنت خبير تسويق ومحتوى متخصص في ريادة الأعمال المنزلية.
تكتب محتوى قيّماً وعملياً يساعد النساء على تطوير مشاريعهن.
اكتب بالعربية الفصحى الخفيفة. الأسلوب: تعليمي، عملي، ملهم."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": f"""أنشئ منشور إنستقرام تعليمي عن: {topic}

اكتب النص مباشرة بدون JSON.
يبدأ بسؤال أو حقيقة مثيرة، نقاط عملية واضحة مع إيموجي، ١٥٠-٢٠٠ كلمة.
ينتهي بـ:
💡 ابدأي رحلتك مع بيتي: bayti-frontend-three.vercel.app/sell"""}]
        )

        caption = response.content[0].text.strip()
        return {"caption": caption, "hashtags": HASHTAGS, "image_url": None, "type": content_type, "event": ""}

