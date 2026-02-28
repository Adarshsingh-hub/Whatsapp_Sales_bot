import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TWILIO_ACCOUNT_SID = os.getenv(
        "TWILIO_ACCOUNT_SID"
    )
    TWILIO_AUTH_TOKEN = os.getenv(
        "TWILIO_AUTH_TOKEN"
    )
    TWILIO_WHATSAPP_NUMBER = os.getenv(
        "TWILIO_WHATSAPP_NUMBER"
    )
    OWNER_WHATSAPP = os.getenv(
    "OWNER_WHATSAPP"
    )
    # OpenAI + Storage
    OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
    )
    OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL"
    ,"gpt-4o-mini")
    EMBED_MODEL = os.getenv(
    "EMBED_MODEL"
    ,"text-embedding-3-small")
    DATABASE_URL = os.getenv(
    "DATABASE_URL"
    )
    CHROMA_PATH = os.getenv(
    "CHROMA_PATH"
    ,"./chroma_db")
    DATA_PATH = os.getenv(
    "DATA_PATH"
    ,"./data")
    TOP_K = int(os.getenv(
    "TOP_K"
    ,"5"))
    MAX_TOKENS = int(os.getenv(
    "MAX_TOKENS"
    ,"500"))
    SESSION_TIMEOUT = int(os.getenv(
    "SESSION_TIMEOUT_MINUTES"
    ,"30"))
    # SALES system prompt - persuasive, friendly, closes deals
    # Customise brand name + product focus per client
    SYSTEM_PROMPT = (
    "You are a friendly sales assistant for {brand_name}. "
    "Your goal is to help customers find the right product, "
    "answer their questions confidently, and guide them towards "
    "making a purchase decision. "
    "Use the product information provided in the context. "
    "Be warm, helpful, and gently persuasive — never pushy. "
    "If a customer is ready to buy, ask for their details and "
    "tell them someone will confirm their order shortly. "
    "If you cannot answer something, say so and offer to connect "
    "them with the team. Keep replies concise — max 3-4 sentences. "
    "This is WhatsApp, not email. Short responses only."
    )
config = Config()