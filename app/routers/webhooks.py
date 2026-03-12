from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app import models, schemas, database
from app.routers.chat import execute_chat_command
from app.notifications.dispatcher import dispatch_notification
import os

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/twilio")
async def twilio_webhook(request: Request, db: Session = Depends(database.get_db)):
    """
    Handles incoming WhatsApp and SMS messages from Twilio.
    """
    form_data = await request.form()
    from_number = form_data.get("From", "")
    body = form_data.get("Body", "")

    if not from_number or not body:
        return Response(content="Invalid request", status_code=400)

    # For WhatsApp, Twilio sends "whatsapp:+1234567890"
    # For SMS, it sends "+1234567890"
    # Our DB stores it in whatever format the user provided, but we should be flexible.
    
    clean_number = from_number.replace("whatsapp:", "")
    
    user = db.query(models.User).filter(
        (models.User.whatsapp_number == from_number) | 
        (models.User.whatsapp_number == clean_number)
    ).first()

    if not user:
        # We can't identify the user
        print(f"[Twilio Webhook] Unknown sender: {from_number}")
        return Response(content="User not found", status_code=200) # Still return 200 to Twilio

    print(f"[Twilio Webhook] Received msg from {user.email}: {body}")
    
    # Execute the command
    req = schemas.ChatRequest(message=body)
    result = execute_chat_command(req=req, db=db, current_user=user)
    
    reply_text = result["reply"]
    
    # Send reply back via the same platform
    # The dispatcher handles the platform logic
    dispatch_notification(user, reply_text)

    return Response(content="OK", status_code=200)

@router.post("/slack")
async def slack_webhook(request: Request, db: Session = Depends(database.get_db)):
    """
    Handles incoming Slack messages (Slash commands or event subscriptions).
    """
    # Slack slash commands send data as x-www-form-urlencoded
    form_data = await request.form()
    user_id = form_data.get("user_id")
    text = form_data.get("text")
    
    if not user_id or not text:
        # Check if it's an event (JSON)
        try:
            payload = await request.json()
            if payload.get("type") == "url_verification":
                return {"challenge": payload.get("challenge")}
            
            event = payload.get("event", {})
            user_id = event.get("user")
            text = event.get("text")
            
            # Simple check to avoid loops (don't reply to bot messages)
            if event.get("bot_id"):
                return {"ok": True}
        except:
            return Response(content="Invalid request", status_code=400)

    if not user_id or not text:
        return Response(content="Invalid data", status_code=400)

    user = db.query(models.User).filter(models.User.slack_user_id == user_id).first()
    
    if not user:
        print(f"[Slack Webhook] Unknown user ID: {user_id}")
        return {"text": f"I don't recognize your Slack account (ID: {user_id}). Please add this ID to your profile settings."}

    print(f"[Slack Webhook] Received msg from {user.email}: {text}")
    
    req = schemas.ChatRequest(message=text)
    result = execute_chat_command(req=req, db=db, current_user=user)
    
    reply_text = result["reply"]
    
    # For Slack Slash commands, responding with JSON works as a direct reply
    return {"text": reply_text}
