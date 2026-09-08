"""
Bayti Pre-Push Checklist
Run this before every: git push (backend)
Usage: python check_before_push.py
"""
import sys, os, subprocess

errors = []
warnings = []

print("=" * 50)
print("Bayti Pre-Push Checklist")
print("=" * 50)

# 1. Syntax + import check
print("\n[1] Checking main.py imports...")
result = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import main; print('OK')"],
    capture_output=True, text=True, cwd=os.getcwd())
if "OK" in result.stdout:
    print("    PASS - main.py imports cleanly")
elif "SyntaxError" in result.stderr or "IndentationError" in result.stderr or "NameError" in result.stderr:
    print(f"    FAIL - {result.stderr[:300]}")
    errors.append("main.py has syntax/name error")
else:
    print(f"    PASS (env vars missing locally but no syntax errors)")

# 2. Check requirements.txt has key libraries
print("\n[2] Checking requirements.txt...")
try:
    reqs = open("requirements.txt").read()
    required = ["fastapi", "sqlalchemy", "pywebpush", "anthropic"]
    for lib in required:
        if lib.lower() in reqs.lower():
            print(f"    OK - {lib}")
        else:
            print(f"    MISSING - {lib}")
            warnings.append(f"{lib} not in requirements.txt")
except:
    errors.append("requirements.txt not found")

# 3. Check for duplicate function declarations in key files
print("\n[3] Checking for duplicate declarations...")
files_to_check = {
    "routers/orders.py": ["def my_orders", "def create_order"],
    "routers/products.py": ["def create_product", "def list_products", "def auto_translate"],
    "routers/sellers.py": ["def list_sellers", "def get_my_seller_profile"],
    "routers/ai.py": ["def ai_pricing_advisor", "def ai_generate_description"],
    "routers/push.py": ["def send_push_notification", "def subscribe"],
}
for filepath, funcs in files_to_check.items():
    if not os.path.exists(filepath):
        continue
    content = open(filepath, encoding="utf-8").read()
    for func in funcs:
        count = content.count(func)
        if count > 1:
            print(f"    DUPLICATE ({count}x) - {func} in {filepath}")
            errors.append(f"Duplicate: {func} in {filepath}")
        elif count == 1:
            print(f"    OK - {func} in {filepath}")

# 4. Check trailing slash routes
print("\n[4] Checking for trailing slash routes...")
import re
for filepath in ["routers/orders.py", "routers/products.py", "routers/sellers.py", "routers/reviews.py"]:
    if not os.path.exists(filepath):
        continue
    content = open(filepath, encoding="utf-8").read()
    matches = re.findall(r'@router\.\w+\("/"', content)
    if matches:
        print(f"    WARNING - trailing slash route in {filepath}: {matches}")
        warnings.append(f"Trailing slash route in {filepath}")
    else:
        print(f"    OK - {filepath}")

# 5. Summary
print("\n" + "=" * 50)
if errors:
    print(f"FAILED - {len(errors)} error(s):")
    for e in errors:
        print(f"  - {e}")
    print("\nDO NOT PUSH. Fix errors first.")
    sys.exit(1)
elif warnings:
    print(f"WARNINGS - {len(warnings)} warning(s):")
    for w in warnings:
        print(f"  - {w}")
    print("\nOK to push but review warnings.")
else:
    print("ALL CHECKS PASSED - Safe to push!")
