"""FastAPI routes for AI-powered conversation summaries."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas.summary_schema import (
    ConversationSummarySchema,
    SummaryGenerateRequest,
    SummaryListResponse,
)
from app.services.summary_service import (
    generate_or_refresh_summary,
    get_summary_by_session,
    list_summaries,
)

router = APIRouter(prefix="/api/summaries", tags=["Summaries"])


@router.post("/{session_id}/generate", response_model=ConversationSummarySchema)
async def generate_session_summary(
    session_id: str,
    payload: SummaryGenerateRequest | None = None,
    db: Session = Depends(get_db),
) -> ConversationSummarySchema:
    """Generate or regenerate a grounded conversation summary for a session."""
    is_completed = payload.is_completed if payload else False
    summary_obj = await generate_or_refresh_summary(
        db=db,
        session_id=session_id,
        is_completed=is_completed,
    )
    return ConversationSummarySchema.model_validate(summary_obj)


@router.get("/{session_id}", response_model=ConversationSummarySchema)
def get_session_summary(
    session_id: str,
    db: Session = Depends(get_db),
) -> ConversationSummarySchema:
    """Retrieve the persisted summary for a specific session_id."""
    summary_obj = get_summary_by_session(db=db, session_id=session_id)
    return ConversationSummarySchema.model_validate(summary_obj)


@router.get("", response_model=SummaryListResponse)
def list_all_summaries(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    qualification_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> SummaryListResponse:
    """List persisted conversation summaries with pagination and status filtering."""
    return list_summaries(
        db=db,
        limit=limit,
        offset=offset,
        qualification_status=qualification_status,
    )
