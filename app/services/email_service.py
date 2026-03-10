import logging

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str):
    """
    Placeholder for email sending logic. 
    In production, integrate with SendGrid, Mailgun, or SMTP.
    """
    logger.info(f"SIMULATED EMAIL to {to_email}: Subject: {subject}")
    # print(f"📧 [Email Simulation] To: {to_email} | Subject: {subject}")
    return True

async def send_due_soon_reminder(email: str, task_title: str):
    return await send_email(
        email, 
        f"Reminder: {task_title} is due soon", 
        f"Hi! Just a friendly reminder that '{task_title}' is coming up soon. You've got this!"
    )

async def send_overdue_alert(email: str, task_title: str):
    return await send_email(
        email, 
        f"⚠️ Overdue: {task_title}", 
        f"Heads up! '{task_title}' is now overdue. Let's get it done or snooze it for later."
    )

async def send_daily_summary(email: str, tasks_count: int):
    return await send_email(
        email, 
        "Your Daily Summary", 
        f"Good morning! You have {tasks_count} tasks scheduled for today. Have a productive day!"
    )
