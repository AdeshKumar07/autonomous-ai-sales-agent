"""AI-powered conversation summarization service with PostgreSQL grounding and fallback."""

import asyncio
from datetime import datetime, timezone
import json
from fastapi import HTTPException, status
from google import genai
from google.genai import types
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import validate_gemini_config
from app.models.appointment import Appointment
from app.models.lead import ConversationMessage, Lead
from app.models.summary import ConversationSummary
from app.schemas.summary_schema import GeminiSummaryExtraction, SummaryListResponse, ConversationSummarySchema
from app.services.sentiment_service import compute_sentiment_summary

OPT_OUT_PHRASES = (
    "stop contacting",
    "do not contact",
    "don't contact",
    "unsubscribe",
    "remove me",
    "not interested",
)

SUMMARY_SYSTEM_INSTRUCTION = """You are a precise B2B sales call summarizer.
Generate a structured JSON summary strictly grounded in the provided conversation transcript and PostgreSQL lead facts.

Rules:
1. NEVER invent customer details, budgets, timelines, products, or commitments not present in the transcript.
2. If a detail was not mentioned, leave it null or an empty list [].
3. Extract:
   - conversation_title: concise 4-8 word title for this sales conversation
   - summary: clear 2-4 sentence factual overview (note if conversation is still in progress vs completed)
   - main_business_problem: concise statement of the customer's core problem, or null
   - customer_requirements: list of explicit requirements mentioned
   - pain_points: list of explicit pain points mentioned
   - discussed_products: list of products/solution areas discussed
   - objections: list of customer concerns/objections raised
   - customer_questions: list of questions asked by the customer
   - unresolved_questions: list of customer questions that remain unanswered or need company confirmation
   - recommended_next_action: 1-sentence actionable sales follow-up
"""


def _has_opt_out(messages: list[ConversationMessage]) -> bool:
    for msg in messages:
        if msg.role == "user":
            lower = msg.content.lower()
            if any(phrase in lower for phrase in OPT_OUT_PHRASES):
                return True
    return False


def determine_recommended_action(
    lead: Lead,
    latest_sentiment: str | None,
    appointment: Appointment | None,
    messages: list[ConversationMessage],
    ai_recommendation: str | None = None,
) -> str:
    """Apply deterministic business rules before falling back to AI recommendation."""
    if latest_sentiment == "NEGATIVE" and _has_opt_out(messages):
        return "Respect customer opt-out; do not schedule further sales outreach."
    if latest_sentiment == "FRUSTRATED":
        return "Assign a human sales representative to follow up and resolve customer frustration."
    if lead.qualification_status == "HOT" and not appointment:
        return "HOT lead without a scheduled meeting — reach out promptly to book a live product demo."
    if lead.budget and not lead.purchase_timeline:
        return "Follow up to confirm the customer's expected purchase timeline."
    if ai_recommendation and ai_recommendation.strip():
        return ai_recommendation.strip()
    return "Continue discovery to qualify business requirements and timeline."


def _build_fallback_extraction(
    lead: Lead,
    messages: list[ConversationMessage],
    is_completed: bool,
) -> GeminiSummaryExtraction:
    """Deterministic summary fallback if Gemini is unavailable or rate-limited."""
    user_msgs = [m.content.strip() for m in messages if m.role == "user" and m.content.strip()]
    questions = [m for m in user_msgs if "?" in m][:5]
    reqs = [lead.requirements] if lead.requirements else []
    status_label = "completed" if is_completed else "in progress"
    title_subject = lead.company_name or lead.customer_name or lead.session_id
    summary_text = (
        f"Conversation with {title_subject} ({status_label}, {len(user_msgs)} customer messages). "
        f"Lead status is {lead.qualification_status}."
    )
    if lead.requirements:
        summary_text += f" Stated requirements: {lead.requirements}."

    return GeminiSummaryExtraction(
        conversation_title=f"Sales Discussion — {title_subject}",
        summary=summary_text,
        main_business_problem=lead.requirements,
        customer_requirements=reqs,
        pain_points=[],
        discussed_products=[],
        objections=[],
        customer_questions=questions,
        unresolved_questions=[],
        recommended_next_action="Review conversation history and follow up accordingly.",
    )


async def _call_gemini_summary(
    lead: Lead,
    messages: list[ConversationMessage],
    appointment: Appointment | None,
    is_completed: bool,
) -> GeminiSummaryExtraction | None:
    cfg = validate_gemini_config()
    client = genai.Client(api_key=cfg.gemini_api_key)

    transcript = "\n".join(f"{m.role.upper()}: {m.content}" for m in messages[-30:])
    prompt = (
        f"Conversation Status: {'Completed' if is_completed else 'Active / In Progress'}\n"
        f"Saved Lead Facts: name={lead.customer_name}, company={lead.company_name}, "
        f"business_type={lead.business_type}, requirements={lead.requirements}, "
        f"budget={lead.budget}, timeline={lead.purchase_timeline}, "
        f"qualification={lead.qualification_status}\n"
        f"Appointment: {appointment.appointment_reference if appointment else 'None'}\n\n"
        f"Transcript:\n{transcript}"
    )

    config = types.GenerateContentConfig(
        system_instruction=SUMMARY_SYSTEM_INSTRUCTION,
        temperature=0.2,
        max_output_tokens=700,
        response_mime_type="application/json",
        response_schema=GeminiSummaryExtraction,
    )

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=cfg.gemini_model,
                contents=prompt,
                config=config,
            ),
            timeout=cfg.gemini_timeout_seconds,
        )
        raw = (getattr(response, "text", None) or "").strip()
        if not raw:
            return None
        return GeminiSummaryExtraction.model_validate(json.loads(raw))
    except (asyncio.TimeoutError, json.JSONDecodeError, ValidationError, Exception):
        return None


