from fastapi import APIRouter, HTTPException
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
        words = re.findall(r"[\w؀-ۿ]{3,}", text.lower())
        return {w for w in words if w not in stop_words}

    query_keywords = get_keywords(data.product_name)

    # Find products with at least 1 keyword in common
    prices = []
    for p in all_products:
        product_keywords = get_keywords(p.name) | get_keywords(p.name_ar or "")
        if query_keywords & product_keywords:
            prices.append(p.price)

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
                "system": "You are a UAE marketplace pricing advisor. Write ONE short sentence of practical advice (max 12 words). Be warm and direct. No JSON, just the sentence.",
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
