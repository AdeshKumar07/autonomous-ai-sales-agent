"""API routes for the Autonomous AI Sales Voice Agent, RAG, sentiment, booking, and memory."""

from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.database.db import get_db
from app.models.lead import Lead
from app.rag.retriever import search_knowledge
from app.schemas.appointment_schema import AppointmentCreateRequest, AppointmentPublicSchema
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.schemas.lead_schema import (
    ConversationMessageSchema,
    LeadSchema,
    SessionDetailResponse,
)
from app.services.appointment_intent_service import extract_booking_intent
from app.services.appointment_service import create_appointment, get_available_slots
from app.services.crm_service import log_crm_activity
from app.services.gemini_service import (
    GeminiConfigError,
    GeminiEmptyResponseError,
    GeminiModelError,
    GeminiRateLimitError,
    GeminiService,
    GeminiServiceError,
    GeminiTimeoutError,
)
from app.services.lead_service import (
    apply_lead_updates,
    get_or_create_lead,
    get_session_history,
    get_session_messages,
    save_conversation_turn,
)
from app.services.sentiment_service import SentimentService, compute_sentiment_summary

router = APIRouter(prefix="/api/agent", tags=["Agent"])

RAG_MIN_SIMILARITY = 0.35


@lru_cache(maxsize=1)
def get_gemini_service() -> GeminiService:
    """Lazily initialize and cache the GeminiService instance."""
    return GeminiService()


@lru_cache(maxsize=1)
def get_sentiment_service() -> SentimentService:
    """Lazily initialize and cache the SentimentService instance."""
    return SentimentService()


