"""FastAPI routes for CRM lead management, appointment history, notes, and activities."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas.appointment_schema import AppointmentPublicSchema
from app.schemas.crm_schema import (
    CRMLeadDetailSchema,
    CRMLeadSummarySchema,
    CRMNoteCreateRequest,
)
from app.services.appointment_service import list_appointments
from app.services.crm_service import add_crm_note, get_crm_lead_detail, list_crm_leads

router = APIRouter(prefix="/api/crm", tags=["CRM"])


@router.get("/leads", response_model=list[CRMLeadSummarySchema])
def crm_list_leads(db: Session = Depends(get_db)) -> list[CRMLeadSummarySchema]:
    """Return all CRM leads with qualification, latest sentiment, and appointment counts."""
    return list_crm_leads(db)


@router.get("/leads/{lead_id}", response_model=CRMLeadDetailSchema)
def crm_get_lead_detail(
    lead_id: int,
    db: Session = Depends(get_db),
) -> CRMLeadDetailSchema:
    """Return complete CRM lead profile, appointments, and activity timeline."""
    detail = get_crm_lead_detail(db, lead_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CRM lead {lead_id} was not found.",
        )
    return detail


@router.get("/leads/{lead_id}/appointments", response_model=list[AppointmentPublicSchema])
def crm_get_lead_appointments(
    lead_id: int,
    db: Session = Depends(get_db),
) -> list[AppointmentPublicSchema]:
    """Return appointment history for a specific CRM lead."""
    detail = get_crm_lead_detail(db, lead_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CRM lead {lead_id} was not found.",
        )
    items = list_appointments(db=db, lead_id=lead_id)
    return [AppointmentPublicSchema.model_validate(item) for item in items]


@router.post("/leads/{lead_id}/notes", response_model=CRMLeadDetailSchema)
def crm_add_lead_note(
    lead_id: int,
    payload: CRMNoteCreateRequest,
    db: Session = Depends(get_db),
) -> CRMLeadDetailSchema:
    """Add an internal sales note and optional next follow-up action to a CRM lead."""
    updated = add_crm_note(
        db=db,
        lead_id=lead_id,
        note=payload.note,
        next_follow_up=payload.next_follow_up,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CRM lead {lead_id} was not found.",
        )
    return updated
