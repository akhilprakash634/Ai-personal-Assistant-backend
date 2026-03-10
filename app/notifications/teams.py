import requests
import logging

logger = logging.getLogger(__name__)

def send_teams_notification(webhook_url: str, message: str):
    try:
        # MS Teams Connector webhook format
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": message,
                                "weight": "bolder",
                                "size": "medium"
                            }
                        ],
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.0"
                    }
                }
            ]
        }
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Teams notification: {e}")
        return False
