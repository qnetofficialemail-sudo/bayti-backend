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
    """AI Pricing Advisor — analyzes market and suggests optimal price."""
    from core.database import SessionLocal
    from models.user import Product, Category
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    # Get similar products from DB
    db = SessionLocal()
    try:
        similar = db.query(Product).join(Category, isouter=True).filter(
            Category.name.ilike(f"%{data.category}%")
        ).limit(20).all()
        
        market_data = [{"name": p.name, "price": p.price} for p in similar if p.price > 0]
    finally:
        db.close()

    system_prompt = """You are a UAE marketplace pricing expert for Bayti.
Analyze the product and market data, then give a short pricing recommendation.
Respond in JSON: {"verdict": "good"|"high"|"low", "suggestion": "one sentence advice", "min": number, "max": number}
verdict: "good" if price is competitive, "high" if overpriced, "low" if underpriced.
suggestion: warm, practical advice in 15 words max.
min/max: the recommended price range based on market data.
Return ONLY the JSON object."""

    user_prompt = f"""Product: "{data.product_name}"
Category: {data.category}
Seller's price: AED {data.price}
Similar products on Bayti: {market_data if market_data else "No similar products yet — this could be a unique opportunity!"}

Give pricing recommendation as JSON."""

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
                "max_tokens": 200,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=15,
        )
        result = response.json()
        text = result.get("content", [{}])[0].get("text", "{}")
        import json
        clean = text.replace("```json", "").replace("```", "").strip()
        advice = json.loads(clean)
        return advice
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
