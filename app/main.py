from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()
from .database import engine, Base
from .routers import auth, tasks, chat, dashboard, settings, expenses, subscriptions, notifications, webhooks
from .scheduler.engine import start_scheduler, stop_scheduler
from .telegram_bot import start_telegram_polling

# Create tables if they don't exist (in a real app, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Reminder Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    start_scheduler()
    start_telegram_polling()

@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(tasks.router)
app.include_router(chat.router)
app.include_router(settings.router)
app.include_router(expenses.router)
app.include_router(subscriptions.router)
app.include_router(notifications.router)
app.include_router(webhooks.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Reminder Assistant API!"}
