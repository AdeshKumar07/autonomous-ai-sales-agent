"""Service layer for PostgreSQL conversation memory and lead qualification."""

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.lead import ConversationMessage, Lead
from app.schemas.chat_schema import ChatHistoryItem
from app.schemas.lead_schema import LeadExtractionResult
from app.schemas.sentiment_schema import SentimentAnalysisResult

VALID_QUALIFICATION_STATUSES = {"NEW", "HOT", "WARM", "COLD"}
UPDATABLE_LEAD_FIELDS = (
    "customer_name",
    "company_name",
    "email",
    "phone",
    "business_type",
    "requirements",
    "budget",
    "purchase_timeline",
    "interest_level",
)


def get_or_create_lead(db: Session, session_id: str) -> Lead:
    """Retrieve the existing lead for session_id or create one without duplicates."""
    lead = db.scalar(select(Lead).where(Lead.session_id == session_id))
    if lead:
        return lead

    lead = Lead(
        session_id=session_id,
        qualification_status="NEW",
        qualification_reason="Insufficient information to qualify yet.",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    from app.services.crm_service import log_crm_activity

    log_crm_activity(
        db=db,
        lead_id=lead.id,
        session_id=lead.session_id,
        activity_type="LEAD_CREATED",
        description="Lead session initialized.",
    )
    return lead


def get_session_history(
    db: Session,
    session_id: str,
    limit: int = 20,
) -> list[ChatHistoryItem]:
    """Load recent persisted messages for session_id in chronological order."""
    rows = db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.id.desc())
        .limit(limit)
    ).all()

    ordered = list(reversed(rows))
    return [
        ChatHistoryItem(role=row.role, content=row.content)
        for row in ordered
        if row.role in ("user", "assistant") and row.content.strip()
    ]


def save_conversation_turn(
    db: Session,
    session_id: str,
    user_message: str,
    assistant_reply: str,
    sentiment: SentimentAnalysisResult | None = None,
) -> None:
    """Persist both the user message (with optional sentiment) and assistant reply."""
    db.add(
        ConversationMessage(
            session_id=session_id,
            role="user",
            content=user_message.strip(),
            sentiment=sentiment.sentiment if sentiment else None,
            sentiment_confidence=sentiment.confidence if sentiment else None,
            sentiment_explanation=sentiment.explanation if sentiment else None,
            emotional_indicators=sentiment.emotional_indicators if sentiment else None,
            recommended_strategy=sentiment.recommended_strategy if sentiment else None,
            analyzed_at=sentiment.analyzed_at if sentiment else None,
        )
    )
    db.add(
        ConversationMessage(
            session_id=session_id,
            role="assistant",
            content=assistant_reply.strip(),
        )
    )
    db.commit()


def _resolve_consistent_status(
    lead: Lead,
    proposed_status: str | None,
) -> str:
    """Ensure qualification_status aligns with requirements, timeline, and buying intent."""
    candidate = (proposed_status or lead.qualification_status or "NEW").strip().upper()
    if candidate not in VALID_QUALIFICATION_STATUSES:
        candidate = "NEW"

    if candidate == "COLD":
        return "COLD"

    has_requirements = bool(lead.requirements)
    has_timeline = bool(lead.purchase_timeline)
    has_any_signal = any(
        [
            lead.customer_name,
            lead.company_name,
            lead.requirements,
            lead.budget,
            lead.purchase_timeline,
            lead.interest_level,
        ]
    )

    if candidate == "HOT" and not (has_requirements and has_timeline):
        return "WARM" if has_any_signal else "NEW"

    if candidate == "NEW" and has_requirements and has_timeline:
        return "WARM"

    return candidate


def apply_lead_updates(
    db: Session,
    lead: Lead,
    extracted: LeadExtractionResult | dict[str, Any] | None,
) -> Lead:
    """Merge non-null extracted fields into Lead while preserving unmentioned values."""
    if not extracted:
        return lead

    if isinstance(extracted, dict):
        validated = LeadExtractionResult.model_validate(extracted)
    else:
        validated = extracted

    # Only clear fields if the customer explicitly requested deletion.
    for field_name in validated.cleared_fields:
        if field_name in UPDATABLE_LEAD_FIELDS:
            setattr(lead, field_name, None)

    prev_status = lead.qualification_status
    changed_fields: list[str] = []

    for field in UPDATABLE_LEAD_FIELDS:
        val = getattr(validated, field, None)
        if isinstance(val, str) and val.strip():
            cleaned = val.strip()
            if getattr(lead, field) != cleaned:
                setattr(lead, field, cleaned)
                changed_fields.append(field)

    lead.qualification_status = _resolve_consistent_status(
        lead=lead,
        proposed_status=validated.qualification_status,
    )

    if validated.qualification_reason:
        lead.qualification_reason = validated.qualification_reason

    db.add(lead)
    db.commit()
    db.refresh(lead)

    from app.services.crm_service import log_crm_activity

    if changed_fields:
        log_crm_activity(
            db=db,
            lead_id=lead.id,
            session_id=lead.session_id,
            activity_type="INFO_UPDATED",
            description=f"Updated lead fields: {', '.join(changed_fields)}.",
        )
    if lead.qualification_status != prev_status:
        log_crm_activity(
            db=db,
            lead_id=lead.id,
            session_id=lead.session_id,
            activity_type="LEAD_QUALIFIED",
            description=f"Lead status changed from {prev_status} to {lead.qualification_status}.",
        )
    return lead


def list_leads(db: Session) -> list[Lead]:
    """Return all saved leads ordered by most recently updated."""
    return list(db.scalars(select(Lead).order_by(Lead.updated_at.desc(), Lead.id.desc())).all())


def get_lead_by_id(db: Session, lead_id: int) -> Lead | None:
    """Return a single lead by primary key."""
    return db.scalar(select(Lead).where(Lead.id == lead_id))


def get_session_messages(db: Session, session_id: str) -> list[ConversationMessage]:
    """Return all persisted messages for a session in chronological order."""
    return list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.id.asc())
        ).all()
    )