async def _process_booking_intent(
    db: Session,
    lead: Lead,
    message: str,
    history: list,
) -> tuple[str | None, AppointmentPublicSchema | None]:
    """Deterministically check slots or execute booking before Gemini replies."""
    intent = await extract_booking_intent(message=message, history=history, lead=lead)
    if not intent.wants_booking or intent.cancel_booking:
        return None, None

    settings = get_settings()
    appt_type = intent.appointment_type or "DEMO"

    if not intent.preferred_date:
        return (
            "Customer wants to schedule an appointment. Ask for their preferred date, "
            "meeting type (Call, Online Meeting, or Demo), and timezone.",
            None,
        )

    try:
        target_date = date.fromisoformat(intent.preferred_date)
    except ValueError:
        return "Customer mentioned an unclear date. Ask them to clarify the date (YYYY-MM-DD).", None

    if not intent.timezone:
        return (
            f"Customer wants {appt_type} on {target_date.isoformat()}. "
            "Ask which timezone they are in before checking or confirming slots.",
            None,
        )

    try:
        availability = get_available_slots(
            db=db,
            target_date=target_date,
            appointment_type=appt_type,
            timezone_name=intent.timezone,
        )
    except HTTPException as exc:
        return f"Availability check failed: {exc.detail}. Ask customer for a different date/timezone.", None

    if not availability.is_working_day or not availability.available_slots:
        return (
            f"No available slots on {target_date.isoformat()} ({intent.timezone}). "
            "Politely inform the customer and ask for another weekday.",
            None,
        )

    slot_labels = ", ".join(s.display_start for s in availability.available_slots[:6])

    if not intent.preferred_time:
        return (
            f"Real available {appt_type} slots on {target_date.isoformat()} ({intent.timezone}): {slot_labels}. "
            "Present only these slots and ask which one they prefer.",
            None,
        )

    if not intent.confirm_booking:
        return (
            f"Customer selected {intent.preferred_time} on {target_date.isoformat()} ({intent.timezone}). "
            f"Available slots include: {slot_labels}. Ask the customer to confirm booking this exact slot.",
            None,
        )

    # Customer explicitly confirmed: validate contact info and execute real backend booking.
    if not lead.customer_name or not (lead.email or lead.phone):
        return (
            "Before confirming the booking in the system, ask the customer for their name and either email or phone number.",
            None,
        )

    try:
        hh, mm = map(int, intent.preferred_time.split(":"))
        tz_obj = ZoneInfo(intent.timezone)
        start_local = datetime.combine(target_date, time(hh, mm), tzinfo=tz_obj)
        end_local = start_local + timedelta(minutes=settings.booking_slot_minutes)
        appt = create_appointment(
            db=db,
            payload=AppointmentCreateRequest(
                lead_id=lead.id,
                session_id=lead.session_id,
                title=f"Fortivex AI {appt_type.replace('_', ' ').title()}",
                appointment_type=appt_type,
                scheduled_start=start_local,
                scheduled_end=end_local,
                timezone=intent.timezone,
                customer_name=lead.customer_name,
                customer_email=lead.email,
                customer_phone=lead.phone,
            ),
        )
        appt_schema = AppointmentPublicSchema.model_validate(appt)
        return (
            f"BOOKING CONFIRMED IN BACKEND: reference={appt.appointment_reference}, "
            f"type={appt.appointment_type}, date={target_date.isoformat()}, "
            f"time={start_local.strftime('%I:%M %p').lstrip('0')} {intent.timezone}. "
            "Confirm these exact details to the customer.",
            appt_schema,
        )
    except HTTPException as exc:
        log_crm_activity(
            db=db,
            lead_id=lead.id,
            session_id=lead.session_id,
            activity_type="APPOINTMENT_REQUESTED",
            description=f"Booking attempt failed ({exc.detail}); available slots: {slot_labels}.",
        )
        return (
            f"Booking could not be confirmed ({exc.detail}). "
            f"Available slots on {target_date.isoformat()} ({intent.timezone}): {slot_labels}. "
            "Ask the customer to pick an available slot.",
            None,
        )
    except Exception:
        return "Booking encountered a validation error. Ask the customer to verify the date and time.", None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Generate a RAG-grounded, sentiment-aware, booking-capable Gemini reply."""
    try:
        service = get_gemini_service()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    lead = get_or_create_lead(db, payload.session_id)
    db_history = get_session_history(db, payload.session_id, limit=20)
    effective_history = db_history if db_history else payload.history

    try:
        sentiment_svc = get_sentiment_service()
        current_sentiment = await sentiment_svc.analyze_message(
            message=payload.message,
            history=effective_history,
        )
    except Exception:
        current_sentiment = None

    booking_context, booked_appointment = await _process_booking_intent(
        db=db,
        lead=lead,
        message=payload.message,
        history=effective_history,
    )

    try:
        raw_chunks = search_knowledge(query=payload.message)
        relevant_chunks = [c for c in raw_chunks if c.get("score", 0.0) >= RAG_MIN_SIMILARITY]
    except Exception:
        relevant_chunks = []

    sources = list(
        dict.fromkeys(
            (c.get("source_filename") or c.get("document_name"))
            for c in relevant_chunks
            if c.get("source_filename") or c.get("document_name")
        )
    )

    try:
        reply = await service.generate_sales_reply(
            message=payload.message,
            history=effective_history,
            lead=lead,
            rag_chunks=relevant_chunks,
            sentiment=current_sentiment,
            booking_context=booking_context,
        )
    except GeminiConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GeminiModelError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except GeminiRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except GeminiTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except GeminiEmptyResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except GeminiServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    save_conversation_turn(
        db=db,
        session_id=payload.session_id,
        user_message=payload.message,
        assistant_reply=reply,
        sentiment=current_sentiment,
    )

    extracted = await service.extract_lead_updates(
        message=payload.message,
        assistant_reply=reply,
        existing_lead=lead,
    )
    updated_lead = apply_lead_updates(db=db, lead=lead, extracted=extracted)

    all_messages = get_session_messages(db, payload.session_id)
    sentiment_summary = compute_sentiment_summary(all_messages)

    return ChatResponse(
        reply=reply,
        session_id=payload.session_id,
        provider="gemini",
        model=service.model_name,
        lead=LeadSchema.model_validate(updated_lead),
        sources=sources,
        sentiment=current_sentiment,
        sentiment_summary=sentiment_summary,
        appointment=booked_appointment,
    )


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
def get_agent_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionDetailResponse:
    """Return persisted conversation history, lead profile, and sentiment summary."""
    lead = db.scalar(select(Lead).where(Lead.session_id == session_id))
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' was not found.",
        )

    messages = get_session_messages(db, session_id)
    sentiment_summary = compute_sentiment_summary(messages)

    return SessionDetailResponse(
        session_id=session_id,
        lead=LeadSchema.model_validate(lead),
        messages=[ConversationMessageSchema.model_validate(m) for m in messages],
        sentiment_summary=sentiment_summary,
    )
