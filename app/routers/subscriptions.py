from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models, auth
from app.database import get_db

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("/", response_model=List[schemas.SubscriptionResponse])
def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Subscription).filter(models.Subscription.user_id == current_user.id).all()

@router.post("/", response_model=schemas.SubscriptionResponse)
def create_subscription(
    subscription: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_sub = models.Subscription(**subscription.model_dump(), user_id=current_user.id)
    db.add(new_sub)
    
    # Log activity
    log = models.ActivityLog(
        user_id=current_user.id, 
        action="Added Subscription", 
        description=f"Now tracking {new_sub.name} subscription"
    )
    db.add(log)
    
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.delete("/{sub_id}")
def delete_subscription(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    sub = db.query(models.Subscription).filter(
        models.Subscription.id == sub_id,
        models.Subscription.user_id == current_user.id
    ).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    db.delete(sub)
    db.commit()
    return {"detail": "Subscription removed"}
