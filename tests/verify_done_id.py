import requests
import sqlite3

BASE_URL = "http://localhost:8000"

def setup_pending_tasks():
    print("Setting up pending tasks for testing...")
    conn = sqlite3.connect('sql_app.db')
    c = conn.cursor()
    # Ensure a user with slack_id 'U_DONE_TEST' exists
    c.execute("UPDATE users SET slack_user_id='U_DONE_TEST' WHERE id=2")
    # Add two overdue tasks
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    past = now - timedelta(days=2)
    c.execute("INSERT INTO tasks (title, due_date, user_id, is_completed, priority, category) VALUES (?, ?, ?, 0, 'MEDIUM', 'General')", ("Review reports", past, 2))
    c.execute("INSERT INTO tasks (title, due_date, user_id, is_completed, priority, category) VALUES (?, ?, ?, 0, 'MEDIUM', 'General')", ("Water plants", past, 2))
    conn.commit()
    conn.close()

def test_ambiguous_done():
    print("\nTesting Ambiguous 'done' command...")
    url = f"{BASE_URL}/webhooks/slack"
    data = {"user_id": "U_DONE_TEST", "text": "done"}
    response = requests.post(url, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response (should contain IDs): {response.text}")

if __name__ == "__main__":
    setup_pending_tasks()
    test_ambiguous_done()
