from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import SessionLocal
from ..models import Task, Reminder, User, ActivityLog
from ..notifications.dispatcher import dispatch_notification
from datetime import timedelta

def generate_reminders():
    print(f"[{datetime.utcnow()}] Checking for due tasks to send reminders...")
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        # 1. Initial Reminders (Immediate)
        due_tasks = db.query(Task).filter(
            Task.is_completed == False,
            Task.due_date <= now
        ).all()
        
        for task in due_tasks:
            existing = db.query(Reminder).filter(
                Reminder.task_id == task.id,
                Reminder.is_followup == False,
                Reminder.is_ensure == False
            ).first()
            
            if not existing:
                reminder = Reminder(
                    message=f"🔔 REMINDER: '{task.title}' is due now!",
                    scheduled_for=now,
                    is_sent=False,
                    is_followup=False,
                    is_ensure=False,
                    task_id=task.id,
                    user_id=task.user_id
                )
                db.add(reminder)
        
        # 2. Follow-up Reminders (1 hour later)
        followup_threshold = now - timedelta(hours=1)
        tasks_needing_followup = db.query(Task).join(Reminder).filter(
            Task.is_completed == False,
            Reminder.is_sent == True,
            Reminder.is_followup == False,
            Reminder.is_ensure == False,
            Reminder.scheduled_for <= followup_threshold
        ).all()

        for task in tasks_needing_followup:
            existing_followup = db.query(Reminder).filter(
                Reminder.task_id == task.id,
                Reminder.is_followup == True
            ).first()
            
            if not existing_followup:
                followup = Reminder(
                    message=f"⚠️ FOLLOW-UP: '{task.title}' is still pending. Did you forget?",
                    scheduled_for=now,
                    is_sent=False,
                    is_followup=True,
                    is_ensure=False,
                    task_id=task.id,
                    user_id=task.user_id
                )
                db.add(followup)

        # 3. Ensure Reminders (3 hours after Follow-up = 4 hours after Initial)
        ensure_threshold = now - timedelta(hours=3)
        tasks_needing_ensure = db.query(Task).join(Reminder).filter(
            Task.is_completed == False,
            Reminder.is_sent == True,
            Reminder.is_followup == True,
            Reminder.is_ensure == False,
            Reminder.scheduled_for <= ensure_threshold
        ).all()

        for task in tasks_needing_ensure:
            existing_ensure = db.query(Reminder).filter(
                Reminder.task_id == task.id,
                Reminder.is_ensure == True
            ).first()
            
            if not existing_ensure:
                ensure = Reminder(
                    message=f"🚨 ENSURE: '{task.title}' MUST be completed. Please confirm or snooze.",
                    scheduled_for=now,
                    is_sent=False,
                    is_followup=False,
                    is_ensure=True,
                    task_id=task.id,
                    user_id=task.user_id
                )
                db.add(ensure)

        db.commit()

        # 4. Dispatch all unsent reminders
        unsent_reminders = db.query(Reminder).filter(Reminder.is_sent == False).all()
        for r in unsent_reminders:
            user = db.query(User).filter(User.id == r.user_id).first()
            if user:
                success = dispatch_notification(user, r.message)
                if success:
                    r.is_sent = True
                    # Log the activity
                    activity = ActivityLog(
                        user_id=user.id,
                        action="Notification Sent",
                        description=f"Sent {user.notification_platform.value} reminder: {r.message}"
                    )
                    db.add(activity)
        
        db.commit()
    finally:
        db.close()

def send_daily_summary():
    print(f"[{datetime.utcnow()}] Generating daily morning summary for all users...")
    db: Session = SessionLocal()
    try:
        from datetime import date
        today = date.today()
        users = db.query(User).all()
        for user in users:
            # Fetch tasks due today (or overdue and not completed)
            today_tasks = db.query(Task).filter(
                Task.user_id == user.id,
                Task.is_completed == False,
                Task.due_date <= datetime.combine(today, datetime.max.time())
            ).all()
            
            if today_tasks:
                msg = f"🌅 Good morning! Here are your tasks for today:\n"
                for i, t in enumerate(today_tasks, 1):
                    msg += f"{i}. {t.title}\n"
                msg += "\nStay productive! 💪"
                success = dispatch_notification(user, msg)
                if success:
                    activity = ActivityLog(
                        user_id=user.id,
                        action="Daily Summary Sent",
                        description=f"Sent morning summary via {user.notification_platform.value}"
                    )
                    db.add(activity)
    finally:
        db.close()

scheduler = BackgroundScheduler()
# Check for task reminders every minute
scheduler.add_job(generate_reminders, 'interval', minutes=1)
# Send daily summary every morning at 8:00 AM
scheduler.add_job(send_daily_summary, 'cron', hour=8, minute=0)

def start_scheduler():
    scheduler.start()
    
def stop_scheduler():
    scheduler.shutdown()
