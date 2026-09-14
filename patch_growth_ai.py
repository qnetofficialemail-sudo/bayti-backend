import sys

# ── patch growth.py ──────────────────────────────────────────────────────────
path = sys.argv[1] if len(sys.argv) > 1 else "routers/growth.py"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")
has_crlf = "\r\n" in c
c = c.replace("\r\n", "\n")
n = 0

old = "مميزات بيتي: ذكاء اصطناعي يكتب وصف المنتج، استوديو ذكي يولّد صور تسويقية مجاناً، وصول لجمهور واسع في الإمارات، مجاني تماماً في المرحلة التجريبية، أول 10 بائعين يحصلون على صفحة مميزة مجاناً.\nرابط التسجيل: bayti.ink/sell"
new = "مميزات بيتي: ذكاء اصطناعي يكتب وصف المنتج، استوديو ذكي يولّد صور تسويقية مجاناً، وصول لجمهور واسع في الإمارات، مجاني تماماً في المرحلة التجريبية، أول 10 بائعين يحصلون على صفحة مميزة مجاناً، إمكانية إضافة خصم % على أي منتج مع عرض السعر الأصلي مشطوباً، خاصية التوصيل المجاني التلقائي عند بلوغ حد معين في الطلب.\nرابط التسجيل: bayti.ink/sell"

if old in c:
    c = c.replace(old, new)
    n += 1
    print("OK growth.py system prompt")
else:
    print("MISS growth.py system prompt")

if has_crlf:
    c = c.replace("\n", "\r\n")
with open(path, "wb") as f:
    f.write(c.encode("utf-8"))
print(f"growth.py: {n}/1")
