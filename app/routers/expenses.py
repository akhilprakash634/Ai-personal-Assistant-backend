from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime
from app import schemas, models, auth
from app.database import get_db

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.get("/", response_model=List[schemas.ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()

@router.post("/", response_model=schemas.ExpenseResponse)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_expense = models.Expense(**expense.model_dump(), user_id=current_user.id)
    db.add(new_expense)
    
    # Log activity
    log = models.ActivityLog(
        user_id=current_user.id, 
        action="Logged Expense", 
        description=f"Recorded expense of {new_expense.amount} for {new_expense.category}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(new_expense)
    return new_expense

@router.get("/summary")
def get_expense_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> Dict[str, Any]:
    # Monthly summary
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_total = db.query(func.sum(models.Expense.amount)).filter(
        models.Expense.user_id == current_user.id,
        models.Expense.date >= month_start
    ).scalar() or 0
    
    # Category summary
    category_summary = db.query(
        models.Expense.category, 
        func.sum(models.Expense.amount).label("total")
    ).filter(
        models.Expense.user_id == current_user.id
    ).group_by(models.Expense.category).all()
    
    return {
        "monthly_total": monthly_total,
        "categories": {cat: total for cat, total in category_summary}
    }
