import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, models, auth
from app.database import get_db
from app.chat_parser.engine import parse_chat_command
from app.services.tasks import complete_task_item
import pytz

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=schemas.ChatResponse)
def execute_chat_command(
    req: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    parsed = parse_chat_command(req.message, current_user.timezone or "UTC")
    intent = parsed["intent"]
    
    # Track this action in ActivityLog
    new_activity = models.ActivityLog(
        user_id=current_user.id,
        action="Chat Command",
        description=f"Received: {req.message[:50]}..."
    )
    
    # Check if this is the user's first chat interaction for onboarding
    chat_activity_count = db.query(models.ActivityLog).filter(
        models.ActivityLog.user_id == current_user.id,
        models.ActivityLog.action == "Chat Command"
    ).count()
    
    is_new_user = chat_activity_count == 0
    db.add(new_activity)
    db.commit() # Commit immediately so subsequent calls see the activity
    
    # Step 2: Intent Execution
    if intent == "greet":
        if is_new_user:
            reply = "Hi there! I'm your Personal AI Agent. I'm here to help you stay organized with tasks, reminders, and even track your expenses. How can I help you get started today?"
        else:
            import random
            greetings = [
                "Hello! Great to see you again. What's on your mind?",
                "Hi! I'm ready to help. What do you need to do?",
                "Hey! How's your day going? Need help with anything?",
                "Hello! I'm here. Just let me know what you need."
            ]
            reply = random.choice(greetings)
        return {"reply": reply}

    elif intent == "help":
        reply = (
            "I can help you with a few things:\n\n"
            "✅ *Tasks*: Say 'Remind me to call doctor tomorrow' or 'call mom tmr'.\n"
            "💰 *Expenses*: Say 'spent 350 on lunch' or 'coffee 200'.\n"
            "📋 *Management*: Use 'list tasks', 'done #ID', or 'delete #ID'.\n\n"
            "Just talk to me naturally, even with typos — I'll understand!"
        )
        return {"reply": reply}

    elif intent == "who_are_you":
        return {"reply": "I'm your Personal AI Agent, designed to keep your life organized and your budget on track. Think of me as your digital assistant that lives in your chat!"}

    # Conversational prefixes
    import random
    success_prefixes = ["Sure thing!", "You got it!", "Done!", "Of course.", "No problem!", "Got it.", "Okay —"]
    prefix = random.choice(success_prefixes)

    if intent == "create_reminder":
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
        
        if new_task.due_date:
            try:
                user_tz = pytz.timezone(current_user.timezone or "UTC")
                local_dt = pytz.utc.localize(new_task.due_date).astimezone(user_tz)
                # Conversational date phrasing
                date_str = local_dt.strftime('%B %d')
                if local_dt.date() == datetime.now(user_tz).date() + timedelta(days=1):
                    date_str = "tomorrow"
                elif local_dt.date() == datetime.now(user_tz).date():
                    date_str = "today"
                
                reply = f"Got it! I'll remind you to {new_task.title.lower()} {date_str} at {local_dt.strftime('%I:%M %p')}."
            except Exception:
                reply = f"{prefix} I’ve added that reminder for you."
        else:
            reply = f"{prefix} I’ve added '{new_task.title}' to your reminders."
            
        return {"reply": reply, "data": {"task": schemas.TaskResponse.model_validate(new_task).model_dump()}}

    elif intent == "create_expense":
        new_expense = models.Expense(
            amount=int(parsed["amount"]),
            category=parsed["category"],
            note=parsed["note"],
            date=parsed["date"],
            user_id=current_user.id
        )
        db.add(new_expense)
        db.commit()
        return {"reply": f"Okay — I’ve recorded ₹{int(parsed['amount'])} for {parsed['category'].lower()}.", "data": {"refresh_expenses": True}}

    elif intent == "create_subscription":
        new_sub = models.Subscription(
            name=parsed["name"],
            renewal_date=parsed["renewal_date"],
            recurrence=parsed["recurrence"],
            cost=int(parsed["cost"]) if parsed["cost"] else None,
            user_id=current_user.id
        )
        db.add(new_sub)
        db.commit()
        renewal_str = parsed["renewal_date"].strftime('%B %d') if parsed["renewal_date"] else "soon"
        reply = f"I’ll remind you about your {parsed['name']} renewal on {renewal_str}."
        if parsed["recurrence"] == models.RecurrenceType.MONTHLY:
            reply = f"Got it—I'll watch your {parsed['name']} renewal on the {parsed['renewal_date'].day}th every month."
        return {"reply": reply}

    elif intent == "create_followup":
        new_task = models.Task(
            title=parsed["title"],
            due_date=parsed["due_date"],
            user_id=current_user.id,
            category="Personal"
        )
        db.add(new_task)
        db.commit()
        return {"reply": f"Got it — I’ll remind you to {parsed['title'].lower()}."}

    elif intent == "show_dashboard":
        filter_type = parsed.get("filter", "all")
        user_tz = pytz.timezone(current_user.timezone or "UTC")
        now_local = datetime.now(user_tz)
        today_local = now_local.date()
        
        # Build a text list of tasks for chat-only interfaces
        tasks_query = db.query(models.Task).filter(models.Task.user_id == current_user.id, models.Task.is_completed == False)
        
        if filter_type == "today":
            # Filter tasks due on today's local date
            tasks = [t for t in tasks_query.all() if t.due_date and pytz.utc.localize(t.due_date).astimezone(user_tz).date() == today_local]
            reply = "I'm looking at your reminders for today. Here's what's on your plate:"
            if tasks:
                task_list = "\n".join([f"- **[#{t.id}]** {t.title}" for t in tasks])
                reply += f"\n{task_list}"
            else:
                reply = "You don't have anything scheduled for today! Enjoy your day. ✨"
            return {"reply": reply, "data": {"action": "navigate", "page": "dashboard", "filter": "today"}}
            
        elif filter_type == "overdue":
            # Tasks with due_date < now_local
            tasks = [t for t in tasks_query.all() if t.due_date and pytz.utc.localize(t.due_date).astimezone(user_tz) < now_local]
            reply = "I've pulled up your overdue items. These might need your attention:"
            if tasks:
                task_list = "\n".join([f"- **[#{t.id}]** {t.title}" for t in tasks])
                reply += f"\n{task_list}"
            else:
                reply = "Nothing is overdue right now. Great job! ✅"
            return {"reply": reply, "data": {"action": "navigate", "page": "dashboard", "filter": "overdue"}}
            
        elif filter_type == "upcoming":
            # Tasks due after today_local
            tasks = [t for t in tasks_query.all() if t.due_date and pytz.utc.localize(t.due_date).astimezone(user_tz).date() > today_local]
            reply = "Here's what me and you have coming up soon:"
            if tasks:
                task_list = "\n".join([f"- **[#{t.id}]** {t.title}" for t in tasks])
                reply += f"\n{task_list}"
            else:
                reply = "Your schedule looks clear for the next few days."
            return {"reply": reply, "data": {"action": "navigate", "page": "dashboard", "filter": "upcoming"}}
            
        return {"reply": "Taking you to your dashboard.", "data": {"action": "navigate", "page": "dashboard"}}

    elif intent == "query_reminders":
        tasks = db.query(models.Task).filter(models.Task.user_id == current_user.id, models.Task.is_completed == False).order_by(models.Task.due_date.asc()).all()
        if not tasks:
            return {"reply": "You don't have any pending reminders right now! Everything is clear. 👍"}
        task_list = "\n".join([f"- **[#{t.id}]** {t.title}" for t in tasks])
        return {"reply": f"Here’s what I have for you:\n{task_list}"}

    elif intent == "query_expenses":
        return {"reply": "I'm opening your expense overview for you.", "data": {"action": "navigate", "page": "expenses"}}

    elif intent == "update_reminder":
        # Handle "complete" action
        task_id = parsed.get("id")
        query = parsed.get("query")
        
        task_query = db.query(models.Task).filter(models.Task.user_id == current_user.id, models.Task.is_completed == False)
        if task_id:
            task = task_query.filter(models.Task.id == task_id).first()
        elif query:
            task = task_query.filter(models.Task.title.ilike(f"%{query}%")).first()
        else:
            task = task_query.order_by(models.Task.due_date.asc()).first()

        if task:
            complete_task_item(db, task, current_user.id)
            return {"reply": "Nice 👍 I’ve marked that as done for you.", "data": {"refresh_tasks": True}}
        return {"reply": "I couldn't find that reminder to complete."}

    elif intent == "delete_reminder":
        task_id = parsed.get("id")
        query = parsed.get("query")
        task_query = db.query(models.Task).filter(models.Task.user_id == current_user.id)
        if task_id:
            task = task_query.filter(models.Task.id == task_id).first()
        elif query:
            task = task_query.filter(models.Task.title.ilike(f"%{query}%")).first()
        else:
            return {"reply": "Which reminder should I delete?"}
            
        if task:
            db.delete(task)
            db.commit()
            return {"reply": "I’ve removed that for you.", "data": {"refresh_tasks": True}}
        return {"reply": "I couldn't find that reminder."}

    elif intent == "clarify":
        missing = parsed["missing"]
        if missing == "date":
            # Save the title in session/log for next time? 
            return {"reply": "Sure, when should I remind you?"}
        elif missing == "title":
            return {"reply": "I can help with that! What should I remember?"}
        return {"reply": "Could you give me more details?"}

    elif intent == "none":
        fallback_replies = [
            "I'm not quite sure I caught that. Did you mean to create a reminder or log an expense?",
            "I'm still learning! Could you rephrase that? For example, 'Remind me to...' or 'I spent...'",
            "Hmm, I didn't quite get that. Try saying 'help' if you're not sure what I can do!"
        ]
        return {"reply": random.choice(fallback_replies)}

    return {"reply": "I'm not sure how to handle that yet, but I'm learning!"}
