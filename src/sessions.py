from datetime import datetime, timedelta
from src.config import config

# Store sessions in memory
sessions: dict = {}


def get_session(phone: str) -> dict:
    now = datetime.now()

    # Check if session exists
    if phone in sessions:
        last_active = sessions[phone]["last_active"]
        timeout = timedelta(minutes=config.SESSION_TIMEOUT)

        # If session expired → delete it
        if now - last_active > timeout:
            del sessions[phone]

    # If no session → create new one
    if phone not in sessions:
        sessions[phone] = {
            "phone": phone,
            "chat_history": [],          # list of {role, content}
            "lead_data": {},             # name, email, address etc
            "intent_history": [],        # tracked intents
            "is_qualified": False,       # has user shown buy intent?
            "needs_human": False,        # escalate to owner?
            "message_count": 0,
            "created_at": now,
            "last_active": now,
        }

    # Update activity + message count
    sessions[phone]["last_active"] = now
    sessions[phone]["message_count"] += 1

    return sessions[phone]


def update_session(phone: str, role: str, content: str):
    """Add a message to chat history."""
    session = get_session(phone)

    session["chat_history"].append({
        "role": role,
        "content": content
    })

    # Keep only last 20 messages to avoid token overflow
    if len(session["chat_history"]) > 20:
        session["chat_history"] = session["chat_history"][-20:]


def mark_qualified(phone: str, lead_data: dict):
    """Mark this contact as a qualified lead and store their data."""
    session = get_session(phone)
    session["is_qualified"] = True
    session["lead_data"].update(lead_data)


def mark_needs_human(phone: str):
    """Flag conversation for human takeover."""
    session = get_session(phone)
    session["needs_human"] = True