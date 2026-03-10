from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, auth
from ..database import get_db
from ..chat_parser.engine import parse_chat_command

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=schemas.ChatResponse)
def execute_chat_command(
    req: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    parsed = parse_chat_command(req.message)
    intent = parsed["intent"]
    
    if intent == "create_task":
        data = parsed["data"]
        new_task = models.Task(
            title=data["title"],
            due_date=data["due_date"],
            priority=data["priority"],
            category=data["category"],
            recurrence=data["recurrence"],
            recurrence_interval=data["recurrence_interval"],
            user_id=current_user.id
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        reply = f"Done — I've scheduled '{new_task.title}' for you."
        if new_task.due_date:
            reply = f"All set! I've scheduled '{new_task.title}' for {new_task.due_date.strftime('%B %d at %I:%M %p')}."
        
        if new_task.recurrence != models.RecurrenceType.NONE:
            reply += f" I'll make sure to remind you {new_task.recurrence}."
        elif "every" in req.message.lower() or "monthly" in req.message.lower() or "weekly" in req.message.lower():
            reply += " This sounds like a recurring task. Should I set it to repeat for you?"

        return {"reply": reply, "data": {"task": schemas.TaskResponse.model_validate(new_task).model_dump()}}
        
    elif intent == "show_dashboard":
        return {"reply": f"Showing your dashboard with {parsed['filter']} tasks.", "data": {"action": "navigate", "page": "dashboard", "filter": parsed['filter']}}
        
    elif intent == "navigate":
        return {"reply": f"Navigating to {parsed['page']} page.", "data": {"action": "navigate", "page": parsed['page']}}
        
    elif intent == "mark_done":
        # Usually needs a specific task. We'll find the most recently due open task matching the query if provided
        query = parsed.get("task_query")
        task_query = db.query(models.Task).filter(
            models.Task.user_id == current_user.id,
            models.Task.is_completed == False
        )
        
        if query:
            task_query = task_query.filter(models.Task.title.ilike(f"%{query}%"))
            
        task = task_query.order_by(models.Task.due_date.asc()).first()
        
        if task:
            # We don't implement the full complete logic here due to circular deps, just a simple flag. 
            # Ideally this calls the same logic as the tasks router
            task.is_completed = True
            db.commit()
            return {"reply": f"Got it! I've marked '{task.title}' as completed for you. Great job!", "data": {"refresh_tasks": True}}
        return {"reply": "I couldn't find an active task matching that description. Want me to create a new one instead?"}
        
    elif intent == "snooze":
        # Snooze the most overdue task or the upcoming one
        task = db.query(models.Task).filter(
            models.Task.user_id == current_user.id,
            models.Task.is_completed == False
        ).order_by(models.Task.due_date.asc()).first()
        
        if task:
            from datetime import timedelta, datetime
            now = datetime.utcnow()
            days = parsed["days"]
            base = now if (not task.due_date or task.due_date < now) else task.due_date
            task.due_date = base + timedelta(days=days)
            db.commit()
            return {"reply": f"No problem. I've snoozed '{task.title}' for {days} days. It'll be back on your radar then!", "data": {"refresh_tasks": True}}
            
        return {"reply": "I couldn't find a task to snooze right now. Is there something else I can help you with?"}
        
    return {"reply": "I'm not sure how to handle that command."}
