from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

class RecurrenceType(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class PriorityType(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class NotificationPlatform(str, enum.Enum):
    WEB = "web"
    SLACK = "slack"
    TEAMS = "teams"
    WHATSAPP = "whatsapp"
    SMS = "sms"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Notification Preferences
    notification_platform = Column(Enum(NotificationPlatform), default=NotificationPlatform.WEB)
    slack_webhook = Column(String, nullable=True)
    teams_webhook = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    
    # New Preferences
    timezone = Column(String, default="UTC")
    email_notifications_enabled = Column(Boolean, default=True)
    default_task_category = Column(String, default="General")
    
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="owner", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, default="General")
    priority = Column(Enum(PriorityType), default=PriorityType.MEDIUM)
    is_completed = Column(Boolean, default=False)
    
    # Timing
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Recurrence
    recurrence = Column(Enum(RecurrenceType), default=RecurrenceType.NONE)
    recurrence_interval = Column(Integer, default=1) # e.g. every 2 weeks
    
    # Owner
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="tasks")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    is_followup = Column(Boolean, default=False)
    is_ensure = Column(Boolean, default=False)
    
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    task = relationship("Task", back_populates="reminders")
    owner = relationship("User", back_populates="reminders")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False) # e.g. "created task", "completed task"
    description = Column(String, nullable=False) # e.g. "Completed 'Drink 2L Water'"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activities")
