from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .. import schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def calculate_next_occurrence(due_date: datetime, recurrence: models.RecurrenceType, interval: int) -> datetime:
    if recurrence == models.RecurrenceType.DAILY:
        return due_date + timedelta(days=interval)
    elif recurrence == models.RecurrenceType.WEEKLY:
        return due_date + timedelta(weeks=interval)
    elif recurrence == models.RecurrenceType.MONTHLY:
        return due_date + relativedelta(months=interval)
    elif recurrence == models.RecurrenceType.YEARLY:
        return due_date + relativedelta(years=interval)
    return due_date

@router.get("/", response_model=List[schemas.TaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Task).filter(models.Task.user_id == current_user.id).all()

@router.post("/", response_model=schemas.TaskResponse)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_task = models.Task(**task.model_dump(), user_id=current_user.id)
    db.add(new_task)
    
    # Log activity
    log = models.ActivityLog(user_id=current_user.id, action="Created Task", description=f"Created task '{task.title}'")
    db.add(log)
    
    db.commit()
    db.refresh(new_task)
    return new_task

@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(task, key, value)
        
    # Log activity
    log = models.ActivityLog(user_id=current_user.id, action="Updated Task", description=f"Updated task '{task.title}'")
    db.add(log)
        
    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/complete", response_model=schemas.TaskResponse)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.is_completed:
        return task
        
    if task.recurrence != models.RecurrenceType.NONE and task.due_date:
        # It's a recurring task, schedule the next occurrence
        task.due_date = calculate_next_occurrence(task.due_date, task.recurrence, task.recurrence_interval)
        # We don't mark it as completed, since it just rolls over to the next date!
        # Alternatively, we could create a new instance and complete this one. 
        # For simplicity in MVP, we just bump the due_date.
    else:
        task.is_completed = True
        
    # Log activity
    log = models.ActivityLog(user_id=current_user.id, action="Completed Task", description=f"Completed task '{task.title}'")
    db.add(log)
        
    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/snooze", response_model=schemas.TaskResponse)
def snooze_task(
    task_id: int,
    days: int = 0,
    hours: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    now = datetime.utcnow()
    if not task.due_date:
        task.due_date = now + timedelta(days=days, hours=hours)
    else:
        # If it's already overdue, snooze from today
        base_date = now if task.due_date < now else task.due_date
        task.due_date = base_date + timedelta(days=days, hours=hours)
        
    # Log activity
    log = models.ActivityLog(user_id=current_user.id, action="Snoozed Task", description=f"Snoozed task '{task.title}'")
    db.add(log)
        
    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/duplicate", response_model=schemas.TaskResponse)
def duplicate_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    original_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    
    if not original_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Create new task based on original
    new_task = models.Task(
        title=f"{original_task.title} (Copy)",
        description=original_task.description,
        category=original_task.category,
        priority=original_task.priority,
        due_date=original_task.due_date,
        recurrence=original_task.recurrence,
        recurrence_interval=original_task.recurrence_interval,
        user_id=current_user.id
    )
    db.add(new_task)
    
    # Log activity
    log = models.ActivityLog(user_id=current_user.id, action="Duplicated Task", description=f"Duplicated task '{original_task.title}'")
    db.add(log)
    
    db.commit()
    db.refresh(new_task)
    return new_task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Log activity
    log = models.ActivityLog(user_id=current_user.id, action="Deleted Task", description=f"Deleted task '{task.title}'")
    db.add(log)
        
    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}
