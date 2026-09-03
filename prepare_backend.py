import os

files = {}

files['requirements.txt'] = '''fastapi==0.141.1
uvicorn==0.52.3
sqlalchemy==2.0.52
psycopg2-binary==2.9.9
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.32
aiofiles==25.1.0
pillow==12.3.0
python-dotenv==1.2.2
pydantic[email]==2.13.4
twilio==9.11.0
anthropic==0.117.0
bcrypt==4.0.1
alembic==1.13.1
'''

files['.gitignore'] = '''.env
__pycache__/
*.pyc
*.db
uploads/
*.sqlite
.DS_Store
'''

files['Procfile'] = '''web: uvicorn main:app --host 0.0.0.0 --port $PORT
'''

files['runtime.txt'] = '''python-3.12.3
'''

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

print("\nBackend production files ready!")
