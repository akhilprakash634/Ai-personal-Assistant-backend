import os
import sys
from datetime import datetime, timedelta
# Add backend to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import User, Task, RecurrenceType
from app.auth import get_password_hash

def seed_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if we already seeded
    if db.query(User).count() > 0:
        print("Database already seeded.")
        return
        
    print("Seeding users...")
    user1 = User(email="test1@example.com", hashed_password=get_password_hash("password123"))
    user2 = User(email="test2@example.com", hashed_password=get_password_hash("password123"))
    
    db.add(user1)
    db.add(user2)
    db.commit()
    db.refresh(user1)
    db.refresh(user2)
    
    print("Seeding tasks for User 1...")
    now = datetime.utcnow()
    
    # User 1 Tasks
    # 1. Overdue Monthly Payment
    t1 = Task(
        title="Pay internet bill",
        category="Finance",
        due_date=now - timedelta(days=2),
        recurrence=RecurrenceType.MONTHLY,
        user_id=user1.id
    )
    # 2. Upcoming SSL Renewal
    t2 = Task(
        title="Renew generic SSL certificate",
        category="Work",
        due_date=now + timedelta(days=1),
        recurrence=RecurrenceType.YEARLY,
        user_id=user1.id
    )
    # 3. Today Health
    t3 = Task(
        title="Drink 2L water & 30 min exercise",
        category="Health",
        due_date=now.replace(hour=18, minute=0, second=0),
        recurrence=RecurrenceType.DAILY,
        user_id=user1.id
    )
    
    print("Seeding tasks for User 2...")
    # User 2 Tasks (Isolation Verification)
    t4 = Task(
        title="Renew domain name for startup",
        category="Work",
        due_date=now + timedelta(days=5),
        recurrence=RecurrenceType.YEARLY,
        user_id=user2.id
    )
    t5 = Task(
        title="Follow up with John on contract",
        category="Personal",
        due_date=now - timedelta(days=1), # Overdue
        recurrence=RecurrenceType.NONE,
        user_id=user2.id
    )
    
    db.add_all([t1, t2, t3, t4, t5])
    db.commit()
    print("Database seeded successfully!")
    print("\nCredentials:")
    print("User 1: test1@example.com / password123")
    print("User 2: test2@example.com / password123")

if __name__ == "__main__":
    seed_db()
