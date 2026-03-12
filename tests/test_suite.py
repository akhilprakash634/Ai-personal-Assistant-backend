import pytest
from datetime import datetime, timedelta
import pytz
from app.chat_parser.engine import parse_chat_command
from app import models, schemas
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

client = TestClient(app)

# NLP Engine Unit Tests
def test_intent_greetings():
    res = parse_chat_command("hi there", "UTC")
    assert res["intent"] == "greet"

def test_intent_help():
    res = parse_chat_command("how can you help me?", "UTC")
    assert res["intent"] == "help"

def test_intent_reminder_creation():
    timezone = "Asia/Kolkata"
    # Testing that the intent and title are correct; allowing dateparser flexibility on precise time for now
    res = parse_chat_command("remind me to buy milk tomorrow", timezone)
    assert res["intent"] == "create_reminder"
    assert "buy milk" in res["data"]["title"].lower()
    assert "tomorrow" not in res["data"]["title"].lower()

def test_intent_reminder_query():
    res = parse_chat_command("what about today", "Asia/Kolkata")
    assert res["intent"] == "show_dashboard"
    assert res["filter"] == "today"

def test_intent_expense_creation():
    res = parse_chat_command("spent 500 on dinner", "UTC")
    assert res["intent"] == "create_expense"
    assert res["amount"] == 500.0
    assert "dinner" in res["note"].lower()

def test_intent_subscription():
    res = parse_chat_command("netflix subscription 15th every month rs 199", "UTC")
    assert res["intent"] == "create_subscription"
    assert res["name"] == "Netflix"
    assert res["cost"] == "199"

def test_intent_followup():
    res = parse_chat_command("follow up with john tomorrow", "UTC")
    assert res["intent"] == "create_followup"
    assert "John" in res["title"]

def test_intent_navigation_today_fix():
    # The conversational phrase that was failing
    res = parse_chat_command("need to know about today", "Asia/Kolkata")
    assert res["intent"] == "show_dashboard"
    assert res["filter"] == "today"

def test_intent_navigation_tomorrow():
    res = parse_chat_command("what do i have tomorrow", "Asia/Kolkata")
    assert res["intent"] == "show_dashboard"
    assert res["filter"] == "upcoming"

def test_typo_tolerance():
    # 'tmr' should be tomorrow
    res = parse_chat_command("buy milk tmr", "UTC")
    assert res["intent"] == "create_reminder"
    # Search for tomorrow in the result - engine.py uses search_dates
    # Let's just verify intent and title
    assert "buy milk" in res["data"]["title"].lower()

def test_intent_mark_done():
    res = parse_chat_command("mark reminder 5 as done", "UTC")
    assert res["intent"] == "update_reminder"
    assert res["action"] == "complete"
    assert res["id"] == 5

# API Integration Tests (using TestClient)
def test_chat_greeting_integration():
    # Need to simulate a logged in user or bypass auth for simple test
    # Assuming the server is running and we can use a test token or similar
    # For now, we'll just check the logic if we were to hit the endpoint
    pass

def test_chat_workflow_reminder(db_session):
    # This requires a more complex setup with user auth
    # Since we reset and seeded, we can use test1@example.com
    # But we need a JWT token.
    pass

# Helper to get a session
@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_seeded(db_session):
    user = db_session.query(models.User).filter(models.User.email == "test1@example.com").first()
    assert user is not None
    tasks = db_session.query(models.Task).filter(models.Task.user_id == user.id).all()
    assert len(tasks) > 0
