"""Pydantic v2 schemas for message-level sentiment analysis and session summary."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

SentimentLabel = Literal["POSITIVE", "NEUTRAL", "FRUSTRATED", "NEGATIVE"]
SentimentTrend = Literal["improving", "stable", "declining", "insufficient_data"]

_VALID_LABELS = {"POSITIVE", "NEUTRAL", "FRUSTRATED", "NEGATIVE"}


class SentimentAnalysisResult(BaseModel):
    """Structured sentiment analysis output for a single customer message."""

    sentiment: SentimentLabel = "NEUTRAL"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    explanation: str = ""
    emotional_indicators: list[str] = Field(default_factory=list)
    recommended_strategy: str = ""
    analyzed_at: datetime | None = None

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalize_sentiment_label(cls, value: object) -> str:
        if not isinstance(value, str):
            return "NEUTRAL"
        upper = value.strip().upper()
        return upper if upper in _VALID_LABELS else "NEUTRAL"

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, value: object) -> float:
        try:
            num = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.5
        return round(max(0.0, min(1.0, num)), 3)

    @field_validator("emotional_indicators", mode="before")
    @classmethod
    def clean_indicators(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()][:6]


class SentimentSummarySchema(BaseModel):
    """Session-level sentiment summary distinguishing latest, overall, and trend."""

    latest_sentiment: SentimentLabel | None = None
    latest_confidence: float | None = None
    latest_explanation: str | None = None
    latest_emotional_indicators: list[str] = Field(default_factory=list)
    latest_recommended_strategy: str | None = None
    latest_analyzed_at: datetime | None = None
    overall_sentiment: SentimentLabel | None = None
    sentiment_trend: SentimentTrend = "insufficient_data"
    analyzed_message_count: int = 0
