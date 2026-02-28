from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import config
from src.sessions import get_session, update_session, mark_qualified, mark_needs_human
import json
import logging
import os

logger = logging.getLogger(__name__)

# =========================
# INITIALISE MODELS (once)
# =========================

embeddings = OpenAIEmbeddings(
    model=config.EMBED_MODEL,
    api_key=os.getenv("OPENAI_API_KEY")
)

vectorstore = Chroma(
    persist_directory=config.CHROMA_PATH,
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": config.TOP_K}
)

llm = ChatOpenAI(
    model_name=config.OPENAI_MODEL,
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.3,
    max_tokens=config.MAX_TOKENS
)

# =========================
# INTENT CLASSIFICATION
# =========================

def classify_intent(message: str) -> str:
    """Quickly classify the customer's intent before generating a reply."""

    prompt = f"""
Classify this WhatsApp message intent into ONE category:
- product_enquiry: asking about products or services
- price_question: asking about price or cost
- buy_intent: wants to order, buy, or book
- complaint: unhappy, issue, problem
- human_request: explicitly wants to talk to a person
- greeting: just saying hi or hello
- other: anything else

Message: {message}

Reply with ONLY the category name, nothing else.
"""

    resp = llm.invoke([HumanMessage(content=prompt)])
    return resp.content.strip().lower()


# =========================
# CONTEXT RETRIEVAL (RAG)
# =========================

def retrieve_context(query: str) -> str:
    """Retrieve relevant product/FAQ chunks for the query."""
    docs = retriever.get_relevant_documents(query)
    return "\n\n".join(d.page_content for d in docs)


# =========================
# BUILD CHAT HISTORY
# =========================

def build_messages(session: dict, user_message: str, context: str) -> list:
    """Build full message list including system prompt + history."""

    system_content = config.SYSTEM_PROMPT.format(
        brand_name=session.get("brand_name", "our brand")
    ) + f"\n\nProduct context:\n{context}"

    messages = [SystemMessage(content=system_content)]

    # Add last 10 messages
    for msg in session["chat_history"][-10:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    # Add current user message
    messages.append(HumanMessage(content=user_message))

    return messages


# =========================
# MAIN PROCESS FUNCTION
# =========================

def process_message(phone: str, user_message: str) -> dict:
    """
    Main entry point.
    Input: phone + message
    Output: dict with reply, intent, needs_human, is_qualified
    """

    session = get_session(phone)

    try:
        # 1. CLASSIFY INTENT
        intent = classify_intent(user_message)
        session["intent_history"].append(intent)

        # 2. HUMAN ESCALATION
        if intent == "human_request":
            mark_needs_human(phone)

            update_session(phone, "user", user_message)

            reply = (
                "Sure! Let me connect you with our team right away. "
                "Someone will reach out to you within 30 minutes."
            )

            update_session(phone, "assistant", reply)

            return {
                "reply": reply,
                "intent": intent,
                "needs_human": True,
                "is_qualified": False
            }

        # 3. RETRIEVE CONTEXT (RAG)
        context = retrieve_context(user_message)

        # 4. BUILD MESSAGE STACK
        messages = build_messages(session, user_message, context)

        # 5. GENERATE LLM RESPONSE
        response = llm.invoke(messages)
        reply = response.content.strip()

        # 6. QUALIFY LEAD
        if intent in ["buy_intent", "price_question"]:
            mark_qualified(phone, {"last_intent": intent})

        # 7. STORE HISTORY
        update_session(phone, "user", user_message)
        update_session(phone, "assistant", reply)

        return {
            "reply": reply,
            "intent": intent,
            "needs_human": False,
            "is_qualified": session["is_qualified"]
        }

    except Exception as e:
        logger.error(f"Error processing message from {phone}: {e}")

        return {
            "reply": "Sorry, something went wrong. Please try again!",
            "intent": "error",
            "needs_human": False,
            "is_qualified": False
        }