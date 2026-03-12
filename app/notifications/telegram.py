import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_notification(chat_id: str, message: str) -> bool:
    """
    Sends a notification via Telegram Bot API to a specific chat_id.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured. Skipping notification.")
        return False
        
    if not chat_id:
        logger.warning("No Telegram chat_id provided.")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("ok"):
             logger.info(f"Telegram notification sent successfully to {chat_id}")
             return True
        else:
             logger.error(f"Telegram API error: {result}")
             return False
    except requests.exceptions.HTTPError as e:
        logger.error(f"Failed to send Telegram notification (HTTP Error): {e} - Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {str(e)}")
        return False
