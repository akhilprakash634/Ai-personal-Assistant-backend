import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .. import models

def parse_chat_command(text: str):
    """
    Parses a chat command and returns a structured intent.
    """
    original_text = text
    text = text.lower().strip()
    
    # 1. Navigation / Show Intent
    if any(keyword in text for keyword in ["show today", "today dues", "show dues today", "due today", "list today", "dues today", "what is due today"]):
        return {"intent": "show_dashboard", "filter": "today"}
    
    if any(keyword in text for keyword in ["show overdue", "list overdue", "overdue"]):
        return {"intent": "show_dashboard", "filter": "overdue"}
        
    if any(keyword in text for keyword in ["show upcoming", "upcoming dues", "upcoming"]):
        return {"intent": "show_dashboard", "filter": "upcoming"}

    if any(keyword in text for keyword in ["dashboard", "home", "show dashboard"]):
        return {"intent": "show_dashboard", "filter": "dashboard"}
    
    if text in ["settings", "go to settings", "open settings"]:
        return {"intent": "navigate", "page": "settings"}
    
    if text in ["tasks", "my tasks", "show tasks", "list tasks", "show all tasks"]:
        return {"intent": "navigate", "page": "tasks"}
        
    # 2. Mark Done
    mark_done_match = re.search(r"mark done (.+)", text)
    if mark_done_match or text.startswith("mark done"):
        return {"intent": "mark_done", "task_query": mark_done_match.group(1) if mark_done_match else None}
        
    # 3. Snooze
    snooze_match = re.search(r"snooze for (\d+) days?", text)
    if snooze_match:
        return {"intent": "snooze", "days": int(snooze_match.group(1))}
        
    # 4. Create Task Parsing (Robust Extraction)
    intent = "create_task"
    recurrence = models.RecurrenceType.NONE
    recurrence_interval = 1
    due_date = None
    priority = models.PriorityType.MEDIUM
    category = "General"
    
    # Working title that we will strip parts from
    temp_title = original_text
    
    # helper to clean title in-place
    def strip_from_title(pattern, flags=re.IGNORECASE):
        nonlocal temp_title
        temp_title = re.sub(pattern, "", temp_title, flags=flags)

    # 5. Extract Priority
    if re.search(r"\b(urgent|high priority|asap|immediate|critical)\b", text):
        priority = models.PriorityType.HIGH
        strip_from_title(r"\b(urgent|high priority|asap|immediate|critical)\b")
    elif re.search(r"\b(low priority|not urgent|whenever|low)\b", text):
        priority = models.PriorityType.LOW
        strip_from_title(r"\b(low priority|not urgent|whenever|low)\b")

    # 6. Extract Category
    categories = ["Work", "Personal", "Health", "Finance", "Shopping", "Renewal", "General"]
    cat_mapping = {
        "Renewal": ["renew", "ssl", "domain", "subscription", "expiry"],
        "Finance": ["pay", "bill", "invoice", "rent", "tax"],
        "Work": ["meeting", "call", "project", "audit", "report"],
        "Health": ["gym", "water", "doctor", "workout"],
        "Personal": ["mom", "dad", "family", "buy", "gift"],
        "Shopping": ["milk", "grocery", "order"]
    }

    cat_found = False
    # Explicit match: category X or [X]
    cat_match = re.search(r"category\s+(\w+)", text)
    if cat_match:
        val = cat_match.group(1).capitalize()
        if val in categories:
            category = val
            cat_found = True
            strip_from_title(r"category\s+" + re.escape(cat_match.group(1)))
    
    if not cat_found:
        for cat in categories:
            pattern = rf"(\[{cat}\]|{cat}:|{cat}\s+-)"
            if re.search(pattern, original_text, re.IGNORECASE):
                category = cat
                cat_found = True
                strip_from_title(pattern)
                break
    
    if not cat_found:
        # Keyword mapping
        for cat, keywords in cat_mapping.items():
            for kw in keywords:
                if re.search(rf"\b{kw}\b", text):
                    category = cat
                    cat_found = True
                    break
            if cat_found: break
    
    # 7. Extract Dates/Recurrence
    now = datetime.utcnow()
    
    # Recurrence patterns
    if "every month" in text:
        recurrence = models.RecurrenceType.MONTHLY
        strip_from_title(r"every month")
        day_match = re.search(r"on the (\d+)(st|nd|rd|th)?", text)
        if day_match:
            day = int(day_match.group(1))
            due_date = now.replace(day=day, hour=10, minute=0, second=0)
            if due_date < now: due_date += relativedelta(months=1)
            strip_from_title(r"on the \d+(st|nd|rd|th)?")
            
    elif "every year" in text:
        recurrence = models.RecurrenceType.YEARLY
        strip_from_title(r"every year")
        
    elif "every day" in text or "daily" in text:
        recurrence = models.RecurrenceType.DAILY
        strip_from_title(r"every day|daily")

    # Absolute Dates (e.g. March 26)
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
              "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    month_pattern = "|".join(months)
    abs_date_match = re.search(rf"\b({month_pattern})\s+(\d+)(st|nd|rd|th)?", text)
    if abs_date_match:
        month_str = abs_date_match.group(1)
        day = int(abs_date_match.group(2))
        
        # Month index (1-based)
        month_idx = -1
        for i, m in enumerate(months):
            if m == month_str:
                month_idx = (i % 12) + 1
                break
        
        if month_idx != -1:
            due_date = now.replace(month=month_idx, day=day, hour=10, minute=0, second=0)
            if due_date < now:
                due_date = due_date.replace(year=now.year + 1)
            strip_from_title(abs_date_match.group(0))

    # Relative Dates
    if not due_date:
        if "tomorrow" in text:
            due_date = now + timedelta(days=1)
            due_date = due_date.replace(hour=9, minute=0)
            strip_from_title(r"tomorrow")
        elif "today" in text:
            due_date = now + timedelta(hours=2)
            strip_from_title(r"today")
        elif "next week" in text:
            due_date = now + timedelta(weeks=1)
            strip_from_title(r"next week")
        
        delta_match = re.search(r"in (\d+) (minute|min|hour|hr|day)s?", text)
        if delta_match:
            val = int(delta_match.group(1))
            unit = delta_match.group(2)
            if "min" in unit: due_date = now + timedelta(minutes=val)
            elif "hr" in unit or "hour" in unit: due_date = now + timedelta(hours=val)
            elif "day" in unit: due_date = now + timedelta(days=val)
            strip_from_title(r"in \d+ (minute|min|hour|hr|day)s?")

    # 8. Clean Title Final
    strip_from_title(r"^(remind me to|remind me|add task|create task|task:)", flags=re.IGNORECASE)
    
    # Clean extra whitespace
    clean_title = re.sub(r"\s+", " ", temp_title).strip()
    if not clean_title or clean_title.lower() == "to":
        clean_title = "New Task"
    
    # Capitalize
    clean_title = clean_title[0].upper() + clean_title[1:] if clean_title else "New Task"

    return {
        "intent": intent,
        "data": {
            "title": clean_title[:100], 
            "due_date": due_date,
            "recurrence": recurrence,
            "recurrence_interval": recurrence_interval,
            "priority": priority,
            "category": category
        }
    }
