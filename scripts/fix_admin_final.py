path = r'C:\Users\Dell\Desktop\homemarketplace\frontend\src\pages\AdminPanel.tsx'
content = open(path, encoding='utf-8').read()

# The problem: expandedSeller block is outside the seller card div
# Find and fix the broken structure
old = '''                  </div>
                </div>
              </div>
              {expandedSeller === seller.id && ('''

new = '''                  </div>
                </div>
              {expandedSeller === seller.id && ('''

if old in content:
    content = content.replace(old, new)
    # Also fix the closing - remove the extra </div> before ))}
    old2 = '''                </div>
              )}
            </div>
            ))}'''
    new2 = '''                </div>
              )}
            </div>
          ))}'''
    content = content.replace(old2, new2)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ Fixed!")
else:
    # Try different approach - find the exact broken pattern
    idx = content.find('{expandedSeller === seller.id && (')
    if idx > 0:
        print("Found at index:", idx)
        print("Context around it:")
        print(repr(content[idx-200:idx+100]))
    else:
        print("❌ Pattern not found at all")
