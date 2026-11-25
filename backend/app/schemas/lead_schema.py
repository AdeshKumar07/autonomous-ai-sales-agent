"""Pydantic v2 schemas for leads, extraction validation, and session history."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.sentiment_schema import SentimentSummarySchema

QualificationStatus = Literal["NEW", "HOT", "WARM", "COLD"]
_EMPTY_MARKERS = {"", "null", "none", "n/a", "na", "unknown", "not provided", "declined"}


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    if cleaned.lower() in _EMPTY_MARKERS:
        return None
    return cleaned


class LeadExtractionResult(BaseModel):
    """Validated structured output from Gemini lead extraction."""

    customer_name: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    business_type: str | None = None
    requirements: str | None = None
    budget: str | None = None
    purchase_timeline: str | None = None
    interest_level: str | None = None
    qualification_status: QualificationStatus | None = None
    qualification_reason: str | None = None
    cleared_fields: list[str] = Field(default_factory=list)

    @field_validator(
        "customer_name",
        "company_name",
        "email",
        "phone",
        "business_type",
        "requirements",
        "budget",
        "purchase_timeline",
        "interest_level",
        "qualification_reason",
        mode="before",
    )
    @classmethod
    def normalize_optional_fields(cls, value: object) -> str | None:
        return _clean_optional_text(value)

    @field_validator("qualification_status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> str | None:
        cleaned = _clean_optional_text(value)
        if not cleaned:
            return None
        upper = cleaned.upper()
        return upper if upper in {"NEW", "HOT", "WARM", "COLD"} else None


class LeadSchema(BaseModel):
    """Structured lead representation returned by chat, leads, and session endpoints."""

    model_config = ConfigDict(from_attributes=True)

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
    qualification_status: str = "NEW"
    qualification_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ConversationMessageSchema(BaseModel):
    """Persisted conversation message schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    sentiment: str | None = None
    sentiment_confidence: float | None = None
    sentiment_explanation: str | None = None
    emotional_indicators: list[str] | None = None
    recommended_strategy: str | None = None
    analyzed_at: datetime | None = None
    created_at: datetime


class SessionDetailResponse(BaseModel):
    """Complete session state including lead profile, messages, and sentiment summary."""

    session_id: str
    lead: LeadSchema
    messages: list[ConversationMessageSchema]
    sentiment_summary: SentimentSummarySchema | None = None
