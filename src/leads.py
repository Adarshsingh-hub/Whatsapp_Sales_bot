import psycopg2
import logging
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)


# =========================
# DB CONNECTION
# =========================

def get_connection():
    return psycopg2.connect(config.DATABASE_URL)


# =========================
# CREATE TABLE (RUN ONCE)
# =========================

def create_leads_table():
    """Run once at startup to create the leads table."""
    sql = """
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        phone VARCHAR(20) UNIQUE NOT NULL,
        name VARCHAR(100),
        intent VARCHAR(50),
        message_count INT DEFAULT 0,
        is_hot BOOLEAN DEFAULT FALSE,
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


# =========================
# UPSERT LEAD
# =========================

def save_lead(phone: str, session: dict, is_hot: bool = False):
    """
    Insert or update lead.
    If phone already exists → update data.
    """

    lead_data = session.get("lead_data", {})

    latest_intent = (
        session["intent_history"][-1]
        if session.get("intent_history")
        else None
    )

    sql = """
    INSERT INTO leads (phone, name, intent, message_count, is_hot, notes, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (phone) DO UPDATE SET
        name = EXCLUDED.name,
        intent = EXCLUDED.intent,
        message_count = EXCLUDED.message_count,
        is_hot = EXCLUDED.is_hot,
        notes = EXCLUDED.notes,
        updated_at = NOW()
    """

    values = (
        phone,
        lead_data.get("name"),
        latest_intent,
        session.get("message_count", 0),
        is_hot,
        str(lead_data)
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)
        conn.commit()

    logger.info(f"Lead saved: {phone} | hot={is_hot}")