"""AI Sales Agent persona, lead-aware & RAG-grounded system instructions, and prompt builder."""

from typing import Any
from google.genai import types
from app.models.lead import Lead
from app.schemas.chat_schema import ChatHistoryItem
from app.schemas.sentiment_schema import SentimentAnalysisResult

SALES_AGENT_SYSTEM_INSTRUCTION = """You are a professional, consultative AI Sales Representative for FORTIVEX AI PRIVATE LIMITED.

Your responsibilities:
- Welcome customers warmly and professionally.
- Support both English and Hindi naturally, matching the customer's language.
- Answer product, pricing, FAQ, and policy questions strictly using the Retrieved Company Knowledge Context provided below.
- If the customer asks a question about company facts, products, pricing, or policies that is NOT covered by the Retrieved Company Knowledge Context, clearly state that this specific information is not available in the current company documents rather than guessing or inventing an answer.
- Naturally collect these lead qualification details over the course of the conversation:
  1. Customer name
  2. Company name
  3. Email address
  4. Phone number
  5. Business type
  6. Business requirements
  7. Expected budget
  8. Purchase timeline
  9. Interest level

Strict conversation rules:
- NEVER ask for all details in one message. Ask at most ONE relevant follow-up question at a time.
- NEVER ask for information the customer has already provided (check the Saved Customer Profile below).
- Remember and reference previously collected customer information when answering follow-up questions.
- If the customer declines to share a detail (e.g., email or phone), accept politely and move on without pressuring them.
- Offer a live product demonstration when appropriate and ask for their preferred date, time, and time zone.
- Never invent customer details, unsupported claims, or unverified company facts.
- Keep responses concise, natural, and easy to listen to via text-to-speech (2 to 4 sentences).
"""


def format_lead_context(lead: Lead | None) -> str:
    """Format currently known lead fields so Gemini never re-asks or forgets them."""
    if not lead:
        return "Saved Customer Profile: None yet."

    fields = [
        ("Customer name", lead.customer_name),
        ("Company name", lead.company_name),
        ("Email", lead.email),
        ("Phone", lead.phone),
        ("Business type", lead.business_type),
        ("Business requirements", lead.requirements),
        ("Expected budget", lead.budget),
        ("Purchase timeline", lead.purchase_timeline),
        ("Interest level", lead.interest_level),
        ("Current qualification status", lead.qualification_status),
    ]
    known = [f"- {label}: {val}" for label, val in fields if val]
    missing = [label for label, val in fields[:-1] if not val]

    known_block = "\n".join(known) if known else "- No details collected yet."
    missing_block = ", ".join(missing) if missing else "All key details collected."

    return (
        f"Saved Customer Profile (use this context; do not re-ask known fields):\n"
        f"{known_block}\n"
        f"Still unknown: {missing_block}"
    )


def format_retrieved_knowledge(rag_chunks: list[dict[str, Any]] | None) -> str:
    """Format retrieved ChromaDB chunks for grounded Gemini responses."""
    if not rag_chunks:
        return (
            "Retrieved Company Knowledge Context:\n"
            "- No matching company knowledge documents were retrieved for this message."
        )

    lines = [
        "Retrieved Company Knowledge Context (use ONLY these facts for company/product/pricing/policy answers; note that these are research-draft documents and any unknowns must not be invented):"
    ]
    for idx, chunk in enumerate(rag_chunks, start=1):
        doc_name = chunk.get("source_filename") or chunk.get("document_name", "unknown")
        doc_type = chunk.get("document_type", "unknown")
        content = chunk.get("content", "").strip()
        lines.append(f"[{idx}] Source: {doc_name} (type: {doc_type})\n{content}")
    return "\n\n".join(lines)


def format_sentiment_guidance(sentiment: SentimentAnalysisResult | None) -> str:
    """Provide tone-adaptation instructions based on detected customer sentiment."""
    if not sentiment:
        return "Customer Sentiment Adaptation:\n- Maintain a polite, clear, and helpful tone."

    tone_rules = {
        "POSITIVE": "Maintain a friendly, warm, and engaging tone; continue the sales conversation naturally.",
        "NEUTRAL": "Provide clear, professional, and informative answers without unnecessary fluff.",
        "FRUSTRATED": (
            "Acknowledge the customer's frustration sincerely, apologize where appropriate, "
            "do NOT repeat earlier questions, and offer a direct solution or human representative assistance."
        ),
        "NEGATIVE": (
            "Respect the customer's decision completely. Do NOT pressure them or continue aggressive selling. "
            "Offer a polite closing or optional escalation if appropriate."
        ),
    }
    rule = tone_rules.get(sentiment.sentiment, tone_rules["NEUTRAL"])
    strategy = sentiment.recommended_strategy or rule
    return (
        f"Customer Sentiment Adaptation:\n"
        f"- Detected Sentiment: {sentiment.sentiment} (confidence: {sentiment.confidence})\n"
        f"- Tone Rule: {rule}\n"
        f"- Recommended Strategy: {strategy}"
    )


def format_booking_context(booking_context: str | None) -> str:
    """Provide deterministic backend slot/booking state so Gemini never invents slots or IDs."""
    if not booking_context:
        return (
            "Appointment Booking Context:\n"
            "- No active booking action in this turn. Never invent available slots or booking references."
        )
    return f"Appointment Booking Context (use ONLY these verified backend facts):\n{booking_context}"


def build_lead_aware_system_instruction(
    lead: Lead | None,
    rag_chunks: list[dict[str, Any]] | None = None,
    sentiment: SentimentAnalysisResult | None = None,
    booking_context: str | None = None,
) -> str:
    """Combine base sales persona, lead profile, RAG context, sentiment, and booking state."""
    return (
        f"{SALES_AGENT_SYSTEM_INSTRUCTION}\n\n"
        f"{format_lead_context(lead)}\n\n"
        f"{format_sentiment_guidance(sentiment)}\n\n"
        f"{format_booking_context(booking_context)}\n\n"
        f"{format_retrieved_knowledge(rag_chunks)}"
    )


def build_gemini_contents(
    history: list[ChatHistoryItem],
    latest_message: str,
    max_turns: int = 20,
) -> list[types.Content]:
    """Convert recent conversation history and the latest user message into Gemini Content objects."""
    trimmed_history = history[-max_turns:] if max_turns > 0 else list(history)

    if (
        trimmed_history
        and trimmed_history[-1].role == "user"
        and trimmed_history[-1].content.strip() == latest_message.strip()
    ):
        trimmed_history = trimmed_history[:-1]

    contents: list[types.Content] = []
    for item in trimmed_history:
        gemini_role = "model" if item.role == "assistant" else "user"
        contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=item.content)],
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=latest_message.strip())],
        )
    )
    return contents
