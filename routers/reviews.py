from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from core.auth import get_current_user
from models.user import Review, Order, SellerProfile
from typing import Optional

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

@router.post("")
def create_review(
    order_id: int,
    rating: int,
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Can only review delivered orders")
    
    existing = db.query(Review).filter(Review.order_id == order_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already reviewed this order")
    
    review = Review(
        order_id=order_id,
        buyer_id=current_user.id,
        seller_id=order.seller_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    
    # Update seller rating
    seller = db.query(SellerProfile).filter(SellerProfile.id == order.seller_id).first()
    if seller:
        avg = db.query(func.avg(Review.rating)).filter(Review.seller_id == seller.id).scalar() or rating
        seller.rating = round(float(avg), 1)
    
    db.commit()
    db.refresh(review)
    return {"message": "Review submitted", "rating": rating}

@router.get("/seller/{seller_id}")
def get_seller_reviews(seller_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.seller_id == seller_id, Review.is_approved == True).order_by(Review.created_at.desc()).limit(20).all()
    return [{
        "id": r.id,
        "rating": r.rating,
        "comment": r.comment,
        "buyer_name": r.buyer.full_name if r.buyer else "Anonymous",
        "created_at": r.created_at,
    } for r in reviews]

@router.get("/check/{order_id}")
def check_review(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    review = db.query(Review).filter(Review.order_id == order_id).first()
    return {"reviewed": review is not None, "rating": review.rating if review else None}


@router.get("/admin/pending")
def get_pending_reviews(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    reviews = db.query(Review).filter(Review.is_approved == False).order_by(Review.created_at.desc()).all()
    return [{
        "id": r.id,
        "rating": r.rating,
        "comment": r.comment,
        "is_approved": r.is_approved,
        "buyer_name": r.buyer.full_name if r.buyer else "Anonymous",
        "seller_name": r.seller.shop_name if r.seller else "",
        "created_at": r.created_at,
    } for r in reviews]

@router.patch("/admin/{review_id}/approve")
def approve_review(review_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_approved = True
    # Update seller rating with approved reviews only
    seller = db.query(SellerProfile).filter(SellerProfile.id == review.seller_id).first()
    if seller:
        avg = db.query(func.avg(Review.rating)).filter(Review.seller_id == seller.id, Review.is_approved == True).scalar()
        seller.rating = round(float(avg), 1) if avg else seller.rating
    db.commit()
    return {"message": "Review approved"}

@router.delete("/admin/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}
