from rapidfuzz import process, utils
import re

SHORTHAND_MAP = {
    "tmr": "tomorrow",
    "tmrw": "tomorrow",
    "2moro": "tomorrow",
    "nxt wk": "next week",
    "evry": "every",
    "renw": "renew",
    "folow": "follow",
    "updt": "update",
    "del": "delete",
    "rem": "remind",
    "expns": "expense",
    "sub": "subscription"
}

def normalize_text(text: str) -> str:
    """
    Normalizes text by correcting common shorthand and typos.
    """
    text = text.lower().strip()
    
    # Replace common shorthand patterns
    for short, full in SHORTHAND_MAP.items():
        # Use word boundary to avoid partial replacements
        text = re.sub(rf"\b{re.escape(short)}\b", full, text)
    
    # Handle specific multi-word shorthands
    text = text.replace("nxt wk", "next week")
    
    return text

def fuzzy_match_intent(text: str, intents: list, threshold: int = 80):
    """
    Experimental: Fuzzy match against a list of intent keywords.
    """
    result = process.extractOne(text, intents, score_cutoff=threshold)
    return result[0] if result else None
