from fastapi import FastAPI, Form, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from src.config import config
from src.bot import process_message
from src.sessions import get_session
from src.leads import create_leads_table, save_lead
import logging

app = FastAPI(title="Digimind WhatsApp Sales Bot")

client = Client(
    config.TWILIO_ACCOUNT_SID,
    config.TWILIO_AUTH_TOKEN
)

logger = logging.getLogger(__name__)


# =========================
# STARTUP
# =========================

@app.on_event("startup")
async def startup():
    create_leads_table()
    logger.info("WhatsApp bot ready")


# =========================
# WHATSAPP WEBHOOK
# =========================

@app.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),   # e.g. whatsapp:+919876543210
    Body: str = Form(...)    # message text
):
    phone = From
    message = Body.strip()

    logger.info(f"Incoming from {phone}: {message[:50]}")

    # Process message via AI bot
    result = process_message(phone, message)

    # Get updated session
    session = get_session(phone)

    # Save lead if qualified OR human needed
    if result["is_qualified"] or result["needs_human"]:
        save_lead(phone, session, is_hot=result["needs_human"])

    # Notify owner if escalation needed
    if result["needs_human"]:
        notify_owner(phone, message, session)

    # Send reply back to user via Twilio
    resp = MessagingResponse()
    resp.message(result["reply"])

    return Response(
        content=str(resp),
        media_type="application/xml"
    )


# =========================
# OWNER ALERT SYSTEM
# =========================

def notify_owner(phone: str, message: str, session: dict):
    """Send WhatsApp alert to business owner when customer needs human."""
    try:
        alert = (
            f"HOT LEAD ALERT!\n"
            f"Customer: {phone}\n"
            f"Message: {message}\n"
            f"Conversation count: {session['message_count']}\n"
            f"Reply now to close the deal!"
        )

        client.messages.create(
            from_=config.TWILIO_WHATSAPP_NUMBER,
            to=config.OWNER_WHATSAPP,
            body=alert
        )

    except Exception as e:
        logger.error(f"Failed to notify owner: {e}")


# =========================
# LOCAL RUN (DEV MODE)
# =========================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )