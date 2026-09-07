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

    # Get products from same category
    db = SessionLocal()
    try:
        category_products = db.query(Product).join(Category, isouter=True).filter(
            Category.name.ilike(f"%{data.category}%"),
            Product.price > 0
        ).limit(50).all()
        all_names = [{"name": p.name, "price": p.price} for p in category_products]
    finally:
        db.close()

    # Use AI to find semantically similar products
    prices = []
    if all_names:
        try:
            sim_response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 150,
                    "system": "You are a product similarity judge. Given a new product and existing products, return ONLY a JSON array of prices of similar products. Similar = same product type (e.g. scented candle and colored candle are similar; candle and perfume are not). If none similar, return []. Return ONLY the JSON array.",
                    "messages": [{"role": "user", "content": f"New: '{data.product_name}'. Existing: {all_names}. Return prices array."}],
                },
                timeout=10,
            )
            sim_text = sim_response.json().get("content", [{}])[0].get("text", "[]")
            clean_sim = sim_text.replace("```json", "").replace("```", "").strip()
            similar_prices = json.loads(clean_sim)
            prices = [float(p) for p in similar_prices if isinstance(p, (int, float)) and p > 0]
        except:
            prices = [p["price"] for p in all_names]

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
