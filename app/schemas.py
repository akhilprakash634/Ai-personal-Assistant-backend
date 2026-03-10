from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from .models import RecurrenceType, PriorityType, NotificationPlatform

class UserBase(BaseModel):
    email: EmailStr
    notification_platform: Optional[NotificationPlatform] = NotificationPlatform.WEB
    slack_webhook: Optional[str] = None
    teams_webhook: Optional[str] = None
    whatsapp_number: Optional[str] = None
    timezone: Optional[str] = "UTC"
    email_notifications_enabled: Optional[bool] = True
    default_task_category: Optional[str] = "General"

class UserUpdate(BaseModel):
    notification_platform: Optional[NotificationPlatform] = None
    slack_webhook: Optional[str] = None
    teams_webhook: Optional[str] = None
    whatsapp_number: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None
    default_task_category: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class GoogleLoginRequest(BaseModel):
    id_token: str

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = "General"
    priority: Optional[PriorityType] = PriorityType.MEDIUM
    due_date: Optional[datetime] = None
    recurrence: Optional[RecurrenceType] = RecurrenceType.NONE
    recurrence_interval: Optional[int] = 1

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[PriorityType] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    recurrence: Optional[RecurrenceType] = None
    recurrence_interval: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    is_completed: bool
    created_at: datetime
    user_id: int
    class Config:
        from_attributes = True

class ReminderResponse(BaseModel):
    id: int
    message: str
    scheduled_for: datetime
    is_sent: bool
    is_followup: bool
    is_ensure: bool
    task_id: int
    user_id: int
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    reply: str
    data: Optional[dict] = None

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    description: str
    timestamp: datetime
    class Config:
        from_attributes = True
