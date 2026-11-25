"""Deterministic booking-intent extractor for Gemini chat integration."""

import asyncio
from datetime import datetime, timezone
import json
from typing import Literal
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError
from app.core.config import Settings, validate_gemini_config
from app.models.lead import Lead
from app.schemas.chat_schema import ChatHistoryItem


class BookingIntentResult(BaseModel):
    """Structured booking intent extracted from the customer conversation."""

    wants_booking: bool = False
    confirm_booking: bool = False
    cancel_booking: bool = False
    appointment_type: Literal["CALL", "ONLINE_MEETING", "DEMO"] | None = None
    preferred_date: str | None = None  # YYYY-MM-DD
    preferred_time: str | None = None  # HH:MM (24h)
    timezone: str | None = None  # IANA timezone if explicitly stated


BOOKING_INTENT_INSTRUCTION = """You extract appointment scheduling intent from a customer sales conversation.
Today's UTC date is {today_utc}.

Rules:
- Set wants_booking=true if the customer is asking to schedule a demo, call, or meeting, or is answering a scheduling question (date, time, timezone, confirmation).
- Set confirm_booking=true ONLY if the customer explicitly confirms booking a specific proposed slot (e.g. "yes", "confirm", "book it", "sounds good, please book").
- Set cancel_booking=true if the customer asks to stop or cancel booking.
- Resolve relative dates like "tomorrow" or "today" to YYYY-MM-DD using Today's UTC date.
- Convert times like "3 PM" or "14:30" to 24-hour HH:MM format.
- Set timezone ONLY if the customer explicitly mentions a timezone or city/region (e.g. "IST" -> "Asia/Kolkata", "EST" -> "America/New_York", "UTC" -> "UTC"). NEVER guess or assume a timezone if not mentioned.
- Return ONLY valid JSON."""


async def extract_booking_intent(
    message: str,
    history: list[ChatHistoryItem],
    lead: Lead | None,
    settings: Settings | None = None,
) -> BookingIntentResult:
    """Extract structured appointment intent non-blockingly."""
    cfg = validate_gemini_config(settings)
    client = genai.Client(api_key=cfg.gemini_api_key)

    recent = history[-6:]
    hist_text = "\n".join(f"{t.role.upper()}: {t.content}" for t in recent) if recent else "None"
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    prompt = (
        f"Known customer: name={lead.customer_name if lead else None}, "
        f"email={lead.email if lead else None}, phone={lead.phone if lead else None}\n\n"
        f"Recent Conversation:\n{hist_text}\n\n"
        f"Latest Customer Message:\n{message.strip()}"
    )

    config = types.GenerateContentConfig(
        system_instruction=BOOKING_INTENT_INSTRUCTION.format(today_utc=today_str),
        temperature=0.1,
        max_output_tokens=250,
        response_mime_type="application/json",
        response_schema=BookingIntentResult,
    )

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=cfg.gemini_model,
                contents=prompt,
                config=config,
            ),
            timeout=min(cfg.gemini_timeout_seconds, 10.0),
        )
        raw = (getattr(response, "text", None) or "").strip()
        if not raw:
            return BookingIntentResult()
        return BookingIntentResult.model_validate(json.loads(raw))
    except (asyncio.TimeoutError, json.JSONDecodeError, ValidationError, Exception):
        return BookingIntentResult()
