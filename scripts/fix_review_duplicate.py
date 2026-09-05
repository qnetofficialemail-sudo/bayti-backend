path = r'C:\Users\Dell\Desktop\homemarketplace\backend\models\user.py'
content = open(path, encoding='utf-8').read()

# Find and remove the duplicate Review class
# Keep only the first occurrence
first = content.find('class Review(Base):')
second = content.find('class Review(Base):', first + 1)

if second != -1:
    # Find where the second Review class ends (at the next class definition)
    next_class = content.find('\nclass ', second + 1)
    if next_class != -1:
        # Remove from second occurrence to next class
        content = content[:second] + content[next_class+1:]
    print("✅ Duplicate removed")
else:
    print("No duplicate found")

open(path, 'w', encoding='utf-8').write(content)

# Verify
count = content.count('class Review(Base):')
print(f"Review class now appears {count} time(s)")
