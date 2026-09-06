import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
email_path = os.path.join(BACKEND, 'services', 'email_service.py')
content = open(email_path, encoding='utf-8').read()

# Remove the hardcoded key
old = 'RESEND_API_KEY = os.getenv("RESEND_API_KEY", "re_UdfGhYMG_7XgRvaPEjNq6di9maDKthoPY")'
new = 'RESEND_API_KEY = os.getenv("RESEND_API_KEY")'

content = content.replace(old, new)
open(email_path, 'w', encoding='utf-8').write(content)
print("Done - API key removed from code")
