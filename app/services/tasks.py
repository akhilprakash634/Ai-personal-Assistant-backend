from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app import models

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

def complete_task_item(db: Session, task: models.Task, user_id: int) -> str:
    """
    Unifies task completion logic including recurrence handling and activity logging.
    Returns a summary of what happened.
    """
    if task.is_completed:
        return f"'{task.title}' was already completed."
        
    if task.recurrence != models.RecurrenceType.NONE and task.due_date:
        # It's a recurring task, schedule the next occurrence
        old_date = task.due_date
        task.due_date = calculate_next_occurrence(task.due_date, task.recurrence, task.recurrence_interval)
        # Log activity
        log = models.ActivityLog(
            user_id=user_id, 
            action="Completed Recurring Task", 
            description=f"Completed occurrence of '{task.title}' (was due {old_date.strftime('%Y-%m-%d')}). Next due: {task.due_date.strftime('%Y-%m-%d')}"
        )
        db.add(log)
        db.commit()
        return f"Marked occurrence of '{task.title}' as done. Next one scheduled for {task.due_date.strftime('%B %d')}."
    else:
        task.is_completed = True
        # Log activity
        log = models.ActivityLog(
            user_id=user_id, 
            action="Completed Task", 
            description=f"Completed task '{task.title}'"
        )
        db.add(log)
        db.commit()
        return f"I've marked '{task.title}' as completed."
