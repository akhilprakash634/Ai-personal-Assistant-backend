import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat_conversational(text, label):
    print(f"\nTesting {label}: '{text}'")
    url = f"{BASE_URL}/webhooks/slack"
    data = {"user_id": "U_CONV_TEST", "text": text}
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    # Create/Update user with ID 2 to have slack_user_id='U_CONV_TEST'
    import sqlite3
    conn = sqlite3.connect('sql_app.db')
    c = conn.cursor()
    c.execute("UPDATE users SET slack_user_id='U_CONV_TEST' WHERE id=2")
    # Clear activity logs for this user to test onboarding
    c.execute("DELETE FROM activity_logs WHERE user_id=2 AND action='Chat Command'")
    conn.commit()
    conn.close()

    print("--- Conversational Tests ---")
    
    test_chat_conversational("hi", "Greeting (New User)")
    test_chat_conversational("hello", "Greeting (Returning User)") # Should be returning now since 'hi' was logged
    test_chat_conversational("help", "Help Request")
    test_chat_conversational("who are you", "Intro Request")
    test_chat_conversational("something about tasks", "Ambiguous Task")
    test_chat_conversational("i spent money", "Ambiguous Expense")
    test_chat_conversational("asdfghjkl", "Unknown Input")
