import requests
import logging

logger = logging.getLogger(__name__)

def send_slack_notification(webhook_url: str, message: str):
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
