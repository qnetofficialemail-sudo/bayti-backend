import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'

# ── 1. Add SellerApplication model to models/user.py ──
model_path = os.path.join(BACKEND, 'models', 'user.py')
content = open(model_path, encoding='utf-8').read()

application_model = '''

class SellerApplication(Base):
    __tablename__ = "seller_applications"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    area = Column(String, nullable=False)
    city = Column(String, default="Dubai")
    what_they_sell = Column(Text, nullable=False)
    doc_1_url = Column(Text, nullable=True)
    doc_2_url = Column(Text, nullable=True)
    doc_3_url = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    invite_token = Column(String, nullable=True, unique=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
'''

if 'SellerApplication' not in content:
    content = content.rstrip() + '\n' + application_model
    open(model_path, 'w', encoding='utf-8').write(content)
    print("Done - SellerApplication model added")
else:
    print("Skip - SellerApplication already exists")

# ── 2. Add upload_document function to cloudinary_upload.py ──
cloud_path = os.path.join(BACKEND, 'services', 'cloudinary_upload.py')
cloud = open(cloud_path, encoding='utf-8').read()

doc_upload = '''
def upload_application_doc(file_bytes: bytes, filename: str) -> str:
    """Upload seller application document to Cloudinary (private folder)."""
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="bayti/applications",
        public_id=filename.rsplit(".", 1)[0],
        overwrite=False,
        resource_type="auto",
    )
    return result["secure_url"]
'''

if 'upload_application_doc' not in cloud:
    cloud = cloud.rstrip() + '\n' + doc_upload
    open(cloud_path, 'w', encoding='utf-8').write(cloud)
    print("Done - upload_application_doc added to cloudinary_upload.py")
else:
    print("Skip - upload_application_doc already exists")

# ── 3. Create routers/applications.py ──
app_router_path = os.path.join(BACKEND, 'routers', 'applications.py')
app_router = '''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from core.auth import get_current_admin
from models.user import SellerApplication, User
from services.cloudinary_upload import upload_application_doc
import secrets

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("/apply")
async def submit_application(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    area: str = Form(...),
    city: str = Form("Dubai"),
    what_they_sell: str = Form(...),
    doc_1: Optional[UploadFile] = File(None),
    doc_2: Optional[UploadFile] = File(None),
    doc_3: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Check not already applied or registered
    existing = db.query(SellerApplication).filter(SellerApplication.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An application with this email already exists")
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    doc_urls = []
    for doc in [doc_1, doc_2, doc_3]:
        if doc and doc.filename:
            file_bytes = await doc.read()
            url = upload_application_doc(file_bytes, doc.filename)
            doc_urls.append(url)
        else:
            doc_urls.append(None)

    application = SellerApplication(
        full_name=full_name,
        email=email,
        phone=phone,
        area=area,
        city=city,
        what_they_sell=what_they_sell,
        doc_1_url=doc_urls[0],
        doc_2_url=doc_urls[1],
        doc_3_url=doc_urls[2],
        status="pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return {"message": "Application submitted successfully", "id": application.id}


@router.get("/admin/list")
def list_applications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    q = db.query(SellerApplication)
    if status:
        q = q.filter(SellerApplication.status == status)
    apps = q.order_by(SellerApplication.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "full_name": a.full_name,
            "email": a.email,
            "phone": a.phone,
            "area": a.area,
            "city": a.city,
            "what_they_sell": a.what_they_sell,
            "doc_1_url": a.doc_1_url,
            "doc_2_url": a.doc_2_url,
            "doc_3_url": a.doc_3_url,
            "status": a.status,
            "invite_token": a.invite_token,
            "notes": a.notes,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in apps
    ]


@router.patch("/admin/{app_id}/approve")
def approve_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    app = db.query(SellerApplication).filter(SellerApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    token = secrets.token_urlsafe(32)
    app.status = "approved"
    app.invite_token = token
    db.commit()
    return {
        "message": "Application approved",
        "invite_token": token,
        "registration_link": f"/seller-register?token={token}"
    }


@router.patch("/admin/{app_id}/reject")
def reject_application(
    app_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    app = db.query(SellerApplication).filter(SellerApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.status = "rejected"
    if notes:
        app.notes = notes
    db.commit()
    return {"message": "Application rejected"}


@router.get("/validate-token/{token}")
def validate_invite_token(token: str, db: Session = Depends(get_db)):
    app = db.query(SellerApplication).filter(
        SellerApplication.invite_token == token,
        SellerApplication.status == "approved"
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Invalid or expired invite token")
    return {
        "valid": True,
        "full_name": app.full_name,
        "email": app.email,
        "phone": app.phone,
    }
'''

open(app_router_path, 'w', encoding='utf-8').write(app_router)
print("Done - routers/applications.py created")

# ── 4. Register router in main.py ──
main_path = os.path.join(BACKEND, 'main.py')
main = open(main_path, encoding='utf-8').read()

if 'applications' not in main:
    old_import = 'from routers import'
    # Find first router import line
    idx = main.find('from routers import')
    if idx < 0:
        idx = main.find('from routers.')
    if idx >= 0:
        eol = main.find('\n', idx)
        main = main[:eol+1] + 'from routers import applications as applications_router\n' + main[eol+1:]
    # Find include_router section
    old_include = 'app.include_router'
    idx2 = main.rfind(old_include)
    eol2 = main.find('\n', idx2)
    main = main[:eol2+1] + 'app.include_router(applications_router.router)\n' + main[eol2+1:]
    open(main_path, 'w', encoding='utf-8').write(main)
    print("Done - applications router registered in main.py")
else:
    print("Skip - applications already in main.py")

# ── 5. DB Migration ──
migrate = '''import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS seller_applications (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                phone VARCHAR,
                area VARCHAR NOT NULL,
                city VARCHAR DEFAULT 'Dubai',
                what_they_sell TEXT NOT NULL,
                doc_1_url TEXT,
                doc_2_url TEXT,
                doc_3_url TEXT,
                status VARCHAR DEFAULT 'pending',
                invite_token VARCHAR UNIQUE,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        print("Done - seller_applications table created")
    except Exception as e:
        print(f"Table: {e}")
    conn.commit()
print("Migration complete")
'''
open(os.path.join(BACKEND, 'migrate_applications.py'), 'w', encoding='utf-8').write(migrate)
print("Done - migrate_applications.py created")
