import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
main_path = os.path.join(BACKEND, "main.py")
content = open(main_path, encoding="utf-8").read()

# Show full main.py
lines = content.split("\n")
for i, line in enumerate(lines):
    print(f"{i+1:4}: {line}")