async def generate_or_refresh_summary(
    db: Session,
    session_id: str,
    is_completed: bool = False,
) -> ConversationSummary:
    """Generate or regenerate a grounded ConversationSummary persisted in PostgreSQL."""
    lead = db.scalar(select(Lead).where(Lead.session_id == session_id))
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' was not found.",
        )

    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.id.asc())
        ).all()
    )
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate summary for an empty conversation.",
        )

    appointment = db.scalar(
        select(Appointment)
        .where(Appointment.lead_id == lead.id)
        .order_by(Appointment.id.desc())
    )
    sentiment_summary = compute_sentiment_summary(messages)

    ai_data = await _call_gemini_summary(lead, messages, appointment, is_completed)
    if ai_data is None:
        ai_data = _build_fallback_extraction(lead, messages, is_completed)

    recommended_action = determine_recommended_action(
        lead=lead,
        latest_sentiment=sentiment_summary.latest_sentiment,
        appointment=appointment,
        messages=messages,
        ai_recommendation=ai_data.recommended_next_action,
    )

    user_msg_count = sum(1 for m in messages if m.role == "user")
    now_utc = datetime.now(timezone.utc)

    existing = db.scalar(
        select(ConversationSummary).where(ConversationSummary.session_id == session_id)
    )
    if existing:
        existing.conversation_title = ai_data.conversation_title[:255]
        existing.summary = ai_data.summary
        existing.customer_name = lead.customer_name
        existing.company_name = lead.company_name
        existing.business_type = lead.business_type
        existing.budget = lead.budget
        existing.purchase_timeline = lead.purchase_timeline
        existing.main_business_problem = ai_data.main_business_problem
        existing.customer_requirements = ai_data.customer_requirements
        existing.pain_points = ai_data.pain_points
        existing.discussed_products = ai_data.discussed_products
        existing.objections = ai_data.objections
        existing.customer_questions = ai_data.customer_questions
        existing.sentiment_overview = sentiment_summary.model_dump(mode="json")
        existing.qualification_status = lead.qualification_status
        existing.appointment_reference = appointment.appointment_reference if appointment else None
        existing.unresolved_questions = ai_data.unresolved_questions
        existing.recommended_next_action = recommended_action
        existing.is_conversation_completed = is_completed or existing.is_conversation_completed
        existing.message_count_at_generation = user_msg_count
        existing.summary_version += 1
        existing.generated_at = now_utc
        summary_obj = existing
    else:
        summary_obj = ConversationSummary(
            session_id=session_id,
            lead_id=lead.id,
            conversation_title=ai_data.conversation_title[:255],
            summary=ai_data.summary,
            customer_name=lead.customer_name,
            company_name=lead.company_name,
            business_type=lead.business_type,
            budget=lead.budget,
            purchase_timeline=lead.purchase_timeline,
            main_business_problem=ai_data.main_business_problem,
            customer_requirements=ai_data.customer_requirements,
            pain_points=ai_data.pain_points,
            discussed_products=ai_data.discussed_products,
            objections=ai_data.objections,
            customer_questions=ai_data.customer_questions,
            sentiment_overview=sentiment_summary.model_dump(mode="json"),
            qualification_status=lead.qualification_status,
            appointment_reference=appointment.appointment_reference if appointment else None,
            unresolved_questions=ai_data.unresolved_questions,
            recommended_next_action=recommended_action,
            is_conversation_completed=is_completed,
            message_count_at_generation=user_msg_count,
            summary_version=1,
            generated_at=now_utc,
        )
        db.add(summary_obj)

    db.commit()
    db.refresh(summary_obj)
    return summary_obj


def get_summary_by_session(db: Session, session_id: str) -> ConversationSummary:
    summary_obj = db.scalar(
        select(ConversationSummary).where(ConversationSummary.session_id == session_id)
    )
    if not summary_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary for session '{session_id}' has not been generated yet.",
        )
    return summary_obj


def list_summaries(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    qualification_status: str | None = None,
) -> SummaryListResponse:
    stmt = select(ConversationSummary)
    if qualification_status:
        stmt = stmt.where(
            ConversationSummary.qualification_status == qualification_status.strip().upper()
        )
    all_rows = list(db.scalars(stmt.order_by(ConversationSummary.updated_at.desc())).all())
    total = len(all_rows)
    page = all_rows[offset : offset + limit]
    return SummaryListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[ConversationSummarySchema.model_validate(item) for item in page],
    )
