import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Add pricing endpoint to backend ai.py ──
ai_path = os.path.join(BACKEND, 'routers', 'ai.py')
ai = open(ai_path, encoding='utf-8').read()

pricing_endpoint = '''

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
'''

if 'pricing-advisor' not in ai:
    ai = ai.rstrip() + '\n' + pricing_endpoint
    open(ai_path, 'w', encoding='utf-8').write(ai)
    print("Done - pricing advisor endpoint added")
else:
    print("Skip - already exists")

# ── 2. Create PricingAdvisor component ──
advisor = r'''import React, { useState, useEffect, useRef } from "react";
import api from "../api/client";

interface Props {
  price: string;
  productName: string;
  categoryName: string;
  isArabic: boolean;
}

export default function PricingAdvisor({ price, productName, categoryName, isArabic }: Props) {
  const [advice, setAdvice] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<any>(null);

  useEffect(() => {
    const numPrice = parseFloat(price);
    if (!numPrice || numPrice <= 0 || !productName || !categoryName) {
      setAdvice(null);
      return;
    }

    // Debounce — wait 1.5s after user stops typing
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.post("/api/ai/pricing-advisor", {
          product_name: productName,
          category: categoryName,
          price: numPrice,
        });
        setAdvice(res.data);
      } catch {
        setAdvice(null);
      } finally {
        setLoading(false);
      }
    }, 1500);

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [price, productName, categoryName]);

  if (!price || parseFloat(price) <= 0) return null;

  const colors = {
    good: { bg: "bg-green-50", border: "border-green-200", text: "text-green-700", icon: "✅" },
    high: { bg: "bg-red-50", border: "border-red-200", text: "text-red-700", icon: "⚠️" },
    low: { bg: "bg-yellow-50", border: "border-yellow-200", text: "text-yellow-700", icon: "💡" },
  };

  const verdict = advice?.verdict || "good";
  const c = colors[verdict as keyof typeof colors] || colors.good;

  return (
    <div className={`mt-2 rounded-xl border px-4 py-3 text-sm transition-all ${c.bg} ${c.border}`}>
      {loading ? (
        <div className="flex items-center gap-2 text-gray-400">
          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" opacity="0.3"/>
            <path d="M21 12a9 9 0 00-9-9"/>
          </svg>
          <span>{isArabic ? "جارٍ تحليل السعر..." : "Analyzing price..."}</span>
        </div>
      ) : advice ? (
        <div>
          <div className={`font-medium ${c.text} mb-1`}>
            {c.icon} {isArabic ? (
              verdict === "good" ? "سعر تنافسي!" :
              verdict === "high" ? "السعر مرتفع قليلاً" :
              "يمكنك رفع السعر"
            ) : (
              verdict === "good" ? "Competitive price!" :
              verdict === "high" ? "Price might be too high" :
              "You could charge more"
            )}
          </div>
          <div className={`text-xs ${c.text} opacity-80`}>{advice.suggestion}</div>
          {advice.min && advice.max && (
            <div className={`text-xs ${c.text} mt-1 font-medium`}>
              {isArabic ? `النطاق المقترح: AED ${advice.min} – AED ${advice.max}` : `Suggested range: AED ${advice.min} – AED ${advice.max}`}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
'''

advisor_path = os.path.join(FRONTEND, 'src', 'components', 'PricingAdvisor.tsx')
open(advisor_path, 'w', encoding='utf-8').write(advisor)
print("Done - PricingAdvisor.tsx created")

# ── 3. Add to AddProduct.tsx ──
add_path = os.path.join(FRONTEND, 'src', 'pages', 'AddProduct.tsx')
add = open(add_path, encoding='utf-8').read()

if 'PricingAdvisor' not in add:
    # Add import
    old_imp = 'import { useLanguage } from "../context/LanguageContext";'
    new_imp = 'import { useLanguage } from "../context/LanguageContext";\nimport PricingAdvisor from "../components/PricingAdvisor";'
    add = add.replace(old_imp, new_imp)

    # Add component after price input — find price field closing
    old_price = 'placeholder="0.00"'
    # Find after price input's closing tag
    idx = add.find(old_price)
    if idx > 0:
        # Find the closing </div> after the price input
        close_div = add.find('</div>', idx)
        if close_div > 0:
            insert_at = close_div + len('</div>')
            advisor_jsx = '\n              <PricingAdvisor price={form.price} productName={form.name} categoryName={categories.find((c:any) => c.id === parseInt(form.category_id))?.name || ""} isArabic={isArabic} />'
            add = add[:insert_at] + advisor_jsx + add[insert_at:]
            print("Done - PricingAdvisor added to AddProduct")
        else:
            print("FAIL - closing div not found in AddProduct")
    else:
        print("FAIL - price placeholder not found in AddProduct")
    
    open(add_path, 'w', encoding='utf-8').write(add)

# ── 4. Add to EditProduct.tsx ──
edit_path = os.path.join(FRONTEND, 'src', 'pages', 'EditProduct.tsx')
edit = open(edit_path, encoding='utf-8').read()

if 'PricingAdvisor' not in edit:
    old_imp2 = 'import { useLanguage } from "../context/LanguageContext";'
    new_imp2 = 'import { useLanguage } from "../context/LanguageContext";\nimport PricingAdvisor from "../components/PricingAdvisor";'
    edit = edit.replace(old_imp2, new_imp2)
    
    # Add after price input
    old_price_label = '{isArabic ? "\u0627\u0644\u0633\u0639\u0631 (\u062f\u0631\u0647\u0645) *" : "Price (AED) *"}'
    idx2 = edit.find(old_price_label)
    if idx2 > 0:
        close_div2 = edit.find('</div>', idx2 + 200)
        if close_div2 > 0:
            insert2 = close_div2 + len('</div>')
            advisor_jsx2 = '\n          <PricingAdvisor price={form.price} productName={form.name} categoryName={categories.find((c:any) => c.id === parseInt(form.category_id))?.name || ""} isArabic={isArabic} />'
            edit = edit[:insert2] + advisor_jsx2 + edit[insert2:]
            print("Done - PricingAdvisor added to EditProduct")
    
    open(edit_path, 'w', encoding='utf-8').write(edit)

print("\nAll done!")
