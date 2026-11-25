"""API routes for querying qualified leads stored in PostgreSQL."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas.lead_schema import LeadSchema
from app.services.lead_service import get_lead_by_id, list_leads

router = APIRouter(prefix="/api/leads", tags=["Leads"])


@router.get("", response_model=list[LeadSchema])
def get_all_leads(db: Session = Depends(get_db)) -> list[LeadSchema]:
    """Return all captured leads ordered by most recently updated."""
    leads = list_leads(db)
    return [LeadSchema.model_validate(item) for item in leads]


@router.get("/{lead_id}", response_model=LeadSchema)
def get_single_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadSchema:
    """Return complete details for a single lead by ID."""
    lead = get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} was not found.",
        )
    return LeadSchema.model_validate(lead)
