import os
import requests
from typing import Optional

# You would typically use the twilio python library, but for simplicity 
# and to avoid extra heavy dependencies, we can use their REST API.

def send_whatsapp_notification(phone_number: str, message: str):
    """
    Sends a WhatsApp message using Twilio's API.
    Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886") # Twilio Sandbox number

    if not account_sid or not auth_token:
        print(f"ERROR: Twilio credentials not found. WhatsApp to {phone_number} failed.")
        return False

    # Twilio expects numbers in E.164 format: whatsapp:+1234567890
    if not phone_number.startswith("+") and not phone_number.startswith("whatsapp:+"):
        print(f"WARNING: Phone number {phone_number} does not start with '+'. This usually fails for international delivery.")

    to_number = f"whatsapp:{phone_number}" if not phone_number.startswith("whatsapp:") else phone_number

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    data = {
        "From": from_number,
        "To": to_number,
        "Body": message
    }

    try:
        response = requests.post(url, data=data, auth=(account_sid, auth_token))
        if response.status_code == 201:
            resp_data = response.json()
            sid = resp_data.get("sid")
            print(f"SUCCESS: WhatsApp message sent to {phone_number}. SID: {sid}")
            return True
        else:
            print(f"ERROR: Twilio API returned {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"EXCEPTION: Failed to send WhatsApp: {str(e)}")
        return False
