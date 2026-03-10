from .slack import send_slack_notification
from .teams import send_teams_notification
from .whatsapp import send_whatsapp_notification
from ..models import NotificationPlatform, User

def dispatch_notification(user: User, message: str):
    """
    Sends a notification to the user's preferred platform.
    """
    platform = user.notification_platform
    
    if platform == NotificationPlatform.SLACK and user.slack_webhook:
        return send_slack_notification(user.slack_webhook, message)
    
    elif platform == NotificationPlatform.TEAMS and user.teams_webhook:
        return send_teams_notification(user.teams_webhook, message)
    
    elif platform == NotificationPlatform.WHATSAPP and user.whatsapp_number:
        return send_whatsapp_notification(user.whatsapp_number, message)
    
    elif platform == NotificationPlatform.SMS and user.whatsapp_number:
        # SMS also uses the phone number field
        return send_whatsapp_notification(user.whatsapp_number, message)
    
    # Fallback to web/console if no platform specified or supported
    print(f"DEBUG: Web notification for {user.email}: {message}")
    return True
