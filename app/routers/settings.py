from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, models, auth
from app.database import get_db

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=schemas.UserResponse)
def get_settings(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("/", response_model=schemas.UserResponse)
def update_settings(
    settings: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    update_data = settings.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user
