import re
from datetime import datetime, timedelta
import pytz
import dateparser
from dateparser.search import search_dates
from dateutil.relativedelta import relativedelta
from app import models
from app.chat_parser.nlp_utils import normalize_text

def parse_chat_command(text: str, timezone_str: str = "UTC"):
    """
    Parses a chat command and returns a structured intent, respecting the user's timezone.
    """
    original_text = text
    # Step 1: Normalize text (typo correction and shorthand expansion)
    text = normalize_text(text)
    
    try:
        user_tz = pytz.timezone(timezone_str)
    except Exception:
        user_tz = pytz.UTC
        
    now_local = datetime.now(user_tz)
    
    # 0. Greetings & Help
    if re.search(r"\b(hi|hello|hey|hola|greetings|good morning|good evening)\b", text):
        if text.strip() in ["hi", "hello", "hey"]:
            return {"intent": "greet", "is_simple": True}
        return {"intent": "greet", "is_simple": False}

    if any(kw in text for kw in ["help", "what can you do", "get started", "how to build", "how to use", "commands", "guide"]):
        return {"intent": "help"}

    if any(kw in text for kw in ["who are you", "what are you", "your name", "introduce yourself"]):
        return {"intent": "who_are_you"}

    # 1. Navigation / Query
    query_today_patterns = [
        "today", "today's update", "today's plan", "today's schedule", 
        "know about today", "tell me about today", "what's today", 
        "how's today", "anything today", "status today", "whats up today",
        "due today", "list today", "show today"
    ]
    if any(p in text for p in query_today_patterns):
        # Additional check to ensure it's not a creation command (e.g., "remind me to... today")
        if not any(kw in text for kw in ["remind", "add", "create", "buy", "call", "send"]):
            return {"intent": "show_dashboard", "filter": "today"}
    
    if any(keyword in text for keyword in ["show overdue", "list overdue", "overdue"]):
        return {"intent": "show_dashboard", "filter": "overdue"}
        
    if any(keyword in text for keyword in ["show upcoming", "upcoming dues", "upcoming", "tomorrow plan", "what do i have tomorrow"]):
        return {"intent": "show_dashboard", "filter": "upcoming"}
    
    if text in ["tasks", "my tasks", "show tasks", "list tasks", "show all tasks", "pending tasks", "reminders", "my reminders", "show reminders"]:
        return {"intent": "query_reminders"}

    if any(kw in text for kw in ["show expense", "how much did i spend", "expense summary", "spending"]):
        return {"intent": "query_expenses"}

    # Mark Done
    # Support: "mark 5 as done", "done reminder 5", "complete #5"
    id_match = re.search(r"(?:mark\s+)?(?:#|task\s+|reminder\s+)?(\d+)\s+(?:as\s+)?(?:done|complete|finished)", text) or \
               re.search(r"(?:mark\s+)?(?:done|complete|finished)\s+(?:#|task\s+|reminder\s+)?(\d+)", text)
    if id_match:
        # If the first regex matched, the ID is in group 1. If the second, also in group 1 of its match.
        val = id_match.group(1)
        return {"intent": "update_reminder", "action": "complete", "id": int(val)}
        
    if any(text.startswith(kw) for kw in ["completed", "finished", "done", "mark as done"]):
        query = re.sub(r"^(completed|finished|done|mark as done|mark done)\s*", "", text).strip()
        return {"intent": "update_reminder", "action": "complete", "query": query if query else None}

    # Delete
    del_match = re.search(r"(?:delete|remove|cancel)\s+(?:#|task\s+)?(\d+)", text)
    if del_match:
        return {"intent": "delete_reminder", "id": int(del_match.group(1))}
    
    if any(text.startswith(kw) for kw in ["delete", "remove", "cancel"]):
        query = re.sub(r"^(delete|remove|cancel)\s+", "", text).strip()
        return {"intent": "delete_reminder", "query": query}

    # 3. Subscription / Renewal
    if any(kw in text for kw in ["renewal", "subscription", "renew"]):
        # "netflix renewal 5th every month"
        dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': now_local})
        name_match = re.search(r"\b(\w+)\s+(?:renewal|subscription|renew)\b", text)
        name = name_match.group(1).capitalize() if name_match else "Service"
        
        recurrence = models.RecurrenceType.MONTHLY if "every month" in text or "monthly" in text else \
                     models.RecurrenceType.YEARLY if "every year" in text or "yearly" in text else models.RecurrenceType.NONE
        
        return {
            "intent": "create_subscription",
            "name": name,
            "renewal_date": dt if dt else None,
            "recurrence": recurrence,
            "cost": amount_match.group(1) if (amount_match := re.search(r"(?:₹|rs\.?\s*)(\d+(?:\.\d{1,2})?)", text)) else None
        }

    # 4. Expense Logging
    # "spent 350 on lunch", "coffee 200", "paid electricity 900"
    amount_match = re.search(r"(?:₹|rs\.?|)?(\d+(?:\.\d{1,2})?)", text)
    # Use word boundaries for keywords to avoid accidental matches (e.g. "on" in "done")
    expense_keywords = [r"\bspent\b", r"\bpaid\b", r"\bcost\b", r"\bfor\b", r"\bon\b", r"\bbuy\b"]
    is_remind = any(kw in text for kw in ["remind", "reminder", "task"])
    if amount_match and any(re.search(kw, text) for kw in expense_keywords) and not is_remind:
        amount = float(amount_match.group(1))
        # Remove original amount from text to find category/note
        clean_text = text.replace(amount_match.group(0), "").strip()
        clean_text = re.sub(r"\b(spent|paid|on|for|buy)\b", "", clean_text).strip()
        
        # Try to find a date in the remaining text
        dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'past', 'RELATIVE_BASE': now_local})
        
        return {
            "intent": "create_expense",
            "amount": amount,
            "category": clean_text.split()[0].capitalize() if clean_text else "Misc",
            "note": clean_text.capitalize(),
            "date": dt if dt else now_local
        }

    # 5. Follow-ups
    if "follow up" in text:
        name_match = re.search(r"follow\s*up\s+(?:with\s+)?(\w+)", text)
        name = name_match.group(1).capitalize() if name_match else "someone"
        dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': now_local})
        
        return {
            "intent": "create_followup",
            "title": f"Follow up with {name}",
            "due_date": dt if dt else (now_local + timedelta(days=1))
        }

    # 6. Create Reminder (Default)
    # Strip action keywords FIRST to avoid dateparser misinterpreting words like "me"
    temp_title = re.sub(r"^(remind me to|remind me|add|create|task|reminder|need to|know about|tell me about|check|see|show me)\s*", "", text).strip()
    
    # Try precise parse first (better for specific times like 10am)
    dt = dateparser.parse(temp_title, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': now_local.replace(tzinfo=None)})
    date_phrase = ""
    
    if dt:
        # If we got a precise date, we need to find what phrase it matched to clean the title
        # This is tricky with .parse(), so we use search_dates to find the phrase if possible
        date_results = search_dates(temp_title, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': now_local.replace(tzinfo=None)})
        if date_results:
            # Find the date_phrase that matches the parsed dt as closely as possible
            # search_dates returns (phrase, datetime_object)
            # We iterate to find the phrase that corresponds to our precisely parsed dt
            for phrase, parsed_dt_from_search in date_results:
                # Compare year, month, day, hour, minute to see if it's the same date
                if dt.year == parsed_dt_from_search.year and \
                   dt.month == parsed_dt_from_search.month and \
                   dt.day == parsed_dt_from_search.day and \
                   dt.hour == parsed_dt_from_search.hour and \
                   dt.minute == parsed_dt_from_search.minute:
                    date_phrase = phrase
                    break
        # Ensure dt has timezone if it's naive
        if dt.tzinfo is None:
            dt = user_tz.localize(dt)
    else:
        # Fallback to search_dates
        date_results = search_dates(temp_title, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': now_local.replace(tzinfo=None)})
        if date_results:
            date_phrase, dt = date_results[0]
        # Ensure dt has timezone if it's naive
        if dt and dt.tzinfo is None: # Added 'dt and' check here
            dt = user_tz.localize(dt)

    if date_phrase:
        # Remove the exact date phrase found
        temp_title = temp_title.replace(date_phrase, "").strip()
    
    # Still strip common time keywords just in case
    time_keywords = ["tomorrow", "tmr", "today", "next", "in", "at", "am", "pm", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "morning", "afternoon", "evening", "night"]
    for kw in time_keywords:
        temp_title = re.sub(rf"\b{kw}\b", "", temp_title).strip()
    
    # Strip numbers if it looks like a time/date
    temp_title = re.sub(r"\b\d+(?:am|pm|st|nd|rd|th)?\b", "", temp_title).strip()
    temp_title = re.sub(r"\b(at|on|for|by)\b", "", temp_title).strip()
    temp_title = re.sub(r"\s+", " ", temp_title).strip()
    
    # Common fragments that are likely not titles
    query_fragments = ["to", "for", "at", "about", "todo", "to do", "know about", "knowing about", "tell me about", "what's", "whats", "the"]
    if not temp_title or temp_title in query_fragments:
        # If we have a date or time keywords, it might be a query
        if "today" in text or "today" in normalize_text(original_text): 
            return {"intent": "show_dashboard", "filter": "today"}
        if "tomorrow" in text or "tmr" in text: 
            return {"intent": "show_dashboard", "filter": "upcoming"}
        if dt: return {"intent": "clarify", "missing": "title", "date": dt}
        return {"intent": "none"}

    # If we have a title but no date, it's a clarify case or a reminder for "today"
    if not dt:
        # If it's short, ask for a date
        if len(temp_title.split()) < 3:
            return {"intent": "clarify", "missing": "date", "title": temp_title}
        # Otherwise default to today/asap
        dt = now_local

    return {
        "intent": "create_reminder",
        "data": {
            "title": temp_title.capitalize(),
            "due_date": dt,
            "priority": models.PriorityType.MEDIUM,
            "category": "General",
            "recurrence": models.RecurrenceType.MONTHLY if "every month" in text else models.RecurrenceType.NONE,
            "recurrence_interval": 1
        }
    }
