import os
import time
import requests
import traceback
import threading
from app.database import SessionLocal
from app.models import User
from app.routers.chat import execute_chat_command
from app import schemas
from app.notifications.telegram import send_telegram_notification

def telegram_polling_worker():
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram Bot Token not found. Polling disabled.")
        return
        
    offset = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    print("Started Telegram long-polling worker...")
    
    while True:
        try:
            # timeout=30 in params tells Telegram to wait up to 30s before returning empty.
            # timeout=35 in requests prevents python from dropping the connection before Telegram does.
            response = requests.get(f"{url}?offset={offset}&timeout=30", timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update and "text" in update["message"]:
                            chat_id = str(update["message"]["chat"]["id"])
                            text = update["message"]["text"]
                            
                            db = SessionLocal()
                            try:
                                user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
                                if user:
                                    print(f"[Telegram] Received msg from {user.email}: {text}")
                                    req = schemas.ChatRequest(message=text)
                                    result = execute_chat_command(req=req, db=db, current_user=user)
                                    reply_text = result["reply"]
                                    send_telegram_notification(user.telegram_chat_id, reply_text)
                                else:
                                    # Unknown user
                                    msg = f"Hello! I don't recognize this account. Your Telegram Chat ID is {chat_id}. Please add it to your profile settings."
                                    requests.post(
                                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                                        json={"chat_id": chat_id, "text": msg}
                                    )
                            except Exception as e:
                                print(f"[Telegram] Error processing message: {e}")
                                traceback.print_exc()
                            finally:
                                db.close()
        except requests.exceptions.RequestException as e:
            # Network error or timeout. Sleep briefly before retrying.
            time.sleep(5)
        except Exception as e:
            print(f"[Telegram] Critical polling error: {e}")
            traceback.print_exc()
            time.sleep(5)

def start_telegram_polling():
    thread = threading.Thread(target=telegram_polling_worker, daemon=True)
    thread.start()
