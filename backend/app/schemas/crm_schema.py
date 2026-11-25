"""Pydantic v2 schemas for CRM lead views, activity timeline, and sales notes."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.appointment_schema import AppointmentPublicSchema
from app.schemas.sentiment_schema import SentimentSummarySchema


class CRMActivitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    session_id: str
    activity_type: str
    description: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class CRMNoteCreateRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=2000)
    next_follow_up: str | None = Field(default=None, max_length=255)

    @field_validator("note")
    @classmethod
    def note_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Note cannot be empty.")
        return cleaned


class CRMLeadSummarySchema(BaseModel):
    id: int
    session_id: str
    customer_name: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    business_type: str | None = None
    requirements: str | None = None
    budget: str | None = None
    purchase_timeline: str | None = None
    interest_level: str | None = None
    qualification_status: str
    qualification_reason: str | None = None
    latest_sentiment: str | None = None
    sentiment_trend: str = "insufficient_data"
    appointment_count: int = 0
    last_conversation_at: datetime | None = None
    next_follow_up: str | None = None
    internal_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CRMLeadDetailSchema(CRMLeadSummarySchema):
    sentiment_summary: SentimentSummarySchema
    appointments: list[AppointmentPublicSchema] = Field(default_factory=list)
    activities: list[CRMActivitySchema] = Field(default_factory=list)
