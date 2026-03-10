import os
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.notifications.whatsapp import send_whatsapp_notification

load_dotenv()

def test_send():
    phone = input("Enter your phone number (with + and country code, e.g. +917902819158): ")
    message = "🚀 ANTIGRAVITY: This is a manual test of your WhatsApp notification system. It works!"
    
    print(f"Attempting to send to {phone}...")
    success = send_whatsapp_notification(phone, message)
    
    if success:
        print("\n✅ SUCCESS! Check your WhatsApp.")
    else:
        print("\n❌ FAILED. Check the errors above.")

if __name__ == "__main__":
    test_send()
