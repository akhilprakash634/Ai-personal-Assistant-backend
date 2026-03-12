import requests
import json

BASE_URL = "http://localhost:8000"

def test_twilio_webhook():
    print("Testing Twilio Webhook (WhatsApp/SMS)...")
    url = f"{BASE_URL}/webhooks/twilio"
    data = {
        "From": "+1234567890",
        "Body": "Remind me to buy milk tomorrow at 10am"
    }
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def test_slack_webhook():
    print("\nTesting Slack Webhook (Slash Command)...")
    url = f"{BASE_URL}/webhooks/slack"
    data = {
        "user_id": "U123456",
        "text": "Spent 500 on dinner"
    }
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def test_slack_webhook_list():
    print("\nTesting Slack Webhook (List Tasks)...")
    url = f"{BASE_URL}/webhooks/slack"
    data = {"user_id": "U123456", "text": "list tasks"}
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def test_slack_webhook_snooze():
    print("\nTesting Slack Webhook (Snooze by ID)...")
    url = f"{BASE_URL}/webhooks/slack"
    data = {"user_id": "U123456", "text": "snooze 4 for 3 days"}
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def test_slack_webhook_mark_done():
    print("\nTesting Slack Webhook (Mark Done by ID)...")
    url = f"{BASE_URL}/webhooks/slack"
    data = {"user_id": "U123456", "text": "done 4"}
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

def test_slack_webhook_delete():
    print("\nTesting Slack Webhook (Delete by ID)...")
    url = f"{BASE_URL}/webhooks/slack"
    data = {"user_id": "U123456", "text": "delete 5"}
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    print("Verification script ready.")
    test_slack_webhook_list()
    test_slack_webhook_snooze()
    test_slack_webhook_mark_done()
    test_slack_webhook_delete()
