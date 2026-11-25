"""CRM service layer backed by PostgreSQL Lead, Appointment, and CRMActivity tables."""

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.appointment import Appointment, CRMActivity
from app.models.lead import ConversationMessage, Lead
from app.schemas.appointment_schema import AppointmentPublicSchema
from app.schemas.crm_schema import (
    CRMActivitySchema,
    CRMLeadDetailSchema,
    CRMLeadSummarySchema,
)
from app.services.sentiment_service import compute_sentiment_summary


def log_crm_activity(
    db: Session,
    lead_id: int,
    session_id: str,
    activity_type: str,
    description: str,
    metadata_json: dict[str, Any] | None = None,
    commit: bool = True,
) -> CRMActivity:
    """Append a structured activity event to the lead's CRM timeline."""
    activity = CRMActivity(
        lead_id=lead_id,
        session_id=session_id,
        activity_type=activity_type,
        description=description,
        metadata_json=metadata_json,
    )
    db.add(activity)
    if commit:
        db.commit()
        db.refresh(activity)
    return activity


def _build_crm_summary(db: Session, lead: Lead) -> CRMLeadSummarySchema:
    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == lead.session_id)
            .order_by(ConversationMessage.id.asc())
        ).all()
    )
    sentiment_summary = compute_sentiment_summary(messages)
    last_conv = messages[-1].created_at if messages else None
    appt_count = len(
        db.scalars(select(Appointment.id).where(Appointment.lead_id == lead.id)).all()
    )

    return CRMLeadSummarySchema(
        id=lead.id,
        session_id=lead.session_id,
        customer_name=lead.customer_name,
        company_name=lead.company_name,
        email=lead.email,
        phone=lead.phone,
        business_type=lead.business_type,
        requirements=lead.requirements,
        budget=lead.budget,
        purchase_timeline=lead.purchase_timeline,
        interest_level=lead.interest_level,
        qualification_status=lead.qualification_status,
        qualification_reason=lead.qualification_reason,
        latest_sentiment=sentiment_summary.latest_sentiment,
        sentiment_trend=sentiment_summary.sentiment_trend,
        appointment_count=appt_count,
        last_conversation_at=last_conv,
        next_follow_up=lead.next_follow_up,
        internal_notes=lead.internal_notes,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


def list_crm_leads(db: Session) -> list[CRMLeadSummarySchema]:
    """Return all CRM leads with latest sentiment, appointment count, and last contact."""
    leads = list(
        db.scalars(select(Lead).order_by(Lead.updated_at.desc(), Lead.id.desc())).all()
    )
    return [_build_crm_summary(db, lead) for lead in leads]


def get_crm_lead_detail(db: Session, lead_id: int) -> CRMLeadDetailSchema | None:
    """Return full CRM lead detail including sentiment summary, appointments, and timeline."""
    lead = db.scalar(select(Lead).where(Lead.id == lead_id))
    if not lead:
        return None

    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == lead.session_id)
            .order_by(ConversationMessage.id.asc())
        ).all()
    )
    sentiment_summary = compute_sentiment_summary(messages)
    last_conv = messages[-1].created_at if messages else None

    appointments = list(
        db.scalars(
            select(Appointment)
            .where(Appointment.lead_id == lead.id)
            .order_by(Appointment.scheduled_start.desc())
        ).all()
    )
    activities = list(
        db.scalars(
            select(CRMActivity)
            .where(CRMActivity.lead_id == lead.id)
            .order_by(CRMActivity.id.desc())
        ).all()
    )

    return CRMLeadDetailSchema(
        id=lead.id,
        session_id=lead.session_id,
        customer_name=lead.customer_name,
        company_name=lead.company_name,
        email=lead.email,
        phone=lead.phone,
        business_type=lead.business_type,
        requirements=lead.requirements,
        budget=lead.budget,
        purchase_timeline=lead.purchase_timeline,
        interest_level=lead.interest_level,
        qualification_status=lead.qualification_status,
        qualification_reason=lead.qualification_reason,
        latest_sentiment=sentiment_summary.latest_sentiment,
        sentiment_trend=sentiment_summary.sentiment_trend,
        appointment_count=len(appointments),
        last_conversation_at=last_conv,
        next_follow_up=lead.next_follow_up,
        internal_notes=lead.internal_notes,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        sentiment_summary=sentiment_summary,
        appointments=[AppointmentPublicSchema.model_validate(a) for a in appointments],
        activities=[CRMActivitySchema.model_validate(act) for act in activities],
    )


def add_crm_note(
    db: Session,
    lead_id: int,
    note: str,
    next_follow_up: str | None = None,
) -> CRMLeadDetailSchema | None:
    """Append an internal sales note to a lead and record a CRM activity event."""
    lead = db.scalar(select(Lead).where(Lead.id == lead_id))
    if not lead:
        return None

    cleaned_note = note.strip()
    if lead.internal_notes:
        lead.internal_notes = f"{lead.internal_notes}\n• {cleaned_note}"
    else:
        lead.internal_notes = f"• {cleaned_note}"

    if next_follow_up is not None and next_follow_up.strip():
        lead.next_follow_up = next_follow_up.strip()

    db.add(lead)
    log_crm_activity(
        db=db,
        lead_id=lead.id,
        session_id=lead.session_id,
        activity_type="NOTE_ADDED",
        description=f"Internal sales note added: {cleaned_note[:120]}",
        commit=False,
    )
    db.commit()
    return get_crm_lead_detail(db, lead.id)
