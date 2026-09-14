import sys

path = sys.argv[1] if len(sys.argv) > 1 else "routers/ai.py"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")
has_crlf = "\r\n" in c
c = c.replace("\r\n", "\n")
n = 0

# patch sellers system prompt
old = """مميزات بيتي التي يمكنك ذكرها:
- الذكاء الاصطناعي يكتب وصف المنتج تلقائياً من الصورة
- استوديو بيتي الذكي: يولّد صوراً تسويقية احترافية مجاناً
- مستشار التسعير الذكي
- لوحة تحكم سهلة لإدارة المنتجات والطلبات
- وصول لجمهور واسع في الإمارات
- بدون عمولة في المرحلة التجريبية"""
new = """مميزات بيتي التي يمكنك ذكرها:
- الذكاء الاصطناعي يكتب وصف المنتج تلقائياً من الصورة
- استوديو بيتي الذكي: يولّد صوراً تسويقية احترافية مجاناً
- مستشار التسعير الذكي
- لوحة تحكم سهلة لإدارة المنتجات والطلبات
- وصول لجمهور واسع في الإمارات
- بدون عمولة في المرحلة التجريبية
- خاصية الخصم: أضف نسبة خصم % على أي منتج — يظهر السعر الأصلي مشطوباً وbadge أحمر للمشتري
- خاصية التوصيل المجاني: حدد مبلغ أدنى للطلب ويتحول التوصيل لمجاني تلقائياً"""

if old in c:
    c = c.replace(old, new)
    n += 1
    print("OK ai.py sellers system prompt")
else:
    print("MISS ai.py sellers system prompt")

# patch value topics list — add discount and shipping topics
old2 = '            "كيف تجدين زبائنك الأوائل؟",\n            "لماذا تحتاجين قصة لعلامتك التجارية؟",'
new2 = '            "كيف تجدين زبائنك الأوائل؟",\n            "لماذا تحتاجين قصة لعلامتك التجارية؟",\n            "متى يجب أن تضيفي خصماً على منتجك؟ ومتى يضرّك؟",\n            "التوصيل المجاني: هل هو ميزة أم فخ؟ كيف تحسبينه صح",'

if old2 in c:
    c = c.replace(old2, new2)
    n += 1
    print("OK ai.py value topics")
else:
    print("MISS ai.py value topics")

# patch sellers topics list — add discount and shipping topics
old3 = '            "من يمكنه البيع عبر بيتي؟ الجواب سيفاجئك",'
new3 = '            "من يمكنه البيع عبر بيتي؟ الجواب سيفاجئك",\n            "خاصية الخصم في بيتي — كيف تستخدمينها بذكاء لتبيعي أكثر",\n            "التوصيل المجاني من بيتي — كيف يزيد مبيعاتك تلقائياً",'

if old3 in c:
    c = c.replace(old3, new3)
    n += 1
    print("OK ai.py sellers topics")
else:
    print("MISS ai.py sellers topics")

if has_crlf:
    c = c.replace("\n", "\r\n")
with open(path, "wb") as f:
    f.write(c.encode("utf-8"))
print(f"ai.py: {n}/3")
