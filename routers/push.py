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
    print(f"Push: found {len(subs)} subscriptions for user {user_id}")
    
    for sub in subs:
        try:
            subscription = json.loads(sub.subscription_json)
            print(f"Push: sending to endpoint {subscription.get('endpoint', 'unknown')[:50]}")
            webpush(
                subscription_info=subscription,
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=private_key,
                vapid_claims={"sub": f"mailto:{claims_email}"},
            )
            print(f"Push: sent successfully")
        except WebPushException as e:
            print(f"Push WebPushException: {e}")
            print(f"Push response: {e.response.text if hasattr(e, 'response') and e.response else 'no response'}")
            if "410" in str(e) or "404" in str(e):
                db.delete(sub)
                db.commit()
        except Exception as e:
            print(f"Push error: {type(e).__name__}: {e}")

@router.post("/test")
def test_push(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    send_push_notification(
        db=db,
        user_id=current_user.id,
        title="Test Notification",
        body="Push notifications are working!",
        url="/seller/dashboard"
    )
    return {"status": "sent", "user_id": current_user.id}
