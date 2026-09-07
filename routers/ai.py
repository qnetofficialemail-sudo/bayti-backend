from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from core.database import get_db, HTTPException
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

For each category, provide a demand forecast for the next 6 months.
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
                "max_tokens": 2000,
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
