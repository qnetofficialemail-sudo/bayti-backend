import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"

content = open(os.path.join(BACKEND, "routers/ai.py"), encoding='utf-8').read()

# Find the system prompt in pricing advisor
idx = content.find("pricing advisor")
if idx < 0:
    idx = content.find("pricing-advisor")
    # Get the function body after the route decorator
    idx = content.find("def ai_pricing_advisor")

# Show 3000 chars from the function
print(content[idx:idx+3000])
