#!/usr/bin/env python3
"""
Bayti Pre-Push Checklist
شغّل هذا قبل كل git push للـ backend
"""
import subprocess, sys, os, re

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
errors = []

print("=" * 50)
print("  Bayti — Pre-Push Check")
print("=" * 50)

# ١. فحص syntax فقط (بدون import المكتبات الخارجية)
print("\n١. فحص الـ syntax...")
files_to_check = [
    "main.py",
    "routers/ai.py",
    "routers/auth.py",
    "routers/products.py",
    "routers/orders.py",
    "routers/sellers.py",
    "routers/admin.py",
    "routers/growth.py",
    "routers/studio.py",
]

syntax_ok = True
for f in files_to_check:
    fpath = os.path.join(BACKEND, f)
    if not os.path.exists(fpath):
        continue
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", fpath],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"   ❌ {f}: {result.stderr.strip()}")
        errors.append(f"syntax error in {f}")
        syntax_ok = False
    else:
        print(f"   ✅ {f}")

# ٢. فحص duplicate function names في ai.py
print("\n٢. فحص duplicate functions في ai.py...")
ai_path = os.path.join(BACKEND, "routers/ai.py")
if os.path.exists(ai_path):
    content = open(ai_path, encoding="utf-8").read()
    funcs = re.findall(r"^def (\w+)|^async def (\w+)", content, re.MULTILINE)
    func_names = [f[0] or f[1] for f in funcs]
    seen = set()
    for name in func_names:
        if name in seen:
            print(f"   ❌ دالة مكررة: {name}")
            errors.append(f"duplicate function: {name}")
        seen.add(name)
    if not errors:
        print("   ✅ لا توجد دوال مكررة")

# ٣. فحص وجود endpoints المهمة
print("\n٣. فحص الـ endpoints...")
required_endpoints = [
    ("/instagram-content-v2", "ai.py"),
    ("/generate-invite", "ai.py"),
    ("/pricing-advisor", "ai.py"),
]
for endpoint, fname in required_endpoints:
    fpath = os.path.join(BACKEND, f"routers/{fname}")
    if os.path.exists(fpath):
        c = open(fpath, encoding="utf-8").read()
        if endpoint in c:
            print(f"   ✅ {endpoint}")
        else:
            print(f"   ❌ {endpoint} غير موجود في {fname}")
            errors.append(f"missing endpoint {endpoint}")

# ٤. تذكيرات
print("\n٤. تذكير قواعد git push...")
print("   ✅ git add -A")
print("   ✅ git commit -m '...'")
print("   ✅ git push")
print("   ⚠️  لا تستخدم && بين الأوامر")

print("\n٥. تذكير قواعد الـ models...")
print("   كل column جديد يحتاج:")
print("   [ ] models/user.py")
print("   [ ] schemas/schemas.py")
print("   [ ] main.py startup migration")
print("   [ ] ALTER TABLE في Railway Console")

# النتيجة
print("\n" + "=" * 50)
if errors:
    print(f"❌ فشل — أصلح قبل الرفع:")
    for e in errors:
        print(f"   • {e}")
    sys.exit(1)
else:
    print("✅ كل شيء جاهز للرفع!")
print("=" * 50)
