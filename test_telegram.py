import os
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.notifications.telegram import send_telegram_notification

load_dotenv()

def test_send():
    print("Ensure you have TELEGRAM_BOT_TOKEN set in your .env file.")
    chat_id = input("Enter your Telegram Chat ID: ")
    message = "🚀 ANTIGRAVITY: This is a manual test of your Telegram notification system. It works!"
    
    print(f"Attempting to send to {chat_id}...")
    success = send_telegram_notification(chat_id, message)
    
    if success:
        print("\n✅ SUCCESS! Check your Telegram app.")
    else:
        print("\n❌ FAILED. Check the errors above.")

if __name__ == "__main__":
    test_send()
