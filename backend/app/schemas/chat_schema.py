"""Pydantic v2 request and response schemas for the AI sales chat API."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator
from app.schemas.appointment_schema import AppointmentPublicSchema
from app.schemas.lead_schema import LeadSchema
from app.schemas.sentiment_schema import SentimentAnalysisResult, SentimentSummarySchema


class ChatHistoryItem(BaseModel):
    """Single turn in the conversation history."""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("History message content cannot be empty.")
        return cleaned


class ChatRequest(BaseModel):
    """Incoming chat request payload from the frontend."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default="default_session", min_length=1, max_length=100)
    history: list[ChatHistoryItem] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty.")
        return cleaned

    @field_validator("session_id")
    @classmethod
    def session_id_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("session_id cannot be empty.")
        return cleaned


class ChatResponse(BaseModel):
    """Standardized chat response returned to the frontend."""

    reply: str
    session_id: str
    provider: str = "gemini"
    model: str
    lead: LeadSchema
    sources: list[str] = Field(default_factory=list)
    sentiment: SentimentAnalysisResult | None = None
    sentiment_summary: SentimentSummarySchema | None = None
    appointment: AppointmentPublicSchema | None = None
