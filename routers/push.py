from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
from models.user import PushSubscription
from pydantic import BaseModel
import json, os

router = APIRouter(prefix="/api/push", tags=["push"])

class SubscriptionData(BaseModel):
    subscription: dict

@router.post("/subscribe")
def subscribe(data: SubscriptionData, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sub_json = json.dumps(data.subscription)
    # Check if already exists
    existing = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id,
        PushSubscription.subscription_json == sub_json
    ).first()
    if not existing:
        sub = PushSubscription(user_id=current_user.id, subscription_json=sub_json)
        db.add(sub)
        db.commit()
    return {"status": "subscribed"}

@router.delete("/unsubscribe")
def unsubscribe(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db.query(PushSubscription).filter(PushSubscription.user_id == current_user.id).delete()
    db.commit()
    return {"status": "unsubscribed"}

@router.get("/vapid-public-key")
def get_vapid_public_key():
    key = os.getenv("VAPID_PUBLIC_KEY", "")
    if not key:
        raise HTTPException(status_code=500, detail="VAPID not configured")
    return {"public_key": key}

def send_push_notification(db: Session, user_id: int, title: str, body: str, url: str = "/seller/dashboard"):
    from pywebpush import webpush, WebPushException
    import json, os
    
    private_key = os.getenv("VAPID_PRIVATE_KEY")
    public_key = os.getenv("VAPID_PUBLIC_KEY")
    claims_email = os.getenv("VAPID_CLAIMS_EMAIL", "admin@homemarket.ae")
    
    if not private_key or not public_key:
        print("VAPID keys not configured")
        return
    
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    
    for sub in subs:
        try:
            subscription = json.loads(sub.subscription_json)
            webpush(
                subscription_info=subscription,
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=private_key,
                vapid_claims={"sub": f"mailto:{claims_email}"},
            )
        except WebPushException as e:
            print(f"Push failed: {e}")
            if "410" in str(e) or "404" in str(e):
                # Subscription expired — remove it
                db.delete(sub)
                db.commit()
        except Exception as e:
            print(f"Push error: {e}")
