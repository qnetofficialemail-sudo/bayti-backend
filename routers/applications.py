from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
