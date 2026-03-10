from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dateutil import tz
from typing import Dict, Any, List

from .. import schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> Dict[str, Any]:
    
    # Get user's timezone
    user_tz = tz.gettz(current_user.timezone or "UTC")
    now = datetime.now(user_tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Store now as naive UTC for DB comparisons if needed, 
    # but SQLAlchemy handle Offset-naive vs offset-aware. 
    # We'll stick to naive UTC for consistency with existing data if needed,
    # or just use the localized bounds and strip tz for comparison.
    today_start_utc = today_start.astimezone(tz.UTC).replace(tzinfo=None)
    today_end_utc = today_end.astimezone(tz.UTC).replace(tzinfo=None)
    now_utc = now.astimezone(tz.UTC).replace(tzinfo=None)
    
    # Base query for incomplete tasks
    base_query = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.is_completed == False
    )
    
    # Overdue tasks
    overdue_tasks = base_query.filter(
        models.Task.due_date < today_start_utc
    ).all()
    
    # Today tasks
    today_tasks = base_query.filter(
        models.Task.due_date >= today_start_utc,
        models.Task.due_date < today_end_utc
    ).all()
    
    # Upcoming tasks
    upcoming_tasks = base_query.filter(
        models.Task.due_date >= today_end_utc
    ).all()
    
    # Tasks without due date
    no_date_tasks = base_query.filter(
        models.Task.due_date == None
    ).all()

    # High priority tasks (active)
    high_priority_count = base_query.filter(
        models.Task.priority == "high"
    ).count()

    # Recently completed tasks (last 24 hours)
    recently_completed_tasks = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.is_completed == True,
        models.Task.due_date >= now_utc - timedelta(days=1)
    ).all()
    
    def serialize_tasks(tasks):
        return [schemas.TaskResponse.model_validate(t).model_dump() for t in tasks]
        
    return {
        "overdue": serialize_tasks(overdue_tasks),
        "today": serialize_tasks(today_tasks),
        "upcoming": serialize_tasks(upcoming_tasks),
        "no_date": serialize_tasks(no_date_tasks),
        "recently_completed": serialize_tasks(recently_completed_tasks),
        "counts": {
            "overdue": len(overdue_tasks),
            "today": len(today_tasks),
            "upcoming": len(upcoming_tasks),
            "high_priority": high_priority_count,
            "recently_completed": len(recently_completed_tasks),
            "total_active": len(overdue_tasks) + len(today_tasks) + len(upcoming_tasks) + len(no_date_tasks)
        }
    }


@router.get("/activity", response_model=List[schemas.ActivityLogResponse])
def get_dashboard_activity(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    activities = db.query(models.ActivityLog).filter(
        models.ActivityLog.user_id == current_user.id
    ).order_by(models.ActivityLog.timestamp.desc()).limit(limit).all()
    
    return activities
